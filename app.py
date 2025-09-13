# Simple Flask app to demonstrate FMEA with SQLite database
# Includes form page, dashboard, and reports page
# Uses Chart.js for charts and jsPDF for PDF export
# Run with: python app.py
# Access at: http://127.0.0.1:5000/

from flask import Flask, render_template, request, jsonify
import sqlite3
import pandas as pd

app = Flask(__name__)

# Initialize database
def init_db():
    conn = sqlite3.connect('fmea.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS failure_modes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  failure_mode TEXT,
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
    c.execute('SELECT id, failure_mode, s, o, d, rpn FROM failure_modes ORDER BY rpn DESC')
    rows = c.fetchall()
    data = [{'id': row[0], 'Failure Mode': row[1], 'S': row[2], 'O': row[3], 'D': row[4], 'RPN': row[5]} for row in rows]
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

@app.route('/', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        name = request.form['failure_mode']
        s = int(request.form['severity'])
        o = int(request.form['occurrence'])
        d = int(request.form['detectability'])
        if not (1 <= s <= 10 and 1 <= o <= 10 and 1 <= d <= 10):
            return render_template('form.html', error='Values must be between 1 and 10')
        rpn = s * o * d
        conn = sqlite3.connect('fmea.db')
        c = conn.cursor()
        c.execute('INSERT INTO failure_modes (failure_mode, s, o, d, rpn) VALUES (?, ?, ?, ?, ?)',
                  (name, s, o, d, rpn))
        conn.commit()
        conn.close()
    return render_template('form.html')

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