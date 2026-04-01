import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

def send_attendance_alert(to_email, student_name, percentage):
    if not EMAIL_USER or not EMAIL_PASS:
        print("Email credentials not set. Skipping email.")
        return

    subject = "Attendance Alert: Action Required"
    body = f"""
    Dear {student_name},

    Your attendance has fallen to {percentage:.2f}%, which is below the required 80%.
    Please ensure you attend your upcoming classes to avoid any academic penalties.

    Regards,
    Attendance Monitoring System
    """

    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
        server.quit()
        print(f"Alert sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")
