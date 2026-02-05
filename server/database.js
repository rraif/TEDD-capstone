const { Pool } = require('pg');

/*sets up 10 connections (default) that can go to our database
 and fetch data to send to client*/ 
const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    ssl: {rejectUnauthorized: true}
});

/* other files communicate what to get from the database
using this and only this

this gets sent to a connection to fetch data

parametrized queries :)*/
module.exports = {
    query: (text, params) => pool.query(text, params),
    pool: pool
}