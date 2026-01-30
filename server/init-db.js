require('dotenv').config();
const db = require('./database.js');


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

    await db.query(createUsersTable);
    await db.query(createSessionsTable);
    
    await db.query(`
      ALTER TABLE "session" ADD CONSTRAINT "session_pkey" PRIMARY KEY ("sid") NOT DEFERRABLE INITIALLY IMMEDIATE;
    `);
    
    await db.query(`
      CREATE INDEX IF NOT EXISTS "IDX_session_expire" ON "session" ("expire");
    `);

    console.log("users and sessions table created");
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