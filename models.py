import os
import sqlite3

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'database', 'iara.db')

def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # 1. Commercial Ships Registry
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            intl_number TEXT UNIQUE NOT NULL,
            call_sign TEXT,
            markings TEXT,
            owner_name TEXT,
            captain_name TEXT,
            length REAL,
            width REAL,
            tonnage REAL,
            power INTEGER
        )
    ''')
    
    # 2. Fishing Permits
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS permits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ship_id INTEGER,
            permit_year INTEGER,
            valid_until TEXT,
            allowed_gear TEXT,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY(ship_id) REFERENCES ships(id)
        )
    ''')
    
    # 3. Hobby Fishing Tickets
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hobby_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fisherman_name TEXT,
            egn TEXT,
            age_group TEXT,
            telk_decision TEXT,
            price REAL,
            issue_date TEXT,
            valid_until TEXT
        )
    ''')
    
    conn.commit()
    conn.close()