//load tools (dotenv, express, googleapis)
require('dotenv').config(); //opens .env file
const express = require('express'); //loads expressjs
const passport = require('passport');
const GoogleStrategy = require('passport-google-oauth20').Strategy;
const session = require('express-session');
const cors = require('cors');
const {google} = require('googleapis'); //google

const app = express(); //start server app
const PORT = 5000;

//middleware setup
//allow react to send cookies
app.use(cors({
    origin: 'http://localhost:5173',
    credentials: true
}));

app.use(express.json())

//this session config currently uses ram, will change after adding postgres
app.use(session({
    secret:process.env.SESSION_SECRET,
    resave:false,
    saveUninitialized: false,
    cookie: {
        secure: false, //set to true if deploy to https
        maxAge: 24 * 60 * 60 * 1000 //24 hours
    }
}));

//init passport
app.use(passport.initialize());
app.use(passport.session());

//passport strategy
passport.use(new GoogleStrategy({
    clientID: process.env.GOOGLE_CLIENT_ID,
    clientSecret: process.env.GOOGLE_CLIENT_SECRET,
    callbackURL: 'http://localhost:5000/auth/google/callback'//where we go if google accepts
},
(accessToken, refreshToken, profile, done) => {
    const user = {
        googleId: profile.id,
        email: profile.emails[0].value,
        name: profile.displayName,
        tokens: {
            access_token: accessToken,
            refresh_token: refreshToken
        }
    };

    //for future use when postgres 
    return done(null,user);
}));

//what goes into the cookie
passport.serializeUser((user, done) => {
    done(null, user);
});

//unpack the cookie on every request
passport.deserializeUser((user, done) => {
    done(null, user);
});

//login trigger
app.get('/auth/google', 
    passport.authenticate('google', {
        scope: ['https://www.googleapis.com/auth/gmail.readonly', 'email',  'profile', 'openid' ],
        accessType: 'offline',
        prompt: 'consent'
    })
);

//when the user goes to localhost/auth/google
app.get('/auth/google/callback', 
    passport.authenticate('google', {
        failureRedirect: 'http://localhost:5173/login?error=true'
    }),
    (req, res) => {
    //redirect user to the dashboard
    res.redirect('http://localhost:5173/inbox');
});

//check if user is logged in
app.get('/api/current_user', (req, res) => {
    res.send(req.user || null);
});

//logout
app.get('/logout', (req, res, next) => {
    req.logout((err) => {
        if (err) return next(err);
        res.redirect('http://localhost:5173');
    });
});

//protected api (emails)
app.get('/api/emails', async (req, res) =>{
    //is user logged in?
    if(!req.isAuthenticated() || !req.user.tokens) {
        return res.status(401).json({error: 'Unauthorized'});
    }

    try {
        const{access_token, refresh_token } = req.user.tokens;

        //prevent user from seeing another's emails
        const oauth2Client = new google.auth.OAuth2(
            process.env.GOOGLE_CLIENT_ID,
            process.env.GOOGLE_CLIENT_SECRET,
            process.env.GOOGLE_CALLBACK_URL,
        );

        //load tokens
        oauth2Client.setCredentials({
            access_token: access_token,
            refresh_token: refresh_token
        });

        //fetch emails
        const gmail = google.gmail({version: 'v1', auth: oauth2Client});

        const response = await gmail.users.messages.list({
            userId:'me',
            maxResults: 10
        });

        res.json(response.data);
    } catch (error) {
        console.error('Gmail API Error:', error);
        //tell frontend to login again if token isnt valid
        res.status(401).json({error: 'Token expired or invalid', details: error.message});
    }
});

app.listen(PORT, () => {
    console.log('Server running on http://localhost:${PORT}')
});



