const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '../.env') });

const db = require('./database.js')
const express = require('express'); 
const helmet = require('helmet');

const rateLimit = require('express-rate-limit');
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000,
    limit: 100, //100 requests per 15 mins for each ip
    standardHeaders: true, 
    legacyHeaders: false,
    message: "Too many requests, try again later"
});

const passport = require('passport');
const GoogleStrategy = require('passport-google-oauth20').Strategy;
const session = require('express-session');
const pgSession = require('connect-pg-simple')(session);
const cors = require('cors');
const {google} = require('googleapis'); 
const DOMPurify = require('isomorphic-dompurify');
const {encrypt, decrypt} = require('./crypto.js');

const app = express(); 
const PORT = process.env.PORT;
const CLIENT_URL = process.env.CLIENT_URL;

const getGmailClient = (user) => {
    if(!user || !user.refreshToken) {
        throw new Error ('user not authenticated or missing refresh token');
    }
        const oauth2Client = new google.auth.OAuth2(
            process.env.GOOGLE_CLIENT_ID,
            process.env.GOOGLE_CLIENT_SECRET,
            process.env.GOOGLE_CALLBACK_URL,
        );
        oauth2Client.setCredentials({refresh_token: user.refreshToken});
        return google.gmail({version: 'v1', auth: oauth2Client});
    
};

const getEmailBody = (payload) =>{
    //if email body is just there, give it
    if (payload.body && payload.body.data) {
        return Buffer.from(payload.body.data, 'base64url').toString('utf-8');
    }

    //if email body is multipart (text, HTML, pics, attachments, etc.), look inside parts
    if(payload.parts){
        for(const part of payload.parts){
            if(part.mimeType === 'text/plain' || part.mimeType === 'text/html'){
                if(part.body && part.body.data) {
                    return Buffer.from(part.body.data, 'base64url').toString('utf-8');
                }
            }

            if(part.parts){
                const nestedBody = getEmailBody(part);
                if(nestedBody) return nestedBody;
            }
        }
    }
    return 'No readable text found';
}

const requireGoogleAuth = (req, res, next) => {
    if(!req.isAuthenticated()){
        return res.status(401).json({error: 'please log in'});
    }
    if(!req.user.refreshToken){
        return res.status(403).json({error: 'google account not linked properly'});
    }
    next();
};

//use helmet quite literally just "adds security"
app.use(helmet({
    contentSecurityPolicy: false,
}));

app.use(limiter);

app.use(cors({
    origin: CLIENT_URL,
    credentials: true
}));

/* this converts json data sent from the frontend into JS objects 
(this part is not used yet, but will be for something like "mark as unsafe" feature) */
app.use(express.json())

app.use(session({
    store: new pgSession({
        pool: db.pool,
        tableName: 'session'
    }),
    secret:process.env.SESSION_SECRET, // if a cookie doesn't have our session secret, it's invalid
    resave:false, // our web app won't rewrite a user's data if nothings changed
    saveUninitialized: false, // our web app won't remember people who don't login
    cookie: {
        secure: process.env.NODE_ENV === 'production',  
        httpOnly: true,
        maxAge: 24 * 60 * 60 * 1000  // cookzie valid for 24 hours
    }
}));

app.use(passport.initialize());
app.use(passport.session());

/*we tell our how to check google IDs. and we give it the client ID and secret
to basically mean that this guy can call Google*/
passport.use(new GoogleStrategy({
    clientID: process.env.GOOGLE_CLIENT_ID,
    clientSecret: process.env.GOOGLE_CLIENT_SECRET,
    callbackURL: process.env.GOOGLE_CALLBACK_URL //passport tells the user to go to this address after going to Google
},

//after the user logs in, we receive their google data
async (accessToken, refreshToken, profile, done) => {

    //we ask the database to get a specific user with a specific google id
    try{
    const result = await db.query(
        'SELECT * FROM users WHERE google_id = $1',
        [profile.id]
    );

    let user;

    //if the database returns a result, it means the user exists
    if (result.rows.length > 0){
        user = result.rows[0];

    //if it doesn't, then it creates this user as a new user
    } else {
        const insertResult = await db.query(
            `INSERT INTO users (google_id, email, display_name)
            VALUES ($1, $2, $3)
            RETURNING *`,
            [profile.id, profile.emails[0].value, profile.displayName]
        );
        user = insertResult.rows[0];
    }

    if (refreshToken) {
        user.encryptedRefreshToken = encrypt(refreshToken);
    }

    return done(null, user);

    } catch (err) {
        console.error('database auth error: ', err);
        return done(err,null);
}
}));

//covnerts heavy user data into a ticket and stores it in the browser
passport.serializeUser((user, done) => {
    const sessionUser = {
        id: user.id,
        google_id: user.google_id,
        encryptedRefreshToken: user.encryptedRefreshToken,
        email: user.email
    };
    done(null, sessionUser);
});

//you give the ticket to get that heavy data back, which was stored in the server
passport.deserializeUser((sessionUser, done) => {
    const user = {...sessionUser};

    if(user.encryptedRefreshToken){
        user.refreshToken = decrypt(user.encryptedRefreshToken);
    }
    done(null, user);
});

/* when the user clicks login,
this takes the user and permissions to request and 
sends them to the google auth screen*/
app.get('/auth/google', 
    passport.authenticate('google', {
        scope: ['https://www.googleapis.com/auth/gmail.readonly', 'email',  'profile', 'openid'],
        accessType: 'offline',
        prompt: 'consent'
    })
);

/* google sends the user back to the backend, and passport checks the details */
app.get('/auth/google/callback', 
    passport.authenticate('google', {
        failureRedirect: `${CLIENT_URL}/login?error=true` //if the user is fake, go back to login
    }),
    (req, res) => { //if the user isnt fake...

    res.redirect(`${CLIENT_URL}/inbox`); //go to their respective inbox
});

/* get current user is the frontend asking "who am i?" or "who is logged in?" 
the backend runs deserializeUser and gets user
then it says you are "user" or you are null if there is no user detected
then the frontend does whatever function with that specific user*/
app.get('/api/current_user', (req, res) => {
    res.send(req.user || null);
});


app.get('/logout', (req, res, next) => {
    req.logout(() => {
        req.session.destroy();
        res.redirect(process.env.CLIENT_URL);
    });
});

/*define email route
async allows us to use "await" which pauses execution while google fetches email data
async just basically means this is a function that might take a while*/
app.get('/api/emails', requireGoogleAuth, async (req, res) =>{
    //if the user is valid,
    try {
        const gmail = getGmailClient(req.user);

        /*this asks google to send the latest 10 emails of the current logged in accoun
        the await means dont do anything until google answers*/
        const listResponse = await gmail.users.messages.list({
            userId:'me',
            maxResults: 10 
        });

        //this makes an array of message IDs (ticket that links to an email)
        const messages = listResponse.data.messages;

        //if no emails, return json of NOTHING
        if (!messages || messages.length === 0) {
            return res.json([]);
        }

        //goes to where you get the emails
        const emailDetails = await Promise.all(//promise makes it run in parallel
            messages.map(async (msg) => {

                //gets the raw email data
                const detail = await gmail.users.messages.get({
                    userId: 'me',
                    id: msg.id,
                    format: 'full'
                });
            
                //cleans the email data to get individual elements
                const headers = detail.data.payload.headers;
                const subject = DOMPurify.sanitize(headers.find(h => h.name === 'Subject')?.value || '(No Subject)');
                const from = DOMPurify.sanitize(headers.find(h => h.name === 'From')?.value || '(Unknown)');
                const snippet = DOMPurify.sanitize(detail.data.snippet);
                const date = headers.find(h => h.name === 'Date')?.value;
                

                //"readies" the cleaned data
                return{
                    id: msg.id,
                    threadId: msg.threadId,
                    subject: subject,
                    from: from,
                    date: date,
                    snippet: snippet
                };
            })
        );


        //presents or serves the cleaned email data to the frontend
        res.json(emailDetails);

    } catch (error) {
        console.error('Gmail API Error:', error);
        res.status(401).json({error: 'Token expired or invalid'});
    }
});

app.get('/api/emails/:id', requireGoogleAuth, async (req, res) => {

    try {
        const gmail = getGmailClient(req.user);

        const response = await gmail.users.messages.get({
            userId: 'me',
            id: req.params.id,
            format:'full'
        });

        const payload = response.data.payload;
        const headers = payload.headers;
        const rawBody = getEmailBody(payload);

        const cleanData = {
            id: response.data.id,
      
            subject: DOMPurify.sanitize(headers.find(h => h.name === 'Subject')?.value || '(No Subject)'),
            from: DOMPurify.sanitize(headers.find(h => h.name === 'From')?.value || '(Unknown)'),
            to: DOMPurify.sanitize(headers.find(h => h.name === 'To')?.value || '(Unknown)'),
            date: headers.find(h => h.name === 'Date')?.value, 
            
            // CRITICAL: Sanitize the HTML Body
            // This strips out <script> tags but keeps <b>, <p>, etc.
            body: DOMPurify.sanitize(rawBody)
        };

        res.json({
            basic: cleanData,
            headers: headers    
        });

    } catch (error) {
        console.error('gmail get error', error);
        res.status(500).json({error:"internal server error"});
    }
});

app.post('/api/scan', requireGoogleAuth, async(req, res) => {
    const {emailId} = req.body;

    if (!emailId) return res.status(400).json({error: 'email ID required'});

    try{
        //get email
        const gmail = getGmailClient(req.user);
        const response = await gmail.users.messages.get({
            userId: 'me',
            id: emailId,
            format: 'full'
        }); 

        //clean body for the model
        const payload = response.data.payload;
        let rawBody = getEmailBody(payload); 
        const cleanText = rawBody.replace(/\s+/g, ' ').trim().substring(0, 512);

        //call model (might env this)
        const mlUrl = process.env.ML_SERVICE_URL || 'http://127.0.0.1:8000';

        const mlResponse = await fetch(`${mlUrl}/predict`, {
            method:'POST',
            headers:{
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({text: cleanText})
        });

        if (!mlResponse.ok) {
            throw new Error(`Python API returned status: ${mlResponse.status}`);
        }

        const mlResult = await mlResponse.json();

        res.json({
            id: emailId,
            verdict: mlResult.prediction,
            confidence: mlResult.confidence   
        });
    } catch (error) {
        console.error('Scan Error:', error.message);
        res.status(503).json({ error: "Scan Failed", details: error.message });
}
});

//this just turns on the server
app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`)
});



