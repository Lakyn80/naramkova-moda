# backend/api/utils/email.py
from flask_mail import Message
from backend.extensions import mail
from email.header import Header  # ✅ kvůli emoji v Subjectu

def send_email(subject, recipients, body):
    # ✅ Subject s emoji/diakritikou správně zakódujeme
    msg = Message(
        subject=str(Header(subject or "", "utf-8")),
        recipients=recipients,
        body=body,
    )
    # ✅ pro jistotu vynutíme UTF-8
    msg.charset = "utf-8"
    mail.send(msg)
