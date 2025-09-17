# smtp_test.py
import os, smtplib, ssl, traceback
from email.message import EmailMessage
from email.utils import formataddr

# volitelné: pokud máš python-dotenv, odkomentuj pro nahrání .env automaticky
try:
    from dotenv import load_dotenv
    load_dotenv()  # načte .env ze současného adresáře
except Exception:
    pass

MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.seznam.cz")
MAIL_PORT = int(os.getenv("MAIL_PORT", "465"))
MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "True").lower() == "true"
MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "False").lower() == "true"
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")

# kam poslat test — když necháš prázdné, pošle to sám sobě
TEST_EMAIL_TO = os.getenv("TEST_EMAIL_TO") or MAIL_USERNAME

if not (MAIL_USERNAME and MAIL_PASSWORD):
    print("❌ Chybí MAIL_USERNAME nebo MAIL_PASSWORD (zkontroluj .env).")
    raise SystemExit(1)

sender_header = MAIL_DEFAULT_SENDER or formataddr(("Náramková Móda", MAIL_USERNAME))

msg = EmailMessage()
msg["Subject"] = "SMTP test – Náramková Móda"
msg["From"] = sender_header           # ⚠️ u Seznamu MUSÍ odpovídat uživateli domény
msg["To"] = TEST_EMAIL_TO
msg.set_content("Ahoj, tohle je testovací e-mail ze skriptu (SMTP).")

print("=== Konfigurace ===")
print("SERVER:", MAIL_SERVER, "PORT:", MAIL_PORT,
      "SSL:", MAIL_USE_SSL, "TLS:", MAIL_USE_TLS)
print("FROM:", sender_header)
print("TO:", TEST_EMAIL_TO)
print("===================")

try:
    if MAIL_USE_SSL:
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(MAIL_SERVER, MAIL_PORT, context=ctx) as s:
            s.set_debuglevel(1)  # detailní SMTP log do konzole
            s.login(MAIL_USERNAME, MAIL_PASSWORD)
            s.send_message(msg)
    else:
        with smtplib.SMTP(MAIL_SERVER, MAIL_PORT) as s:
            s.set_debuglevel(1)
            s.ehlo()
            if MAIL_USE_TLS:
                s.starttls(context=ssl.create_default_context())
                s.ehlo()
            s.login(MAIL_USERNAME, MAIL_PASSWORD)
            s.send_message(msg)

    print("✅ Hotovo: e-mail byl odeslán.")
except Exception as e:
    print("❌ Chyba při odesílání:")
    traceback.print_exc()
    raise SystemExit(2)
