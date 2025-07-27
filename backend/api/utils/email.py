# 📁 backend/api/utils/email.py

from flask_mail import Message
from backend.extensions import mail
from flask import current_app

def send_email(subject, recipients, body, html=None):
    try:
        print("📧 Připravuji e-mail k odeslání...")  # ✅ debug výpis

        msg = Message(
            subject=subject,
            recipients=recipients,
            body=body,
            html=html,
        )

        # ✅ důležitý sender – bez něj to často selže v tichosti
        msg.sender = current_app.config.get("MAIL_DEFAULT_SENDER")

        print(f"📨 Odesílám na {recipients}...")  # ✅ další výpis
        mail.send(msg)
        print("✅ E-mail byl úspěšně odeslán.")

    except Exception as e:
        print(f"❌ CHYBA při odesílání e-mailu: {e}")
