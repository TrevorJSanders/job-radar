import sqlite3
import os

DB_NAME = "jobradar.db"

def get_db():
    """Returns a connection to the SQLite database with dictionary-like row access."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    # Enable foreign key support
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Initializes the database schema if tables do not exist."""
    conn = get_db()
    cursor = conn.cursor()

    # Table: applications
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company TEXT NOT NULL,
        role TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'applied',
        date_applied TEXT,
        source TEXT,
        fit_score INTEGER,
        notes TEXT,
        next_action TEXT,
        last_activity TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Table: emails
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS emails (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gmail_message_id TEXT UNIQUE NOT NULL,
        thread_id TEXT,
        application_id INTEGER REFERENCES applications(id) ON DELETE SET NULL,
        sender_name TEXT,
        sender_email TEXT,
        subject TEXT,
        body_snippet TEXT,
        received_at TEXT,
        classification_type TEXT,
        confidence_score REAL,
        raw_json TEXT,
        processed INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Table: review_queue
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS review_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email_id INTEGER REFERENCES emails(id) ON DELETE CASCADE,
        suggested_type TEXT,
        suggested_company TEXT,
        suggested_role TEXT,
        confidence_score REAL,
        reasoning TEXT,
        status TEXT DEFAULT 'pending',
        resolved_at TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()
    print(f"Database {DB_NAME} initialized successfully.")
