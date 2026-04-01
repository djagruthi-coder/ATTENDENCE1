from flask import Flask, request, jsonify, render_template, session
import os
from utils.db_manager import query_db, execute_db, init_db, get_db_connection
from utils.email_service import send_attendance_alert
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Initialize DB
init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/teacher_dashboard')
def teacher_dashboard():
    return render_template('teacher_dashboard.html')

@app.route('/student_dashboard')
def student_dashboard():
    return render_template('student_dashboard.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    roll_no = data.get('roll_no')
    dob = data.get('dob')
    
    user = query_db("SELECT * FROM students WHERE roll_no = ? AND dob = ?", [roll_no, dob], one=True)
    if user:
        user_dict = dict(user)
        session['user'] = user_dict
        return jsonify({"success": True, "user": user_dict})
    return jsonify({"success": False, "message": "Invalid Roll No or DOB"}), 401

@app.route('/api/get_classes', methods=['GET'])
def get_classes():
    classes = query_db("SELECT * FROM classes")
    return jsonify([dict(c) for c in classes])

@app.route('/api/add_class', methods=['POST'])
def add_class():
    data = request.json
    branch = data.get('branch')
    section = data.get('section')
    try:
        execute_db("INSERT INTO classes (branch, section) VALUES (?, ?)", [branch, section])
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400

@app.route('/api/add_student', methods=['POST'])
def add_student():
    data = request.json
    roll_no = data.get('roll_no')
    name = data.get('name')
    dob = data.get('dob')
    branch = data.get('branch')
    section = data.get('section')
    email = data.get('email')
    
    try:
        execute_db("INSERT INTO students (roll_no, name, dob, branch, section, email) VALUES (?, ?, ?, ?, ?, ?)",
                   [roll_no, name, dob, branch, section, email])
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400

@app.route('/api/students', methods=['POST'])
def get_students():
    data = request.json
    branch = data.get('branch')
    section = data.get('section')
    students = query_db("SELECT * FROM students WHERE branch = ? AND section = ?", [branch, section])
    return jsonify([dict(s) for s in students])

@app.route('/api/bulk_attendance_subject', methods=['POST'])
def bulk_attendance():
    data = request.json
    subject = data.get('subject')
    date = data.get('date') or datetime.now().strftime('%Y-%m-%d')
    attendance_list = data.get('attendance') # List of {roll_no, present: bool}
    
    conn = get_db_connection()
    try:
        for entry in attendance_list:
            roll_no = entry['roll_no']
            present = entry['present']
            
            # Log the attendance
            conn.execute("INSERT INTO attendance_log (roll_no, subject, date, present) VALUES (?, ?, ?, ?)",
                         [roll_no, subject, date, present])
            
            # Update aggregate table
            # Check if record exists
            row = conn.execute("SELECT * FROM attendance WHERE roll_no = ? AND subject = ?", [roll_no, subject]).fetchone()
            if row:
                attended = row['attended'] + (1 if present else 0)
                total = row['total'] + 1
                conn.execute("UPDATE attendance SET attended = ?, total = ? WHERE roll_no = ? AND subject = ?",
                             [attended, total, roll_no, subject])
            else:
                attended = 1 if present else 0
                total = 1
                conn.execute("INSERT INTO attendance (roll_no, subject, attended, total) VALUES (?, ?, ?, ?)",
                             [roll_no, subject, attended, total])
            
            # Email Alert logic (if < 80%)
            # Fetch latest data for calculation
            row = conn.execute("SELECT * FROM attendance WHERE roll_no = ? AND subject = ?", [roll_no, subject]).fetchone()
            percentage = (row['attended'] / row['total']) * 100
            if percentage < 80:
                student = conn.execute("SELECT * FROM students WHERE roll_no = ?", [roll_no]).fetchone()
                if student and student['email']:
                    send_attendance_alert(student['email'], student['name'], percentage)
                    
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/get_attendance', methods=['POST'])
def get_attendance():
    data = request.json
    roll_no = data.get('roll_no')
    attendance = query_db("SELECT * FROM attendance WHERE roll_no = ?", [roll_no])
    return jsonify([dict(a) for a in attendance])

@app.route('/api/get_attendance_log', methods=['POST'])
def get_attendance_log():
    data = request.json
    roll_no = data.get('roll_no')
    logs = query_db("SELECT * FROM attendance_log WHERE roll_no = ? ORDER BY date DESC", [roll_no])
    return jsonify([dict(l) for l in logs])

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
