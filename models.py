import sqlite3
import os

# Път до базата данни в папка database/
DATABASE_DIR = os.path.join(os.path.dirname(__file__), 'database')
DATABASE_PATH = os.path.join(DATABASE_DIR, 'iara.db')

def init_db():
    # Създава папката database, ако не съществува
    if not os.path.exists(DATABASE_DIR):
        os.makedirs(DATABASE_DIR)
        
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # 1. Таблица за Търговски Кораби
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            intl_number TEXT UNIQUE NOT NULL, -- CFR / IMO Номер
            call_sign TEXT,                  -- Отличителен знак
            markings TEXT NOT NULL,           -- Външна маркировка (напр. БР-123)
            owner_name TEXT NOT NULL,         -- Собственик
            captain_name TEXT NOT NULL,       -- Капитан
            length REAL,                      -- Дължина
            width REAL,                       -- Ширина
            power INTEGER                     -- Мощност (к.с.)
        )
    ''')

    # 2. Таблица за Разрешителни за Стопански Риболов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS permits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ship_id INTEGER NOT NULL,          -- Връзка към кораба от таблица ships
            permit_number TEXT UNIQUE NOT NULL, -- Номер на разрешителното
            fishing_gear TEXT NOT NULL,        -- Риболовни уреди
            valid_from TEXT NOT NULL,          -- Валидно от (дата)
            valid_to TEXT NOT NULL,            -- Валидно до (дата)
            FOREIGN KEY (ship_id) REFERENCES ships (id)
        )
    ''')

    # 3. Таблица за Любителски Риболовни Билети
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hobby_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,                -- Три имена
            egn TEXT NOT NULL,                 -- ЕГН
            duration TEXT NOT NULL,            -- Период (1 седмица, 1 месец и т.н.)
            is_pensioner TEXT DEFAULT 'no',    -- Дали е пенсионер
            telk_number TEXT,                  -- Номер на ТЕЛК (ако има)
            price REAL NOT NULL                -- Платена такса
        )
    ''')

    conn.commit()
    conn.close()
    print("Базата данни и таблиците бяха инициализирани успешно в папката database!")

if __name__ == '__main__':
    init_db()