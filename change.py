import sqlite3
import pandas as pd

# Load data from CSV
df = pd.read_csv('modified.csv')

# Connect to your SQLite database
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Optional: Create the table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS professors (
        id INTEGER PRIMARY KEY,
        Name TEXT,
        Designation TEXT,
        Photo TEXT,
        Profile TEXT,
        Avg_rating REAL,
        no_ratings INTEGER
    )
''')

# Insert or replace entries to avoid duplicates
for _, row in df.iterrows():
    cursor.execute('''
        INSERT OR REPLACE INTO professors (id, Name, Designation, Photo, Profile, Avg_rating, no_ratings)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        int(row['id']),
        row['Name'],
        row['Designation'],
        row['Photo'],
        row['Profile'],
        float(row['Avg_rating']),
        int(row['no_ratings'])
    ))

# Save changes and close connection
conn.commit()
conn.close()

print("CSV data successfully imported into the professors table.")
