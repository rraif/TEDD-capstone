/* this takes the .env file, which contains our secret stuff
and loads it into process.env, which is in memory */
require('dotenv').config(); 

const db = require('./database.js')

/* this contains standard web server features for nodejs so we
don't have to set it up ourselves, we just decide what we want
it to do */
const express = require('express'); 

/* the thing that checks your id */
const passport = require('passport');

/* the thing that lets passport know how to check google IDs */
const GoogleStrategy = require('passport-google-oauth20').Strategy;

/* creates sessions and session ID for users to remember them */
const session = require('express-session');

const pgSession = require('connect-pg-simple')(session);

/* backend is port 5000, frontend is port 5173, this basically allows
frontend to talk to backend despite having different ports */
const cors = require('cors');

/* we get google stuff */
const {google} = require('googleapis'); 

const DOMPurify = require('isomorphic-dompurify')
const {encrypt, decrypt} = require('./crypto.js')

/* this creates the server instance */
const app = express(); 
const PORT = 5000;

/* our backend is port 5000, the snippet below
allows requests from port 5173 (react) to be accepted
we do this because browsers think different ports are a security threat,
so we whitelist this interaction

credentials: true tells the browser that cookies from backend and frontend are valid
and should be remembered/saved */
app.use(cors({
    origin: 'http://localhost:5173',
    credentials: true
}));

/* this converts json data sent from the frontend into JS objects 
(this part is not used yet, but will be for something like "mark as unsafe" feature) */
app.use(express.json())

/* this snippet decides how cookies work for our web app */
app.use(session({
    store: new pgSession({
        pool: db.pool,
        tableName: 'session'
    }),
    secret:process.env.SESSION_SECRET, // if a cookie doesn't have our session secret, it's invalid
    resave:false, // our web app won't rewrite a user's data if nothings changed
    saveUninitialized: false, // our web app won't remember people who don't login
    cookie: {
        secure: false,  // false for http, true for https
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
    callbackURL: 'http://localhost:5000/auth/google/callback' //passport tells the user to go to this address after going to Google
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
        encryptedRefreshToken: user.encryptedRefreshToken
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
        failureRedirect: 'http://localhost:5173/login?error=true' //if the user is fake, go back to login
    }),
    (req, res) => { //if the user isnt fake...

    res.redirect('http://localhost:5173/inbox'); //go to their respective inbox
});

/* get current user is the frontend asking "who am i?" or "who is logged in?" 
the backend runs deserializeUser and gets user
then it says you are "user" or you are null if there is no user detected
then the frontend does whatever function with that specific user*/
app.get('/api/current_user', (req, res) => {
    res.send(req.user || null);
});


app.get('/logout', (req, res, next) => {
    req.logout((err) => {
        if (err) return next(err);
        res.redirect('http://localhost:5173');
    });
});

/*define email route
async allows us to use "await" which pauses execution while google fetches email data
async just basically means this is a function that might take a while*/
app.get('/api/emails', async (req, res) =>{

    //check if user is not logged in or if the user is missing tokens
    if(!req.isAuthenticated() || !req.user.refreshToken) {
        return res.status(401).json({error: 'Unauthorized'});
    }

    //if the user is valid,
    try {
        //create a new instance of the oauth 2 client with our credentials
        //to let google know its us
        const oauth2Client = new google.auth.OAuth2(
            process.env.GOOGLE_CLIENT_ID,
            process.env.GOOGLE_CLIENT_SECRET,
            process.env.GOOGLE_CALLBACK_URL,
        );


        //load our keys into the client to identify the user
        oauth2Client.setCredentials({
            refresh_token: req.user.refreshToken
        });


        //create a gmail object
        const gmail = google.gmail({version: 'v1', auth: oauth2Client});


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

        res.status(401).json({error: 'Token expired or invalid', details: error.message});
    }
});

//this just turns on the server
app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`)
});



