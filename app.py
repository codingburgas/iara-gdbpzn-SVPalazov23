import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for
from models import init_db, DATABASE_PATH

app = Flask(__name__)
init_db()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/ships')
def ships():
    return render_template('ships.html')

@app.route('/permits')
def permits():
    return render_template('permits.html')

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