from flask import Flask, render_template, request, redirect, url_for, send_file
import sqlite3
import csv
import os
from datetime import datetime

app = Flask(__name__)

DB_NAME = 'students.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            date TEXT,
            status TEXT,
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT * FROM students')
    students = c.fetchall()

    today = datetime.now().strftime('%Y-%m-%d')
    c.execute('SELECT student_id, status FROM attendance WHERE date = ?', (today,))
    attendance_today = {sid: status for sid, status in c.fetchall()}
    conn.close()
    return render_template('index.html', students=students, attendance_today=attendance_today, today=today)

@app.route('/add', methods=['POST'])
def add_student():
    name = request.form['name']
    email = request.form['email']
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO students (name, email) VALUES (?, ?)', (name, email))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    student_id = request.form['student_id']
    status = request.form['status']
    date = datetime.now().strftime('%Y-%m-%d')

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT * FROM attendance WHERE student_id = ? AND date = ?', (student_id, date))
    exists = c.fetchone()
    if exists:
        c.execute('UPDATE attendance SET status = ? WHERE student_id = ? AND date = ?', (status, student_id, date))
    else:
        c.execute('INSERT INTO attendance (student_id, date, status) VALUES (?, ?, ?)', (student_id, date, status))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/download')
def download_attendance():
    date = datetime.now().strftime('%Y-%m-%d')
    filename = f"attendance_{date}.csv"

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        SELECT s.name, s.email, a.date, a.status 
        FROM attendance a 
        JOIN students s ON a.student_id = s.id
        WHERE a.date = ?
    ''', (date,))
    rows = c.fetchall()
    conn.close()

    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Name', 'Email', 'Date', 'Status'])
        writer.writerows(rows)

    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
