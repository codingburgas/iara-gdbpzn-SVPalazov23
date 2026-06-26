import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import init_db, DATABASE_PATH

app = Flask(__name__)
app.secret_key = 'iara_secret_key_for_messages'
init_db()

def init_users_db():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_users_db()

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Моля, влезте в системата, за да достъпите тази страница.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['logged_in'] = True
            session['username'] = username
            flash('Успешен вход в системата!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Грешно потребителско име или парола!', 'error')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Паролите не съвпадат!', 'error')
            return redirect(url_for('register'))
            
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            flash('Регистрацията е успешна! Сега можете да влезете.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Това потребителско име вече е заето!', 'error')
        finally:
            conn.close()
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    flash('Успешно излязохте от системата.', 'success')
    return redirect(url_for('home'))

@app.route('/ships', methods=['GET', 'POST'])
@login_required
def ships():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    if request.method == 'POST':
        intl_number = request.form.get('intl_number')
        call_sign = request.form.get('call_sign')
        markings = request.form.get('markings')
        owner_name = request.form.get('owner_name')
        captain_name = request.form.get('captain_name')
        length = request.form.get('length')
        width = request.form.get('width')
        power = request.form.get('power')

        try:
            cursor.execute('''
                INSERT INTO ships (intl_number, call_sign, markings, owner_name, captain_name, length, width, power)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (intl_number, call_sign, markings, owner_name, captain_name, length, width, power))
            conn.commit()
        except sqlite3.IntegrityError:
            pass

    cursor.execute('SELECT * FROM ships')
    all_ships = cursor.fetchall()
    conn.close()

    return render_template('ships.html', ships=all_ships)

@app.route('/permits', methods=['GET', 'POST'])
@login_required
def permits():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    if request.method == 'POST':
        ship_id = request.form.get('ship_id')
        permit_number = request.form.get('permit_number')
        fishing_gear = request.form.get('fishing_gear')
        valid_from = request.form.get('valid_from')
        valid_to = request.form.get('valid_to')

        cursor.execute('''
            INSERT INTO permits (ship_id, permit_number, fishing_gear, valid_from, valid_to)
            VALUES (?, ?, ?, ?, ?)
        ''', (ship_id, permit_number, fishing_gear, valid_from, valid_to))
        conn.commit()

    cursor.execute('SELECT id, intl_number, markings, owner_name FROM ships')
    all_ships = cursor.fetchall()

    cursor.execute('''
        SELECT permits.id, permits.valid_to, permits.permit_number, permits.fishing_gear, permits.valid_from, ships.intl_number 
        FROM permits 
        JOIN ships ON permits.ship_id = ships.id
    ''')
    all_permits = cursor.fetchall()
    conn.close()

    return render_template('permits.html', ships=all_ships, permits=all_permits)

@app.route('/logbook', methods=['GET', 'POST'])
@login_required
def logbook():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logbook (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ship_id INTEGER,
            fish_type TEXT,
            weight REAL,
            catch_date TEXT,
            FOREIGN KEY(ship_id) REFERENCES ships(id)
        )
    ''')
    conn.commit()

    if request.method == 'POST':
        ship_id = request.form.get('ship_id')
        fish_type = request.form.get('fish_type')
        weight = request.form.get('weight')
        catch_date = request.form.get('catch_date')

        cursor.execute('''
            INSERT INTO logbook (ship_id, fish_type, weight, catch_date)
            VALUES (?, ?, ?)
        ''', (ship_id, fish_type, weight, catch_date))
        conn.commit()

    cursor.execute('SELECT id, intl_number, markings FROM ships')
    all_ships = cursor.fetchall()

    cursor.execute('''
        SELECT logbook.id, logbook.fish_type, logbook.weight, logbook.catch_date, ships.intl_number 
        FROM logbook 
        JOIN ships ON logbook.ship_id = ships.id
    ''')
    all_entries = cursor.fetchall()
    conn.close()

    return render_template('logbook.html', ships=all_ships, logbook_entries=all_entries)

@app.route('/tickets')
@login_required
def tickets():
    return render_template('tickets.html')

@app.route('/tickets/calculate', methods=['POST'])
@login_required
def calculate_ticket():
    name = request.form.get('name')
    egn = request.form.get('egn')
    duration = request.form.get('duration')
    is_pensioner = request.form.get('is_pensioner')
    telk = request.form.get('telk')

    prices = {"1_week": 4.00, "1_month": 8.00, "6_months": 15.00, "1_year": 25.00}
    final_price = prices.get(duration, 25.00)

    try:
        year_part = int(egn[0:2])
        month_part = int(egn[2:4])
        if month_part > 40:
            birth_year = 2000 + year_part
        else:
            birth_year = 1900 + year_part
        current_year = datetime.now().year
        age = current_year - birth_year
    except:
        age = 20

    if telk and len(telk.strip()) > 0:
        final_price = 0.00
        age_group = "ТЕЛК Намаление"
    elif age < 14:
        final_price = 0.00
        age_group = "Дете под 14 г."
    elif is_pensioner == 'yes' or age >= 65:
        final_price = final_price * 0.50
        age_group = "Пенсионер"
    else:
        age_group = "Редовен"

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO hobby_tickets (name, egn, duration, is_pensioner, telk_number, price)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (name, egn, duration, is_pensioner if is_pensioner else 'no', telk, final_price))
    conn.commit()
    conn.close()

    flash(f"Успешно издаден билет за {name}! Категория: {age_group}. Цена: {final_price:.2f} лв.", "success")
    return redirect(url_for('tickets'))

@app.route('/inspections', methods=['GET', 'POST'])
@login_required
def inspections():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inspections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ship_id INTEGER,
            inspector_name TEXT,
            status TEXT,
            inspection_date TEXT,
            FOREIGN KEY(ship_id) REFERENCES ships(id)
        )
    ''')
    conn.commit()

    if request.method == 'POST':
        ship_id = request.form.get('ship_id')
        inspector_name = request.form.get('inspector_name')
        status = request.form.get('status')
        inspection_date = request.form.get('inspection_date')

        cursor.execute('''
            INSERT INTO inspections (ship_id, inspector_name, status, inspection_date)
            VALUES (?, ?, ?, ?)
        ''', (ship_id, inspector_name, status, inspection_date))
        conn.commit()

    cursor.execute('SELECT id, intl_number, markings FROM ships')
    all_ships = cursor.fetchall()

    cursor.execute('''
        SELECT inspections.id, inspections.inspector_name, inspections.status, inspections.inspection_date, ships.intl_number 
        FROM inspections 
        JOIN ships ON inspections.ship_id = ships.id
    ''')
    all_inspections = cursor.fetchall()
    conn.close()

    return render_template('inspections.html', ships=all_ships, inspections=all_inspections)

if __name__ == '__main__':
    app.run(debug=True)