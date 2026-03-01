const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '../.env') });
const db = require('./database.js');
const { create } = require('domain');


async function initDatabase() {
  try {
    console.log("Building database");
    
    const createUsersTable = `
        CREATE TABLE IF NOT EXISTS users ( 
        user_id SERIAL PRIMARY KEY,
        google_id VARCHAR(255) UNIQUE NOT NULL,
        email VARCHAR(255) NOT NULL,
        display_name VARCHAR(255),

        user_score INTEGER DEFAULT 0,
        survival_streak INTEGER DEFAULT 0,
        strengths TEXT,
        weaknesses TEXT,
        title VARCHAR(255),

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    `;

      const createSessionsTable = `
        CREATE TABLE IF NOT EXISTS "session" ( 
        "sid" varchar NOT NULL COLLATE "default",
        "sess" json NOT NULL,
        "expire" timestamp(6) NOT NULL
    )
    WITH (OIDS=FALSE);
    `;

    const createTeamsTable = `
        CREATE TABLE IF NOT EXISTS teams (
        team_id SERIAL PRIMARY KEY,
        team_name VARCHAR(255) NOT NULL,
        hashed_join_code VARCHAR(64) UNIQUE NOT NULL,
        encrypted_join_code TEXT NOT NULL,           
        created_by VARCHAR(255) NOT NULL, -- google_id of creator
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    `;

    const createHiddenEmailsTable = `
        CREATE TABLE IF NOT EXISTS hidden_emails (
        google_id VARCHAR(255) NOT NULL,
        email_id VARCHAR(255) NOT NULL,
        hidden_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (google_id, email_id) -- Prevents adding the same email twice
  );
    `;

    await db.query(createUsersTable);
    await db.query(createSessionsTable);
    await db.query(createTeamsTable);
    await db.query(createHiddenEmailsTable);
    
    await db.query(`ALTER TABLE users ADD COLUMN IF NOT EXISTS team_id INTEGER REFERENCES teams(team_id);`);
    await db.query(`ALTER TABLE users ADD COLUMN IF NOT EXISTS is_team_admin BOOLEAN DEFAULT FALSE;`);

    await db.query(`
      ALTER TABLE "session" DROP CONSTRAINT IF EXISTS "session_pkey";
      ALTER TABLE "session" ADD CONSTRAINT "session_pkey" PRIMARY KEY ("sid") NOT DEFERRABLE INITIALLY IMMEDIATE;
    `);
    
    await db.query(`
      CREATE INDEX IF NOT EXISTS "IDX_session_expire" ON "session" ("expire");
    `);

    console.log("users, sessions, teams created");
    process.exit(0);
    
  } catch (err) {
    if (err.code === '42P07') { 
        console.log("tables already exist");
        process.exit(0);
    }
    console.error("users and tables table creation failed", err);
    process.exit(1);
  }
}

initDatabase();