import os
import json
import urllib.request
import urllib.parse

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

def send_telegram_message(text: str) -> bool:
    """
    Pošle text do Telegramu (do chat_id). Vrací True/False podle úspěchu.
    Vyžaduje TELEGRAM_BOT_TOKEN a TELEGRAM_CHAT_ID v env.
    """
    token = BOT_TOKEN
    chat_id = CHAT_ID
    if not token or not chat_id:
        # chybí konfigurace → potichu selžem jako False
        return False

    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",  # můžeš použít <b>...</b> apod.
        "disable_web_page_preview": True,
    }
    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(api_url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            body = resp.read()
            obj = json.loads(body.decode("utf-8"))
            return bool(obj.get("ok"))
    except Exception:
        return False
