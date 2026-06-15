import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for
from models import init_db, DATABASE_PATH

app = Flask(__name__)
init_db()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/ships', methods=['GET', 'POST'])
def ships():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Ако инспекторът изпрати формата (POST заявка)
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
            # Предотвратява грешка, ако се въведе кораб с вече съществуващ CFR номер
            pass

    # Извличане на всички кораби от базата данни, за да ги покажем в таблицата
    cursor.execute('SELECT * FROM ships')
    all_ships = cursor.fetchall()
    conn.close()

    return render_template('ships.html', ships=all_ships)

@app.route('/permits', methods=['GET', 'POST'])
def permits():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # 1. Ако инспекторът изпрати формата за ново разрешително (POST)
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

    # 2. Взимаме всички кораби, за да напълним падащото меню във формата
    cursor.execute('SELECT id, intl_number, markings, owner_name FROM ships')
    all_ships = cursor.fetchall()

    # 3. Взимаме разрешителните, като ги свързваме (JOIN) с таблицата на корабите, за да знаем кой кораб кое разрешително има
    cursor.execute('''
        SELECT permits.id, permits.valid_to, permits.permit_number, permits.fishing_gear, permits.valid_from, ships.intl_number 
        FROM permits 
        JOIN ships ON permits.ship_id = ships.id
    ''')
    all_permits = cursor.fetchall()
    
    conn.close()

    return render_template('permits.html', ships=all_ships, permits=all_permits)

@app.route('/logbook')
def logbook():
    return render_template('logbook.html')

@app.route('/tickets')
def tickets():
    return render_template('tickets.html')

@app.route('/tickets/calculate', methods=['POST'])
def calculate_ticket():
    name = request.form.get('name')
    egn = request.form.get('egn')
    duration = request.form.get('duration')
    is_pensioner = request.form.get('is_pensioner')
    telk = request.form.get('telk')

    # Base rates
    prices = {"1_week": 4.00, "1_month": 8.00, "6_months": 15.00, "1_year": 25.00}
    final_price = prices.get(duration, 25.00)

    # Determine age using the EGN string structure
    try:
        year_part = int(egn[0:2])
        month_part = int(egn[2:4])
        
        # Adjust centuries based on standard Bulgarian civil registration tracking
        if month_part > 40:
            birth_year = 2000 + year_part
        else:
            birth_year = 1900 + year_part
        
        current_year = datetime.now().year
        age = current_year - birth_year
    except:
        age = 20  # Fallback age if EGN parse formatting breaks

    # Apply rule constraints matching TechnoLogica prompt
    if telk and len(telk.strip()) > 0:
        final_price = 0.00  # Free for disabled citizens
        age_group = "ТЕЛК Намаление"
    elif age < 14:
        final_price = final_price * 0.00  # Children catch for free or massive discount
        age_group = "Дете под 14 г."
    elif is_pensioner == 'yes' or age >= 65:
        final_price = final_price * 0.50  # 50% discount for seniors
        age_group = "Пенсионер"
    else:
        age_group = "Редовен"

    # Save details into SQLite backend records
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO hobby_tickets (fisherman_name, egn, age_group, telk_decision, price, issue_date)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (name, egn, age_group, telk, final_price, datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()

    return f"<h1>Успешно издаден билет!</h1><p>Риболовец: {name}</p><p>Категория: {age_group}</p><p>Крайна цена: {final_price:.2f} лв.</p><a href='/tickets'>Обратно</a>"

@app.route('/inspections')
def inspections():
    return render_template('inspections.html')

if __name__ == '__main__':
    app.run(debug=True)