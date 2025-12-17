from flask_mail import Message
from backend.extensions import mail


def send_email(subject, recipients, body, attachments=None, sender=None):
    """
    Odeslání textového e-mailu v UTF-8 s volitelnými přílohami.
    Flask-Mail si MIME + charset sestaví správně sám.
    """
    if isinstance(recipients, str):
        recipients = [recipients]

    msg = Message(
        subject=subject or "",
        recipients=list(recipients or []),
        body=body or "",
        sender=sender,
    )

    # 🔑 DŮLEŽITÉ: jen toto – žádné Header(), žádné extra_headers
    msg.charset = "utf-8"

    for att in attachments or []:
        if not isinstance(att, dict):
            continue
        filename = att.get("filename") or "attachment"
        data = att.get("content", att.get("data"))
        mimetype = att.get("mimetype") or att.get("content_type") or "application/octet-stream"
        if data is None:
            continue
        msg.attach(
            filename=filename,
            content_type=mimetype,
            data=data,
        )

    mail.send(msg)
    return msg
