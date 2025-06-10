from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to something secure

def init_db():
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        # Create bookings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room TEXT,
                name TEXT,
                date TEXT,
                start_time TEXT,
                end_time TEXT
            )
        ''')
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT
            )
        ''')
        # Insert faculty user if not exists
        cursor.execute("SELECT * FROM users WHERE username = ?", ('faculty1',))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                           ('faculty1', 'faculty123', 'faculty'))
        conn.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
            user = cursor.fetchone()

            if user:
                session['username'] = user[1]
                session['role'] = user[3]
                return redirect(url_for('index'))
            else:
                flash('Invalid credentials. Please try again.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/reserve', methods=['GET', 'POST'])
def reserve():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        room = request.form['room']
        name = request.form['name']
        date = request.form['date']
        start_time = request.form['start_time']
        end_time = request.form['end_time']

        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            # Check for conflicting booking
            cursor.execute("""
                SELECT * FROM bookings WHERE room=? AND date=? 
                AND ((start_time<? AND end_time>?) OR (start_time>=? AND start_time<?))
            """, (room, date, end_time, start_time, start_time, end_time))
            existing_booking = cursor.fetchone()

            if existing_booking:
                return "Room already booked for this time slot!"

            # Insert new booking
            cursor.execute("INSERT INTO bookings (room, name, date, start_time, end_time) VALUES (?, ?, ?, ?, ?)", 
                           (room, name, date, start_time, end_time))
            conn.commit()

        return redirect(url_for('view_bookings'))

    return render_template('reserve.html')

@app.route('/bookings')
def view_bookings():
    if 'username' not in session:
        return redirect(url_for('login'))

    with sqlite3.connect('database.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bookings")
        bookings = cursor.fetchall()

    return render_template('bookings.html', bookings=bookings)

@app.route('/delete/<int:booking_id>', methods=['POST'])
def delete_booking(booking_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM bookings WHERE id=?", (booking_id,))
        conn.commit()
    return redirect(url_for('view_bookings'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)