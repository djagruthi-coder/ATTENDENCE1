import os
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_session import Session
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'smart_attendance_key_2026')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_TYPE'] = 'filesystem'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
Session(app)

# --- MODELS --- (UNCHANGED)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    login_id = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False) # admin, teacher, student

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    roll_no = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Timetable(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    day = db.Column(db.String(20), nullable=False)
    time_slot = db.Column(db.String(50), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)

    subject = db.relationship('Subject', backref='timetables')
    teacher = db.relationship('Teacher', backref='timetables')

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    timetable_id = db.Column(db.Integer, db.ForeignKey('timetable.id'), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(10), nullable=False)

# --- EMAIL LOGIC --- (UNCHANGED)
def send_alert(to_email, name, perc):
    user = os.environ.get('EMAIL_USER')
    password = os.environ.get('EMAIL_PASS')
    if not user or not password: return
    try:
        msg = MIMEMultipart()
        msg['From'] = user
        msg['To'] = to_email
        msg['Subject'] = "Low Attendance Warning"
        msg.attach(MIMEText(f"Hello {name},\n\nYour attendance is {perc:.1f}%, which is below 80%. Please attend classes.", 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(user, password)
            server.send_message(msg)
    except Exception as e:
        print(f"Mail Error: {e}")

# --- DECORATORS --- (UNCHANGED)
def auth_role(role):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user' not in session or session['user']['role'] != role:
                return jsonify({"error": "Unauthorized"}), 403
            return f(*args, **kwargs)
        return decorated
    return wrapper

# --- AUTH ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

# ✅ MODIFIED LOGIN ROUTE - Handles both admin & student logins with role hint
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    expected_role = data.get('role')  # Optional: 'admin' or 'student'
    
    user = User.query.filter_by(login_id=data['login_id']).first()
    
    if user and bcrypt.check_password_hash(user.password, data['password']):
        # Optional: Validate role matches the login box used
        if expected_role and user.role != expected_role:
            return jsonify({"success": False, "message": f"Please use the {user.role} login portal."}), 403
        
        session['user'] = {"id": user.id, "login_id": user.login_id, "role": user.role}
        return jsonify({"success": True, "role": user.role})
    
    return jsonify({"success": False, "message": "Invalid credentials"}), 401

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/admin_dashboard')
@auth_role('admin')
def admin_dashboard():
    return render_template('admin.html')

@app.route('/teacher_dashboard')
@auth_role('teacher')
def teacher_dashboard():
    return render_template('teacher.html')

@app.route('/student_dashboard')
@auth_role('student')
def student_dashboard():
    return render_template('student.html')

# --- ALL ADMIN/TEACHER/STUDENT APIs --- (UNCHANGED - Copy from your original code)
# [Keep all your existing API routes exactly as they were...]

# --- ADMIN APIs ---
@app.route('/api/admin/get_all_data', methods=['GET'])
@auth_role('admin')
def get_all_data():
    teachers = [{"id": t.id, "name": t.name, "email": t.email} for t in Teacher.query.all()]
    students = [{"id": s.id, "name": s.name, "roll_no": s.roll_no, "class_name": s.class_name} for s in Student.query.all()]
    subjects = [{"id": s.id, "name": s.name} for s in Subject.query.all()]
    timetable = []
    for t in Timetable.query.all():
        timetable.append({
            "id": t.id, "day": t.day, "time": t.time_slot, 
            "subject": t.subject.name, "teacher": t.teacher.name, "class": t.class_name
        })
    return jsonify({"teachers": teachers, "students": students, "subjects": subjects, "timetable": timetable})

@app.route('/api/admin/add_teacher', methods=['POST'])
@auth_role('admin')
def add_teacher():
    try:
        data = request.json
        hashed_pw = bcrypt.generate_password_hash(data.get('password', 'teacher123')).decode('utf-8')
        new_user = User(login_id=data['email'], password=hashed_pw, role='teacher')
        db.session.add(new_user)
        db.session.commit()
        
        new_teacher = Teacher(user_id=new_user.id, name=data['name'], email=data['email'])
        db.session.add(new_teacher)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/admin/add_student', methods=['POST'])
@auth_role('admin')
def add_student():
    try:
        data = request.json
        hashed_pw = bcrypt.generate_password_hash(data.get('password', 'student123')).decode('utf-8')
        new_user = User(login_id=data['roll_no'], password=hashed_pw, role='student')
        db.session.add(new_user)
        db.session.commit()
        
        new_student = Student(user_id=new_user.id, roll_no=data['roll_no'], name=data['name'], class_name=data['class_name'])
        db.session.add(new_student)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/admin/add_subject', methods=['POST'])
@auth_role('admin')
def add_subject():
    try:
        data = request.json
        new_sub = Subject(name=data['name'])
        db.session.add(new_sub)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/admin/add_timetable', methods=['POST'])
@auth_role('admin')
def add_timetable():
    try:
        data = request.json
        new_tt = Timetable(
            day=data['day'], time_slot=data['time_slot'],
            subject_id=data['subject_id'], teacher_id=data['teacher_id'], class_name=data['class_name']
        )
        db.session.add(new_tt)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)})

# --- TEACHER APIs ---
@app.route('/api/teacher/sessions', methods=['GET'])
@auth_role('teacher')
def teacher_sessions():
    user_id = session['user']['id']
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    sessions = Timetable.query.filter_by(teacher_id=teacher.id).all()
    return jsonify([{
        "id": s.id, "day": s.day, "time": s.time_slot, 
        "subject": s.subject.name, "class": s.class_name
    } for s in sessions])

@app.route('/api/teacher/students/<class_name>', methods=['GET'])
@auth_role('teacher')
def get_students(class_name):
    students = Student.query.filter_by(class_name=class_name).all()
    return jsonify([{"id": s.id, "roll_no": s.roll_no, "name": s.name} for s in students])

@app.route('/api/teacher/mark_attendance', methods=['POST'])
@auth_role('teacher')
def mark_attendance():
    try:
        data = request.json
        tt_id = data['timetable_id']
        records = data['records']
        date_str = datetime.datetime.now().strftime('%Y-%m-%d')
        
        tt = Timetable.query.get(tt_id)
        teacher_id = Teacher.query.filter_by(user_id=session['user']['id']).first().id

        for r in records:
            att = Attendance(
                student_id=r['student_id'], subject_id=tt.subject_id,
                teacher_id=teacher_id, timetable_id=tt_id,
                date=date_str, status=r['status']
            )
            db.session.add(att)
            
            # TRIGGER ALERT
            all_att = Attendance.query.filter_by(student_id=r['student_id'], subject_id=tt.subject_id).all()
            total = len(all_att)
            present = len([a for a in all_att if a.status == 'present'])
            if total > 5:
                perc = (present / total) * 100
                if perc < 80:
                    student = Student.query.get(r['student_id'])
                    send_alert(f"{student.roll_no}@college.com", student.name, perc)

        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/teacher/reports', methods=['GET'])
@auth_role('teacher')
def teacher_reports():
    try:
        user_id = session['user']['id']
        teacher = Teacher.query.filter_by(user_id=user_id).first()
        if not teacher:
            return jsonify({"error": "Teacher not found"}), 404
        
        assignments = Timetable.query.filter_by(teacher_id=teacher.id).all()
        report_data = []
        for ass in assignments:
            total_logs = Attendance.query.filter_by(
                subject_id=ass.subject_id, 
                teacher_id=teacher.id,
                timetable_id=ass.id
            ).all()
            
            if not total_logs:
                report_data.append({
                    "subject": ass.subject.name,
                    "class": ass.class_name,
                    "percentage": 0,
                    "total": 0
                })
                continue
                
            total_count = len(total_logs)
            present_count = len([l for l in total_logs if l.status == 'present'])
            perc = (present_count / total_count) * 100
            
            report_data.append({
                "subject": ass.subject.name,
                "class": ass.class_name,
                "percentage": round(perc, 1),
                "total": total_count
            })
        return jsonify(report_data)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# --- STUDENT APIs ---
@app.route('/api/student/report', methods=['GET'])
@auth_role('student')
def student_report():
    user_id = session['user']['id']
    student = Student.query.filter_by(user_id=user_id).first()
    
    subjects = Subject.query.all()
    report = []
    for s in subjects:
        logs = Attendance.query.filter_by(student_id=student.id, subject_id=s.id).all()
        if not logs: continue
        total = len(logs)
        present = len([l for l in logs if l.status == 'present'])
        report.append({
            "subject": s.name,
            "total": total,
            "present": present,
            "perc": (present/total)*100
        })
    
    history = Attendance.query.filter_by(student_id=student.id).order_by(Attendance.id.desc()).limit(10).all()
    hist_data = [{"date": h.date, "subject": Subject.query.get(h.subject_id).name, "status": h.status} for h in history]
    
    return jsonify({"report": report, "history": hist_data})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(login_id='admin').first():
            pw = bcrypt.generate_password_hash('admin123').decode('utf-8')
            adm = User(login_id='admin', password=pw, role='admin')
            db.session.add(adm)
            db.session.commit()
    app.run(debug=True)
