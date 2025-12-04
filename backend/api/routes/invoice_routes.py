import io
from datetime import datetime
from decimal import Decimal

from flask import Blueprint, request, redirect, flash, send_file
from flask_login import login_required
from flask_mail import Message

from backend.extensions import mail
from backend.models import SoldProduct
from backend.invoicing import build_invoice_pdf_bytes

invoice_bp = Blueprint("invoice_bp", __name__, url_prefix="/api/invoice")

# ---------- Helpers ----------------------------------------------------------

def _parse_price_decimal(val) -> Decimal:
    if val is None:
        return Decimal("0")
    if isinstance(val, (int, float, Decimal)):
        return Decimal(str(val))
    s = "".join(ch for ch in str(val) if ch.isdigit() or ch in (".", ","))
    if s.count(",") == 1 and s.count(".") == 0:
        s = s.replace(",", ".")
    else:
        s = s.replace(",", "")
    try:
        return Decimal(s)
    except Exception:
        return Decimal("0")

def _sold_proxy_for_invoice(sold: SoldProduct):
    unit_price = _parse_price_decimal(getattr(sold, "price", 0))
    qty = int(getattr(sold, "quantity", 1) or 1)
    items = [{
        "name": sold.name or "",
        "quantity": qty,
        "price_czk": float(unit_price),
    }]
    total = unit_price * qty

    class _O: pass
    o = _O()
    o.id = sold.id
    o.customer_name = sold.customer_name or ""
    o.customer_email = sold.customer_email or ""
    o.customer_address = sold.customer_address or ""
    o.note = sold.note or ""
    o.total_czk = float(total)
    o.items = items
    o.created_at = getattr(sold, "sold_at", None)
    return o

def _sold_payment_for_invoice(sold: SoldProduct):
    class _P: pass
    p = _P()
    p.id = sold.id
    p.vs = f"SOLD-{sold.id:06d}"
    p.amount_czk = _parse_price_decimal(getattr(sold, "price", 0)) * int(getattr(sold, "quantity", 1) or 1)
    p.received_at = getattr(sold, "sold_at", None) or datetime.utcnow()
    p.status = "sold"
    p.payment_type = getattr(sold, "payment_type", "Prodej")
    return p

# ---------- API: SOLD PRODUCT faktura ---------------------------------------

@invoice_bp.get("/sold/<int:sold_id>.pdf", endpoint="sold_invoice_pdf_api")
# # @login_required  # dočasně vypnuto
def sold_invoice_pdf_api(sold_id: int):
    """NĂˇhled PDF faktury pro SoldProduct (inline)."""
    sold = SoldProduct.query.get_or_404(sold_id)
    o = _sold_proxy_for_invoice(sold)
    p = _sold_payment_for_invoice(sold)

    pdf_bytes, inv_no = build_invoice_pdf_bytes(o, p, seller=None)
    buf = io.BytesIO(pdf_bytes); buf.seek(0)
    return send_file(
        buf,
        mimetype="application/pdf",
        as_attachment=False,
        download_name=f"{inv_no}.pdf",
        max_age=0,
        etag=False,
        last_modified=None,
    )

@invoice_bp.post("/sold/<int:sold_id>/send", endpoint="sold_invoice_send_api")
# # @login_required  # dočasně vypnuto
def sold_invoice_send_api(sold_id: int):
    """PoĹˇle fakturu e-mailem (PDF v pĹ™Ă­loze) a vrĂˇtĂ­ redirect zpÄ›t do adminu."""
    sold = SoldProduct.query.get_or_404(sold_id)
    recipient = (request.form.get("email") or sold.customer_email or "").strip()
    if not recipient:
        flash("âťŚ ZĂˇkaznickĂ˝ e-mail nenĂ­ vyplnÄ›n.", "danger")
        return redirect("/admin/sold")

    o = _sold_proxy_for_invoice(sold)
    p = _sold_payment_for_invoice(sold)

    pdf_bytes, inv_no = build_invoice_pdf_bytes(o, p, seller=None)

    subject = f"Faktura {inv_no} â€“ NĂˇramkovĂˇ MĂłda"
    body = (
        f"DobrĂ˝ den {o.customer_name},\n\n"
        f"v pĹ™Ă­loze zasĂ­lĂˇme fakturu ÄŤ. {inv_no} k VaĹˇemu nĂˇkupu.\n"
        f"DÄ›kujeme za nĂˇkup.\n\n"
        f"NĂˇramkovĂˇ MĂłda"
    )

    msg = Message(subject=subject, recipients=[recipient], body=body)
    msg.attach(f"{inv_no}.pdf", "application/pdf", pdf_bytes)
    mail.send(msg)

    flash(f"đź“§ Faktura {inv_no} odeslĂˇna na {recipient}.", "success")
    return redirect("/admin/sold")


