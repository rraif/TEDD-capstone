const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '../.env') });

const db = require('./database.js')
const express = require('express'); 
const helmet = require('helmet');

const rateLimit = require('express-rate-limit');
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000,
    limit: 5000, //change before deploy
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
const crypto = require('crypto');

const app = express(); 
const PORT = process.env.PORT;
const CLIENT_URL = process.env.CLIENT_URL;

const MAX_EMAILS = 25;       
const FETCH_CHUNK_SIZE = 45; // How many to grab from Google per API call

const generateTeamCode = () => {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let code = '';
    for (let i = 0; i < 6; i++) {
        code += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return code;
};

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

const getEmailBody = async (payload, gmail = null, messageId = null) => {
    let htmlBody = '';
    let plainBody = '';
    let inlineImages = {}; 

    // 🚀 2. Made the recursive helper async
    const extractParts = async (part) => {
        if (part.mimeType === 'text/html' && part.body && part.body.data) {
            htmlBody = Buffer.from(part.body.data, 'base64url').toString('utf-8');
        } 
        else if (part.mimeType === 'text/plain' && part.body && part.body.data) {
            plainBody = Buffer.from(part.body.data, 'base64url').toString('utf-8');
        }
        // 🚀 3. THE FIX: Look for attachmentId if data is missing!
        else if (part.headers && part.body && part.mimeType.startsWith('image/')) {
            const cidHeader = part.headers.find(h => h.name.toLowerCase() === 'content-id');
            if (cidHeader) {
                const cid = cidHeader.value.replace(/[<>]/g, '');
                let base64Data = null;
                
                // If it's a tiny image, Google gives us the data directly
                if (part.body.data) {
                    base64Data = part.body.data;
                } 
                // If it's a normal/large image, we have to fetch it using the attachmentId
                else if (part.body.attachmentId && gmail && messageId) {
                    try {
                        const attachment = await gmail.users.messages.attachments.get({
                            userId: 'me',
                            messageId: messageId,
                            id: part.body.attachmentId
                        });
                        base64Data = attachment.data.data;
                    } catch (err) {
                        console.error('Failed to fetch image attachment:', err);
                    }
                }
                
                if (base64Data) {
                    const cleanBase64 = base64Data.replace(/-/g, '+').replace(/_/g, '/');
                    inlineImages[cid] = `data:${part.mimeType};base64,${cleanBase64}`;
                }
            }
        }

        // 🚀 4. Await the recursive digger
        if (part.parts) {
            for (const subPart of part.parts) {
                await extractParts(subPart); 
            }
        }
    };

    if (payload.body && payload.body.data) {
        return Buffer.from(payload.body.data, 'base64url').toString('utf-8');
    }

    // 🚀 5. Await the main extraction
    await extractParts(payload);

    let finalBody = htmlBody || plainBody || 'No readable text found';

    if (Object.keys(inlineImages).length > 0 && finalBody !== 'No readable text found') {
        for (const [cid, dataUri] of Object.entries(inlineImages)) {
            const cidRegex = new RegExp(`cid:${cid}`, 'g');
            finalBody = finalBody.replace(cidRegex, dataUri);
        }
    }
    
    return finalBody;
};

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
passport.deserializeUser(async (sessionUser, done) => {
    try {
        //get newest user data
        const result = await db.query('SELECT * FROM users WHERE google_id = $1', [sessionUser.google_id]);

        if (result.rows.length > 0) {
            const freshUser = result.rows[0];

            //refresh token so inbox still works
            if (sessionUser.encryptedRefreshToken) {
                freshUser.refreshToken = decrypt(sessionUser.encryptedRefreshToken);
            }

            done(null, freshUser);
        } else {
            done(null, false);
        }
    } catch (err) {
        console.error("Deserialize error:", err);
        done(err, null);
    }
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
try {
        const googleId = req.user.google_id;
        
        // 1. Fetch hidden IDs
        const hiddenQuery = await db.query('SELECT email_id FROM hidden_emails WHERE google_id = $1', [googleId]);
        const hiddenIds = hiddenQuery.rows.map(row => row.email_id);

        // Setup Gmail Client
        const oauth2Client = new google.auth.OAuth2(process.env.GOOGLE_CLIENT_ID, process.env.GOOGLE_CLIENT_SECRET);
        oauth2Client.setCredentials({ refresh_token: req.user.refreshToken });
        const gmail = google.gmail({ version: 'v1', auth: oauth2Client });

        // 2. Loop through Gmail pages until we find 10 visible emails
        let visibleMessages = [];
        let pageToken = undefined;

        while (visibleMessages.length < MAX_EMAILS) {
            const listResponse = await gmail.users.messages.list({
                userId: 'me',
                maxResults: FETCH_CHUNK_SIZE, // Fetch in chunks of 20 to be efficient
                pageToken: pageToken
            });

            const messages = listResponse.data.messages || [];
            if (messages.length === 0) break; // We reached the absolute end of their inbox

            // Filter this chunk
            const newlyVisible = messages.filter(msg => !hiddenIds.includes(msg.id));
            visibleMessages = visibleMessages.concat(newlyVisible);

            pageToken = listResponse.data.nextPageToken;
            if (!pageToken) break; // No more pages to fetch
        }

        // 3. Slice the array to guarantee EXACTLY 10 emails (in case the last chunk pushed us to 12 or 15)
        visibleMessages = visibleMessages.slice(0, MAX_EMAILS);

        if (visibleMessages.length === 0) {
            return res.json({ emails: [] });
        }

        // 4. Fetch the actual content for our 10 confirmed visible emails
        const emailDetails = await Promise.all(
            visibleMessages.map(async (msg) => {
                const detail = await gmail.users.messages.get({
                    userId: 'me',
                    id: msg.id,
                    format: 'metadata'
                });
            
                const headers = detail.data.payload.headers;
                const subject = DOMPurify.sanitize(headers.find(h => h.name === 'Subject')?.value || '(No Subject)');
                const from = DOMPurify.sanitize(headers.find(h => h.name === 'From')?.value || '(Unknown)');
                const snippet = DOMPurify.sanitize(detail.data.snippet);
                const date = headers.find(h => h.name === 'Date')?.value;
                
                return {
                    id: msg.id,
                    threadId: msg.threadId,
                    subject: subject,
                    from: from,
                    date: date,
                    snippet: snippet
                };
            })
        );

        res.json({ emails: emailDetails });
    } catch (error) {
        console.error('Gmail API Error:', error);
        res.status(401).json({error: 'Token expired or invalid'});
    }
});

app.post('/api/emails/hide', requireGoogleAuth, async (req, res) => {
    const {emailId} = req.body;
    const googleId = req.user.google_id;

    if(!emailId) return res.status(400).json({error: 'email id required'});

    try {
        await db.query(
        'INSERT INTO hidden_emails (google_id, email_id) VALUES ($1, $2) ON CONFLICT DO NOTHING', 
        [googleId, emailId]
        );
        res.json({success: true});
    } catch (err) {
        console.error('error hiding email:', err);
        res.status(500).json({error: 'server error while hiding email'});
    }
});

app.get('/api/emails/hidden', requireGoogleAuth, async (req, res) => {
    const googleId = req.user.google_id;

    try{
        const hiddenQuery = await db.query('SELECT email_id FROM hidden_emails WHERE google_id = $1', [googleId]);
        const hiddenIds = hiddenQuery.rows.map(row => row.email_id);

        if (hiddenIds.length === 0){
            return res.json({success: true, emails: []});
        }

        const oauth2Client = new google.auth.OAuth2(process.env.GOOGLE_CLIENT_ID, process.env.GOOGLE_CLIENT_SECRET);
        oauth2Client.setCredentials({refresh_token: req.user.refreshToken});
        const gmail = google.gmail({version: 'v1', auth: oauth2Client});

        const emailDetails =  [];

        for (const id of hiddenIds){
            try{
                const mail = await gmail.users.messages.get({
                    userId: 'me',
                    id: id,
                    format: 'metadata',
                    metadataHeaders: ['Subject', 'From', 'Date']      
                });

                //purify?
                const headers = mail.data.payload.headers;
                const subject = headers.find(h => h.name === 'Subject')?.value || 'No Subject';
                const from = headers.find(h => h.name === 'From')?.value || 'Unknown Sender';
                const date = headers.find(h => h.name === 'Date')?.value || '';

                emailDetails.push({
                    id: mail.data.id, 
                    subject, 
                    from, 
                    date, 
                    snippet: mail.data.snippet }
                );
            } catch (gmailErr) {
                console.error(`cannot fetch hidden email ${id}:`, gmailErr.message);
            }
        }
           res.json({success: true, emails: emailDetails});
    } catch (err) {
        console.error('Error fetching hidden emails:', err);
        res.status(500).json({ error: "Server error" });
    }
});

app.post('/api/emails/unhide', requireGoogleAuth, async (req, res) => {
    const { emailId } = req.body;
    const googleId = req.user.google_id;

    if (!emailId) return res.status(400).json({ error: "Email ID is required" });

    try {
        await db.query(
            'DELETE FROM hidden_emails WHERE google_id = $1 AND email_id = $2',
            [googleId, emailId]
        );
        res.json({ success: true });
    } catch (err) {
        console.error('Error unhiding email:', err);
        res.status(500).json({ error: "Server error while unhiding email" });
    }
});


app.get('/api/emails/:id', requireGoogleAuth, async (req, res) => {
try {
        const gmail = getGmailClient(req.user);

        // 🚀 1. Fetch BOTH the parsed 'full' data and the 'raw' MIME data concurrently
        const [response, rawResponse] = await Promise.all([
            gmail.users.messages.get({ userId: 'me', id: req.params.id, format: 'full' }),
            gmail.users.messages.get({ userId: 'me', id: req.params.id, format: 'raw' })
        ]);

        const payload = response.data.payload;
        const headers = payload.headers;
        
        // Ensure you are using the async getEmailBody we fixed earlier!
        const rawBody = await getEmailBody(payload, gmail, req.params.id);

        // 🚀 2. Decode the raw email and extract the MIME boundaries
        const rawEmailString = Buffer.from(rawResponse.data.raw, 'base64url').toString('utf-8');
        const splitIndex = rawEmailString.indexOf('\r\n\r\n'); // Headers end at the first double-space
        const rawMimeBody = splitIndex !== -1 ? rawEmailString.substring(splitIndex + 4) : 'No raw body found.';

        const cleanData = {
            id: response.data.id,
            subject: DOMPurify.sanitize(headers.find(h => h.name === 'Subject')?.value || '(No Subject)'),
            from: DOMPurify.sanitize(headers.find(h => h.name === 'From')?.value || '(Unknown)'),
            to: DOMPurify.sanitize(headers.find(h => h.name === 'To')?.value || '(Unknown)'),
            date: headers.find(h => h.name === 'Date')?.value, 
            body: DOMPurify.sanitize(rawBody)
        };

        res.json({
            basic: cleanData,
            headers: headers,
            rawMimeBody: rawMimeBody // 🚀 3. Send the raw MIME text to the frontend
        });

    } catch (error) {
        console.error('gmail get error', error);
        res.status(500).json({error:"internal server error"});
    }
});

app.post('/api/scan', requireGoogleAuth, async(req, res) => {
const {emailId} = req.body;

    // 1. Safety check (kept from your old code!)
    if (!emailId) return res.status(400).json({error: 'email ID required'});

    try{
        const gmail = getGmailClient(req.user);
        
        // 2. Get RAW email (Changed from 'full' to 'raw' because the new model needs the whole MIME string)
        const response = await gmail.users.messages.get({
            userId: 'me',
            id: emailId,
            format: 'raw'
        }); 

        const rawEmailString = Buffer.from(response.data.raw, 'base64url').toString('utf-8');

        // 3. Call new ensemble model (Kept your native fetch and environment variables!)
        const mlUrl = process.env.ML_SERVICE_URL || 'http://127.0.0.1:8000';

        const mlResponse = await fetch(`${mlUrl}/parse-and-predict`, {
            method:'POST',
            headers:{
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({email_content: rawEmailString})
        });

        if (!mlResponse.ok) {
            throw new Error(`Python API returned status: ${mlResponse.status}`);
        }

        const mlResult = await mlResponse.json();
        const analysis = mlResult.combined_analysis;

        // 4. Return exact format frontend expects, plus the new details for later
        res.json({
            id: emailId,
            verdict: analysis.final_prediction,
            confidence: analysis.total_score,
            details: mlResult // Added for the Explainable AI box!
        });
    } catch (error) {
        console.error('Scan Error:', error.message);
        res.status(503).json({ error: "Scan Failed", details: error.message });
    }
});

//user profile
app.get('/api/current-user', requireGoogleAuth, async (req, res) => {
    try {
        // 🚀 Modified to JOIN the teams table and grab team_name
        const userQuery = await db.query(
            `SELECT u.user_id, u.google_id, u.email, u.display_name, 
                    u.user_score, u.survival_streak, u.title, 
                    u.team_id, u.is_team_admin, t.team_name 
             FROM users u 
             LEFT JOIN teams t ON u.team_id = t.team_id 
             WHERE u.google_id = $1`,
            [req.user.google_id]
        );
    
        if (userQuery.rows.length === 0) {
            return res.status(404).json({error: "user not in database"});
        }

        res.json(userQuery.rows[0]);
    } catch (err) {
        console.error("error fetching current user:", err);
        res.status(500).json({error: "Server error"});
    }
});

//creat team (dompurify the team name)
app.post('/api/teams/create', requireGoogleAuth, async(req, res) =>{
    const {teamName} = req.body;
    const googleId = req.user.google_id;

    const cleanTeamName = DOMPurify.sanitize(teamName);

    if(!cleanTeamName) return res.status(400).json({error: "team name is required"});

    try {
        let isCodeUnique = false;
        let newCode = '';
        let hashedCode = '';

        //generate code and check code collision
        while (!isCodeUnique) {
            newCode = generateTeamCode();

            hashedCode = crypto.createHash('sha256').update(newCode).digest('hex');

            const check = await db.query('SELECT * FROM teams WHERE hashed_join_code =$1', [hashedCode]);
            if (check.rows.length === 0) isCodeUnique = true;
        }


        const encryptedCode = encrypt(newCode);

        //create team
        const newTeam = await db.query(
            `INSERT INTO teams (team_name, hashed_join_code, encrypted_join_code, created_by) VALUES ($1, $2, $3, $4) RETURNING *`,
            [cleanTeamName, hashedCode, encryptedCode, googleId]
        );
        const teamId = newTeam.rows[0].team_id;

        //make creator the admin
        await db.query(
            'UPDATE users SET team_id = $1, is_team_admin = TRUE WHERE google_id = $2',
            [teamId, googleId]
        );

        const teamResponse = newTeam.rows[0];
        teamResponse.join_code = newCode;

        res.json({success: true, team: teamResponse});
    }catch (err) {
        console.error('Create team error:', err);
        res.status(500).json({error: 'failed to create team'});
    }
});

//join team (dompurify the entering code)
app.post('/api/teams/join', requireGoogleAuth, async(req, res) => {
    const {joinCode} = req.body;
    const googleId = req.user.google_id;

    if (!joinCode) return res.status(400).json({error: 'join code required'});

    const cleanJoinCode = DOMPurify.sanitize(joinCode.toUpperCase());

    try{
        const hashedInput = crypto.createHash('sha256').update(cleanJoinCode).digest('hex');
        const teamResult = await db.query('SELECT * FROM teams WHERE hashed_join_code = $1', [hashedInput]);

        if (teamResult.rows.length === 0){
            return res.status(404).json({error: 'invalid team code'});
        }

        const teamId = teamResult.rows[0].team_id;

        //add non-admin user to team
        await db.query(
            'UPDATE users SET team_id = $1, is_team_admin = FALSE WHERE google_id = $2',
            [teamId, googleId]
        );

        res.json({success: true, team: teamResult.rows[0]});
    } catch (err) {
        console.error('join team error:', err);
        res.status(500).json({error: "Failed to join team"});
    }
});

//get team
app.get('/api/teams/current', requireGoogleAuth, async (req, res) =>{
    try {
        if (!req.user.team_id) return res.status(400).json({error: 'no team assigned'});

        const teamRes = await db.query('SELECT * FROM teams WHERE team_id = $1', [req.user.team_id]);
        if (teamRes.rows.length === 0) return res.status(404).json({error: "team not found"});

        const teamData = teamRes.rows[0];

        try{
            teamData.join_code = decrypt(teamData.encrypted_join_code);
        } catch(decryptErr){
            console.error("Decryption failed", decryptErr);
            teamData.join_code = 'error_decrypting';
        }

        const membersRes = await db.query(
            'SELECT user_id, display_name, email, user_score, survival_streak, title, is_team_admin FROM users WHERE team_id = $1 ORDER BY is_team_admin DESC, user_score DESC',
            [req.user.team_id]
        );

        res.json({team: teamRes.rows[0], members: membersRes.rows});
    } catch (err) {
        console.error('Fetch team error:', err);
        res.status(500).json({error:'server error'});
    }
});

//kick member
app.delete('/api/teams/members/:userId', requireGoogleAuth, async(req, res) => {
    try{
        if(!req.user.is_team_admin) return res.status(403).json({error: "admin feature only"});

        await db.query(
            'UPDATE users SET team_id = NULL, is_team_admin = FALSE WHERE user_id = $1 AND team_id = $2',
            [req.params.userId, req.user.team_id]
        );

        res.json({success: true});
    } catch (err) {
        console.error('Kick member error:', err);
        res.status(500).json({error: "server error"});
    }
});

//delete entire team (it has to remove users first before deleting team)
//or else the team cant be deleted
app.delete('/api/teams/current', requireGoogleAuth, async (req, res) => {
    try {
        if (!req.user.is_team_admin) return res.status(403).json({error: "admin action only"});

        //doesnt this just remove members? the admin is still in, so it cant be deleted?
        await db.query('UPDATE users SET team_id = NULL, is_team_admin = FALSE WHERE team_id = $1', [req.user.team_id]);
    
        await db.query('DELETE FROM teams WHERE team_id = $1', [req.user.team_id]);

        res.json({success: true});
    } catch(err){
        console.error('Delete team error:', err);
        res.status(500).json({error: "server error"});
    }
});

//this just turns on the server
app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`)
});



