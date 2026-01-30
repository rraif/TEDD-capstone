// Load the .env file (Crucial! Without this, process.env is empty)
require('dotenv').config();

// Import your new database module
const db = require('./database.js');

async function testConnection() {
  try {
    console.log("Attempting to connect to Neon...");
    
    // The Query: Ask the database for the current time
    const result = await db.query('SELECT NOW()');
    
    console.log("✅ SUCCESS! Connected to the database.");
    console.log("Database Time:", result.rows[0].now);
    
    // We force the script to exit, otherwise the pool keeps the connection open
    process.exit(0);
    
  } catch (err) {
    console.error("❌ CONNECTION FAILED:", err);
    process.exit(1);
  }
}

testConnection();