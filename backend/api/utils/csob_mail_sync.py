# backend/api/utils/csob_mail_sync.py
import os
import imaplib
import email
import re
import html as _html
from decimal import Decimal
from typing import List, Tuple, Iterable, Optional

# ---- Regexy ---------------------------------------------------------------

# VS: "VS" nebo "Variabilní symbol", 1–10 číslic
VS_RE  = re.compile(r'(?:VS|Variabiln[íi]\s*symbol)\s*[:\-]?\s*(\d{1,10})', re.I)

# Částka: povol +/-, mezery jako tisícovky, čárka/tečka jako desetinná
AMT_RE = re.compile(r'(?:Částka|Castka)\s*[:\-]?\s*([+\-]?[\d\s]+[,.]\d{2})\s*(?:CZK|Kč)?', re.I)

# Některé varianty předmětů od banky – jen orientační
SUBJECT_HINTS = (
    "příchozí platba", "prichozi platba",
    "připsání částky", "pripsani castky",
    "příchozí úhrada", "prichozi uhrada",
    "avízo", "avizo",
)

# ---- Pomocné parsování ----------------------------------------------------

def _parse_amount(text: str) -> Optional[Decimal]:
    m = AMT_RE.search(text or "")
    if not m:
        return None
    num = (m.group(1) or "").replace(" ", "").replace("\xa0", "").replace(",", ".")
    try:
        return Decimal(num)
    except Exception:
        return None

def _parse_vs(text: str) -> Optional[str]:
    m = VS_RE.search(text or "")
    return m.group(1) if m else None

def _sender_matches(addr: str, allow: Iterable[str]) -> bool:
    if not addr:
        return False
    addr_low = addr.lower()
    for pat in (allow or []):
        if pat.lower() in addr_low:
            return True
    return False

def _msg_to_text(msg: email.message.Message) -> str:
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = (part.get_content_type() or "").lower()
            if ctype.startswith("text/plain"):
                try:
                    body += part.get_payload(decode=True).decode(
                        part.get_content_charset() or "utf-8",
                        errors="ignore",
                    )
                except Exception:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True).decode(
                msg.get_content_charset() or "utf-8",
                errors="ignore",
            )
        except Exception:
            body = ""
    return body

def _msg_to_html(msg: email.message.Message) -> str:
    html = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = (part.get_content_type() or "").lower()
            if ctype.startswith("text/html"):
                try:
                    html += part.get_payload(decode=True).decode(
                        part.get_content_charset() or "utf-8",
                        errors="ignore",
                    )
                except Exception:
                    pass
    else:
        if (msg.get_content_type() or "").lower().startswith("text/html"):
            try:
                html = msg.get_payload(decode=True).decode(
                    msg.get_content_charset() or "utf-8",
                    errors="ignore",
                )
            except Exception:
                html = ""
    return html

def _extract_from_csob_html(html: str) -> Tuple[Optional[str], Optional[Decimal]]:
    """
    HTML layout ČSOB (tabulka):
      <td>Variabilní symbol</td><td>706536</td>
      <td>Částka</td><td>+1,00 CZK</td>
    Vrací (vs, amount) nebo (None, None).
    """
    h = html or ""
    # pryč <script>/<style>
    h = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", h)
    h = _html.unescape(h)
    h = re.sub(r"[ \t\u00A0]+", " ", h)

    # VS je v následujícím <td>
    m_vs = re.search(
        r"(?is)>\s*Variabiln[íi]\s*symbol\s*<\s*/\s*td\s*>\s*<\s*td[^>]*>\s*(\d{1,10})\s*<\s*/\s*td\s*>",
        h,
    )
    vs = m_vs.group(1) if m_vs else None

    # Částka v dalším <td>
    m_amt = re.search(
        r"(?is)>\s*(?:Částka|Castka)\s*<\s*/\s*td\s*>\s*<\s*td[^>]*>\s*([+\-]?\d[\d\s]*[.,]\d{2})\s*(?:CZK|Kč)?\s*<\s*/\s*td\s*>",
        h,
    )
    amount = None
    if m_amt:
        num = m_amt.group(1).replace(" ", "").replace(",", ".")
        try:
            amount = Decimal(num)
        except Exception:
            amount = None

    return vs, amount

# ---- IMAP fetchery --------------------------------------------------------

def fetch_from_imap(
    *,
    host: str,
    port: int,
    ssl: bool,
    user: str,
    password: str,
    folder: str = "INBOX",
    max_items: int = 50,
    allow_senders: Optional[Iterable[str]] = None,
    mark_seen: bool = True,
) -> List[Tuple[str, Decimal, str]]:
    """
    Nízká vrstva: stáhne poslední zprávy z IMAP a zkusí z nich vytěžit (vs, amount).
    Filtruje podle allow_senders (substring match v hlavičce From/Sender).
    Vrací list trojic: (vs, amount, sender_header).
    """
    imap = imaplib.IMAP4_SSL(host, port) if ssl else imaplib.IMAP4(host, port)
    imap.login(user, password)
    imap.select(folder)

    # 🔒 Bereme pouze UNSEEN (jen nové bankovní e-maily). Bez fallbacku na ALL!
    typ, data = imap.search(None, "(UNSEEN)")
    ids = data[0].split()
    if not ids:
        imap.close()
        imap.logout()
        return []

    out: List[Tuple[str, Decimal, str]] = []

    for msg_id in reversed(ids):
        if len(out) >= max_items:
            break

        typ, data = imap.fetch(msg_id, "(RFC822)")
        if typ != "OK":
            continue

        raw = data[0][1]
        msg = email.message_from_bytes(raw)
        sender_hdr = ((msg.get("From") or "") + " " + (msg.get("Sender") or "")).strip()
        subject = (msg.get("Subject") or "")

        # Sender filtr
        if allow_senders and not _sender_matches(sender_hdr, allow_senders):
            continue

        # Parsování – nejdřív HTML tabulka, pak fallback na text
        html_text = _msg_to_html(msg)
        body_text = _msg_to_text(msg)

        vs, amt = (None, None)
        if html_text:
            vs, amt = _extract_from_csob_html(html_text)
        if not vs:
            vs = _parse_vs(body_text) or _parse_vs(subject)
        if amt is None:
            amt = _parse_amount(body_text)

        if vs and amt is not None:
            out.append((vs, amt, sender_hdr))
            if mark_seen:
                try:
                    imap.store(msg_id, "+FLAGS", r"\Seen")
                except Exception:
                    pass

    imap.close()
    imap.logout()
    return out

def fetch_csob_incoming(
    host: Optional[str] = None,
    port: Optional[int] = None,
    ssl: Optional[bool] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
    folder: Optional[str] = None,
    max_items: int = 50,
    bank_senders: Optional[Iterable[str]] = None,
    self_senders: Optional[Iterable[str]] = None,
    mark_seen: bool = True,
) -> List[Tuple[str, Decimal]]:
    """
    Vyšší vrstva – stáhne a vrátí pouze bankovní shody [(vs, amount)].
    Odesílatele:
      - bank_senders: whitelist ČSOB variant
      - self_senders: vlastní maily (NEpoužíváme pro párování, jen diagnostika jinde)
    Parametry se berou prioritně z argumentů, pak z .env:
      IMAP_HOST, IMAP_PORT, IMAP_SSL, IMAP_USER, IMAP_PASSWORD, IMAP_FOLDER
    """
    host = host or os.getenv("IMAP_HOST", "imap.seznam.cz")
    port = int(port or os.getenv("IMAP_PORT", "993"))
    ssl = (ssl if ssl is not None else os.getenv("IMAP_SSL", "true").lower() == "true")
    user = user or os.getenv("IMAP_USER")
    password = password or os.getenv("IMAP_PASSWORD")
    folder = folder or os.getenv("IMAP_FOLDER", "INBOX")

    if not (user and password):
        raise RuntimeError("Chybí IMAP_USER/IMAP_PASSWORD v .env nebo parametrech.")

    bank_senders = list(bank_senders) if bank_senders else [
        "csob.cz", "noreply@csob.cz", "no-reply@csob.cz", "notification@csob.cz", "info@csob.cz"
    ]
    # self_senders tady neřešíme (nepárujeme podle nich)

    rows = fetch_from_imap(
        host=host, port=port, ssl=ssl, user=user, password=password, folder=folder,
        max_items=max_items, allow_senders=bank_senders, mark_seen=mark_seen,
    )
    return [(vs, amt) for (vs, amt, _sender) in rows]

# ============================================================================
# Napojení na DB + odeslání FA + Telegram
# ============================================================================

from backend.extensions import db
from backend.admin.models import Payment, Order
from backend.admin.sold_routes import send_invoice_for_order
from backend.api.utils.telegram import send_telegram_message  # tvůj helper „přes skript“

def _fmt_amount(a: Optional[Decimal]) -> str:
    if a is None:
        return "—"
    try:
        return f"{float(a):.2f} Kč"
    except Exception:
        return f"{a} Kč"

def apply_bank_confirmations_to_db(mark_seen: bool = True) -> dict:
    """
    1) Stáhne potvrzení z banky (VS, částka) – pouze UNSEEN e-maily.
    2) U Payment (VS) nastaví status=received (+ received_at pokud chybí).
    3) U Order (VS) nastaví status=paid.
    4) Po COMMITU: pošle FA a Telegram **jen když došlo ke změně**.
    """
    pairs = fetch_csob_incoming(mark_seen=mark_seen)  # [(vs, amount)]
    results = {
        "checked": len(pairs),
        "updated_payments": 0,
        "updated_orders": 0,
        "emailed_invoices": 0,
        "telegram_ok": 0,
        "items": [],
    }

    for vs, amount in pairs:
        item = {
            "vs": vs, "amount": str(amount),
            "payment_id": None, "order_id": None,
            "payment_updated": False, "order_updated": False,
            "invoice_sent": False, "telegram_sent": False
        }

        # 1) Payment podle VS
        p = db.session.query(Payment).filter_by(vs=vs).order_by(Payment.id.desc()).first()
        if p:
            item["payment_id"] = p.id
            changed_p = False
            if p.status != "received":
                p.status = "received"
                changed_p = True
            if getattr(p, "received_at", None) is None:
                try:
                    from datetime import datetime as _dt
                    p.received_at = _dt.utcnow()
                    changed_p = True
                except Exception:
                    pass
            if changed_p:
                item["payment_updated"] = True
                results["updated_payments"] += 1

        # 2) Order podle VS
        o = db.session.query(Order).filter_by(vs=vs).first()
        if o:
            item["order_id"] = o.id
            if o.status != "paid":
                o.status = "paid"
                item["order_updated"] = True
                results["updated_orders"] += 1

        # 3) Commit změn (pokud byly)
        changed = bool(item["payment_updated"] or item["order_updated"])
        if changed:
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()

        # 4) Odeslat FA jen při změně a pokud existuje order
        if changed and o:
            try:
                send_res = send_invoice_for_order(o.id)
                if send_res.get("ok") and send_res.get("emailed"):
                    item["invoice_sent"] = True
                    results["emailed_invoices"] += 1
            except Exception:
                pass

        # 5) Telegram jen při změně
        if changed:
            try:
                ok = send_telegram_message(
                    f"✅ Potvrzena příchozí platba\nVS: {vs}\nČástka: {_fmt_amount(amount)}"
                    + (f"\nObjednávka: #{o.id}" if o else "\nObjednávka: nenalezena")
                )
                if ok:
                    item["telegram_sent"] = True
                    results["telegram_ok"] += 1
            except Exception:
                pass

        results["items"].append(item)

    return results

# Pohodlný alias pro cron/CLI
def csob_sync(mark_seen: bool = True) -> dict:
    """Využij pro periodický běh (cron). Vrací souhrn."""
    return apply_bank_confirmations_to_db(mark_seen=mark_seen)

if __name__ == "__main__":
    # Jednoduchý test běhu (např. python -m backend.api.utils.csob_mail_sync)
    out = csob_sync(mark_seen=True)
    print(out)
