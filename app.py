# Simple Flask app to demonstrate FMEA with SQLite database
# Includes form page, dashboard, and reports page
# Uses Chart.js for charts and jsPDF for PDF export
# Run with: python app.py
# Access at: http://127.0.0.1:5000/

from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
import pandas as pd

app = Flask(__name__)

# Home page route
@app.route('/home')
def home():
    return render_template('home.html')

# Redirect root URL to /home
@app.route('/')
def root():
    return redirect(url_for('home'))

# Initialize database
def init_db():
    conn = sqlite3.connect('fmea.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS failure_modes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  step TEXT,
                  failure_mode TEXT,
                  cause TEXT,
                  control TEXT,
                  s INTEGER,
                  o INTEGER,
                  d INTEGER,
                  rpn INTEGER)''')
    conn.commit()
    conn.close()

# Retrieve all data
def get_all_data():
    conn = sqlite3.connect('fmea.db')
    c = conn.cursor()
    c.execute('SELECT id, step, failure_mode, cause, control, s, o, d, rpn FROM failure_modes ORDER BY rpn DESC')
    rows = c.fetchall()
    data = [{
        'id': row[0],
        'Step': row[1],
        'Failure Mode': row[2],
        'Cause': row[3],
        'Control': row[4],
        'S': row[5],
        'O': row[6],
        'D': row[7],
        'RPN': row[8]
    } for row in rows]
    conn.close()
    return data

# Get statistics
def get_stats(data):
    if not data:
        return {'average': 0, 'max': 0, 'min': 0, 'high_risk': 0}
    df = pd.DataFrame(data)
    avg_rpn = df['RPN'].mean()
    max_rpn = df['RPN'].max()
    min_rpn = df['RPN'].min()
    high_risk = len(df[df['RPN'] > 60])
    return {'average': round(avg_rpn, 2), 'max': max_rpn, 'min': min_rpn, 'high_risk': high_risk}

@app.route('/form', methods=['GET', 'POST'])
def form():
    error = None
    if request.method == 'POST':
        step = request.form.get('step')
        failure_mode = request.form.get('failure_mode')
        cause = request.form.get('cause')
        control = request.form.get('control')
        try:
            s = int(request.form.get('severity'))
            o = int(request.form.get('occurrence'))
            d = int(request.form.get('detection'))
        except (TypeError, ValueError):
            error = 'Severity, Occurrence, and Detection must be numbers between 1 and 10.'
            return render_template('form.html', error=error)

        if not all([step, failure_mode, cause, control, s, o, d]):
            error = 'All fields are required.'
            return render_template('form.html', error=error)
        if not (1 <= s <= 10 and 1 <= o <= 10 and 1 <= d <= 10):
            error = 'Values must be between 1 and 10.'
            return render_template('form.html', error=error)

        rpn = s * o * d
        conn = sqlite3.connect('fmea.db')
        c = conn.cursor()
        c.execute('INSERT INTO failure_modes (step, failure_mode, cause, control, s, o, d, rpn) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                  (step, failure_mode, cause, control, s, o, d, rpn))
        conn.commit()
        conn.close()
        return redirect(url_for('form'))
    return render_template('form.html', error=error)

@app.route('/dashboard')
def dashboard():
    data = get_all_data()
    stats = get_stats(data)
    top_5 = sorted(data, key=lambda x: x['RPN'], reverse=True)[:5]
    risk_dist = {'Low (0-30)': len([d for d in data if d['RPN'] <= 30]),
                 'Medium (31-60)': len([d for d in data if 31 <= d['RPN'] <= 60]),
                 'High (>60)': len([d for d in data if d['RPN'] > 60])}
    return render_template('dashboard.html', data=data, stats=stats, top_5=top_5, risk_dist=risk_dist)

@app.route('/reports')
def reports():
    data = get_all_data()
    stats = get_stats(data)
    return render_template('reports.html', data=data, stats=stats)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)