import sqlite3

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # Enforce foreign key constraints
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Creating users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password TEXT,
            year TEXT,
            semester TEXT,
            academic_year TEXT,
            school TEXT,
            branch TEXT
        )
    ''')

    # Creating professors table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS professors (
            id INTEGER PRIMARY KEY,
            Name TEXT,
            Designation TEXT,
            Photo TEXT,
            Avg_rating REAL,
            no_ratings INTEGER,
            Profile TEXT
        )
    ''')

    # Creating ratings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            professor_id INTEGER,
            user_email TEXT,
            teaching_rating INTEGER,
            content_rating INTEGER,
            overall_rating INTEGER,
            rating REAL,
            comment TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (professor_id) REFERENCES professors (id),
            FOREIGN KEY (user_email) REFERENCES users (email)
        )
    ''')

    # Creating reviews table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            professor_id INTEGER,
            user_email TEXT,
            review TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (professor_id) REFERENCES professors (id),
            FOREIGN KEY (user_email) REFERENCES users (email)
        )
    ''')

    # Creating community_users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS community_users (
            email TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            FOREIGN KEY (email) REFERENCES users(email) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS community_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES community_users(username) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS community_replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES community_posts(id) ON DELETE CASCADE,
            FOREIGN KEY (username) REFERENCES community_users(username) ON DELETE CASCADE
        )
    ''')

    # Add parent_reply_id column if not exists
    cursor.execute("PRAGMA table_info(community_replies)")
    columns = [row["name"] for row in cursor.fetchall()]
    if "parent_reply_id" not in columns:
        cursor.execute("ALTER TABLE community_replies ADD COLUMN parent_reply_id INTEGER")

    cursor.execute("DELETE FROM professors WHERE id = 231")
    cursor.execute("DELETE FROM professors WHERE id = 205")
    cursor.execute("DELETE FROM professors WHERE id = 213")
    cursor.execute("DELETE FROM professors WHERE id = 214")
    cursor.execute("DELETE FROM professors WHERE id = 253")
    cursor.execute("DELETE FROM professors WHERE id = 228")
    cursor.execute("DELETE FROM professors WHERE id = 234")
    cursor.execute("DELETE FROM professors WHERE id = 190")
    cursor.execute("DELETE FROM professors WHERE id = 218")
    cursor.execute("DELETE FROM professors WHERE id = 216")
    cursor.execute("DELETE FROM professors WHERE id = 203")
    cursor.execute("DELETE FROM professors WHERE id = 204")
    cursor.execute("DELETE FROM professors WHERE id = 222")
    cursor.execute("DELETE FROM professors WHERE id = 217")
    cursor.execute("DELETE FROM professors WHERE id = 206")
    cursor.execute("DELETE FROM professors WHERE id = 223")
    cursor.execute("DELETE FROM professors WHERE id = 120")
    cursor.execute("DELETE FROM professors WHERE id = 198")
    cursor.execute("DELETE FROM professors WHERE id = 212")
    cursor.execute("DELETE FROM professors WHERE id = 235")
    cursor.execute("DELETE FROM professors WHERE id = 231")
    cursor.execute("DELETE FROM professors WHERE id = 207")
    
    # Email of the user to delete


    conn.commit()
    conn.close()

