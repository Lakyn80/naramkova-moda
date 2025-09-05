# backend/auth/password_reset_routes.py
from flask import render_template, request, redirect, url_for, flash, current_app
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask_mail import Message

from backend.extensions import db, mail, bcrypt
from backend.auth.login_routes import auth_bp  # používáme stejný blueprint jako login

# ── Helpers ──────────────────────────────────────────────────────────────────

def _get_serializer() -> URLSafeTimedSerializer:
    secret = current_app.config.get("SECRET_KEY")
    if not secret:
        raise RuntimeError("SECRET_KEY není nastaven – bez něj nelze generovat reset tokeny.")
    salt = current_app.config.get("PASSWORD_RESET_SALT", "nm-password-reset")
    return URLSafeTimedSerializer(secret_key=secret, salt=salt)

def _gen_token(user_id: int | str) -> str:
    s = _get_serializer()
    return s.dumps({"uid": str(user_id)})

def _load_token(token: str, max_age_seconds: int = 3600) -> str:
    s = _get_serializer()
    data = s.loads(token, max_age=max_age_seconds)
    return data.get("uid")

# [CHANGE] – jednotné určení odesílatele
def _mail_sender() -> str | None:
    """
    Vrátí adresu odesílatele pro Flask-Mail.
    Preferujeme MAIL_DEFAULT_SENDER; pokud není, použijeme MAIL_USERNAME.
    """
    sender = current_app.config.get("MAIL_DEFAULT_SENDER")
    if not sender:
        sender = current_app.config.get("MAIL_USERNAME")
    return sender

# ── Diagnostika ──────────────────────────────────────────────────────────────

@auth_bp.get("/__mail_cfg")
def __mail_cfg():
    """Vrátí runtime mail konfiguraci (bez hesla)."""
    cfg = current_app.config
    safe = {
        "MAIL_SERVER": cfg.get("MAIL_SERVER"),
        "MAIL_PORT": cfg.get("MAIL_PORT"),
        "MAIL_USE_SSL": cfg.get("MAIL_USE_SSL"),
        "MAIL_USE_TLS": cfg.get("MAIL_USE_TLS"),
        "MAIL_USERNAME": cfg.get("MAIL_USERNAME"),
        "MAIL_DEFAULT_SENDER": cfg.get("MAIL_DEFAULT_SENDER"),
        "MAIL_SUPPRESS_SEND": cfg.get("MAIL_SUPPRESS_SEND"),
        "MAIL_DEBUG": cfg.get("MAIL_DEBUG"),
    }
    return safe, 200

@auth_bp.get("/__mail_ping")
def __mail_ping():
    """Pošle krátký test e-mail na MAIL_USERNAME přes Flask-Mail (stejná cesta jako reset)."""
    to = current_app.config.get("MAIL_USERNAME")
    if not to:
        return {"ok": False, "err": "MAIL_USERNAME není nastavené"}, 500

    subj = "Mail ping (Flask-Mail)"
    body = "OK z Flasku (Flask-Mail)."

    try:
        # [CHANGE] – přidán explicitní sender
        msg = Message(recipients=[to], subject=subj, body=body, sender=_mail_sender())

        current_app.logger.info("[MAIL_PING] trying to send to %r", to)
        print("[MAIL_PING] to:", to)
        with mail.connect() as conn:
            try:
                if current_app.debug or current_app.config.get("MAIL_DEBUG", False):
                    conn.host.set_debuglevel(1)
                    current_app.logger.info("[MAIL_PING] SMTP debuglevel=1")
                    print("[MAIL_PING] SMTP debuglevel=1")
            except Exception:
                current_app.logger.exception("[MAIL_PING] set_debuglevel failed (ignored)")
            conn.send(msg)
        current_app.logger.info("[MAIL_PING] sent OK")
        print("[MAIL_PING] sent OK")
        return {"ok": True}, 200
    except Exception as e:
        current_app.logger.exception("[MAIL_PING] ERROR sending: %s", e)
        print("[MAIL_PING] ERROR:", e)
        return {"ok": False, "err": str(e)}, 500

# ── Zapomenuté heslo ────────────────────────────────────────────────────────

@auth_bp.get("/forgot")
def forgot_password_form():
    return render_template("admin/auth/forgot.html")

@auth_bp.post("/forgot")
def forgot_password_submit():
    """Odešle reset e-mail (pokud je příjemce známý) nebo vrátí link ve flashi."""
    from backend.models.user import User

    identifier = (request.form.get("email") or "").strip()
    current_app.logger.info("[FORGOT] identifier=%r", identifier)
    print("[FORGOT] identifier:", identifier)

    if not identifier:
        flash("Vyplň e-mail nebo uživatelské jméno.", "warning")
        return redirect(url_for("auth.forgot_password_form"))

    # Najdi uživatele (email → username)
    q = db.session.query(User)
    user = None
    if hasattr(User, "email"):
        user = q.filter_by(email=identifier).first()
        current_app.logger.info("[FORGOT] lookup by email -> %r", getattr(user, "id", None))
        print("[FORGOT] lookup by email ->", getattr(user, "id", None))
    if not user and hasattr(User, "username"):
        user = q.filter_by(username=identifier).first()
        current_app.logger.info("[FORGOT] lookup by username -> %r", getattr(user, "id", None))
        print("[FORGOT] lookup by username ->", getattr(user, "id", None))

    # Bezpečnostně neprozrazujeme existenci účtu
    if not user:
        current_app.logger.info("[FORGOT] user NOT FOUND -> generic flash, no send")
        print("[FORGOT] user NOT FOUND")
        flash("Pokud účet existuje, poslal jsem ti e-mail s odkazem.", "info keep")
        return redirect(url_for("auth.forgot_password_form"))

    token = _gen_token(user.id)
    reset_url = url_for("auth.reset_password_form", token=token, _external=True)
    current_app.logger.info("[FORGOT] token generated for uid=%s", user.id)
    print("[FORGOT] token generated for uid=", user.id)
    current_app.logger.info("[FORGOT] reset_url=%s", reset_url)
    print("[FORGOT] reset_url:", reset_url)

    # Recipient: preferuj user.email; pokud není a identifier vypadá jako e-mail, použij jej
    recipient = getattr(user, "email", None)
    if not recipient and "@" in identifier and "." in identifier and " " not in identifier:
        recipient = identifier
    current_app.logger.info("[FORGOT] recipient=%r", recipient)
    print("[FORGOT] recipient:", recipient)

    subj = current_app.config.get("PASSWORD_RESET_SUBJECT", "Obnova hesla – Náramková Móda")

    if not recipient:
        current_app.logger.info("[FORGOT] no recipient -> show link in flash")
        print("[FORGOT] no recipient -> show link in flash")
        flash("Účet nemá nastavený e-mail. Použij tento odkaz:", "warning keep")
        flash(reset_url, "secondary keep")
        return redirect(url_for("auth.forgot_password_form"))

    if current_app.config.get("MAIL_SUPPRESS_SEND", False):
        current_app.logger.warning("[FORGOT] MAIL_SUPPRESS_SEND=True -> not sending, show link")
        print("[FORGOT] MAIL_SUPPRESS_SEND=True -> not sending")
        flash("Odesílání e-mailů je vypnuto. Tady je odkaz:", "warning keep")
        flash(reset_url, "secondary keep")
        return redirect(url_for("auth.forgot_password_form"))

    body = (
        f"Ahoj {getattr(user, 'username', '') or 'uživateli'},\n\n"
        "přišla žádost o obnovení hesla do administrace. Pokud jsi to byl ty, klikni na odkaz:\n\n"
        f"{reset_url}\n\n"
        "Odkaz platí 60 minut. Pokud jsi nic nepožadoval, tento e-mail ignoruj.\n"
    )

    try:
        # [CHANGE] – přidán explicitní sender
        msg = Message(recipients=[recipient], subject=subj, body=body, sender=_mail_sender())
        current_app.logger.info("[FORGOT] sending to=%r subj=%r sender=%r", recipient, subj, _mail_sender())
        print("[FORGOT] sending to:", recipient)

        with mail.connect() as conn:
            try:
                if current_app.debug or current_app.config.get("MAIL_DEBUG", False):
                    conn.host.set_debuglevel(1)  # kompletní SMTP dialog do konzole
                    current_app.logger.info("[FORGOT] SMTP debuglevel=1")
                    print("[FORGOT] SMTP debuglevel=1")
            except Exception:
                current_app.logger.exception("[FORGOT] set_debuglevel failed (ignored)")
            conn.send(msg)

        flash("Pokud účet existuje, poslal jsem ti e-mail s odkazem.", "info keep")
        current_app.logger.info("[FORGOT] mail sent OK")
        print("[FORGOT] mail sent OK")
    except Exception as e:
        current_app.logger.exception("[FORGOT] ERROR sending mail: %s", e)
        print("[FORGOT] ERROR:", e)
        flash(f"Nepodařilo se odeslat e-mail: {e}", "danger keep")
        flash(reset_url, "secondary keep")

    return redirect(url_for("auth.forgot_password_form"))

@auth_bp.get("/reset/<token>")
def reset_password_form(token: str):
    try:
        _load_token(token, max_age_seconds=3600)
    except (BadSignature, SignatureExpired):
        flash("Odkaz je neplatný nebo mu vypršela platnost.", "danger")
        return redirect(url_for("auth.forgot_password_form"))

    return render_template("admin/auth/reset.html", token=token)

@auth_bp.post("/reset/<token>")
def reset_password_submit(token: str):
    from backend.models.user import User

    new_pwd = (request.form.get("password") or "").strip()
    new_pwd2 = (request.form.get("password2") or "").strip()

    if not new_pwd or len(new_pwd) < 6:
        flash("Heslo musí mít alespoň 6 znaků.", "warning")
        return redirect(url_for("auth.reset_password_form", token=token))
    if new_pwd != new_pwd2:
        flash("Hesla se neshodují.", "warning")
        return redirect(url_for("auth.reset_password_form", token=token))

    try:
        uid = _load_token(token, max_age_seconds=3600)
    except SignatureExpired:
        flash("Odkaz vypršel (60 minut). Požádej znovu o obnovení hesla.", "danger")
        return redirect(url_for("auth.forgot_password_form"))
    except BadSignature:
        flash("Odkaz je neplatný.", "danger")
        return redirect(url_for("auth.forgot_password_form"))

    user = db.session.get(User, uid)
    if not user:
        flash("Uživatel nebyl nalezen.", "danger")
        return redirect(url_for("auth.forgot_password_form"))

    hashed = bcrypt.generate_password_hash(new_pwd).decode("utf-8")
    if hasattr(user, "password_hash"):
        user.password_hash = hashed
    elif hasattr(user, "password"):
        user.password = hashed
    else:
        flash("Model uživatele nemá 'password' ani 'password_hash'.", "danger")
        return redirect(url_for("auth.forgot_password_form"))

    db.session.commit()
    flash("Heslo změněno. Můžeš se přihlásit.", "success")
    return redirect(url_for("auth.login"))  # ✅ Tento soubor obsluhuje přihlášení/odhlášení
