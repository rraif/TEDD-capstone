//load tools (dotenv, express, googleapis)
require('dotenv').config(); //opens .env file
const express = require('express'); //loads expressjs
const {google} = require('googleapis'); //google

const app = express(); //start server app


//we prepare our google IDs to show to google later
const oauth2Client = new google.auth.OAuth2(
    process.env.GOOGLE_CLIENT_ID,
    process.env.GOOGLE_CLIENT_SECRET,
    'http://localhost:5000/auth/google/callback'//where we go if google accepts
);

//when the user goes to localhost
app.get('/auth/google', (req, res) => {

    //make a list of permissions
    const scopes = [
    'https://www.googleapis.com/auth/gmail.readonly', // "I want to READ emails"
    'https://www.googleapis.com/auth/userinfo.email',  // "I want to know your email address"
    'https://www.googleapis.com/auth/userinfo.profile', 
    'openid'  
  ];

    //create special google url
    const url = oauth2Client.generateAuthUrl({
        access_type: 'offline',
        scope: scopes,
        prompt: 'consent'
    })

    //redirect user to the google url
    res.redirect(url);
});

app.get('/auth/google/callback', async (req, res) => {
    //grab the ticket from the URL (?)
    const {code} = req.query;

    //swap ticket for real tokens
    try{
    const{tokens} = await oauth2Client.getToken(code)

    //make us able touse tokens
    oauth2Client.setCredentials(tokens)

    const hasEmailScope = tokens.scope.includes('gmail.readonly');

    if (!hasEmailScope) {
      return res.send(`
        <h1>Access Denied</h1>
        <p>We cannot work without permission to read your emails.</p>
        <p>Please <a href="/auth/google">try again</a> and make sure to check the box!</p>
      `);
    }

    //ask gmail for the latest email
    const gmail = google.gmail({version:'v1', auth:oauth2Client});

    const response = await gmail.users.messages.list({
        userId:'me',
        maxResults:1
    });

    //display data on the screen
    res.send(response.data);

}catch (error){
    console.error(error);
    res.status(500).send('Authentication Failed');
}
});

//turn on the server
app.listen(5000, () => {
    console.log('Server is running on http://localhost:5000');
})


