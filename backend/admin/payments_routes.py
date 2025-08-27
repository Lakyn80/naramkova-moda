# 📁 backend/admin/payments_routes.py
from datetime import datetime
from io import BytesIO

from flask import (
    request, render_template, redirect, url_for, flash, send_file
)
from flask_mail import Message

from backend.extensions import db, mail
from . import admin_bp
from backend.admin.models import Payment, Order
from backend.invoicing import build_invoice_pdf_bytes

# Export: pandas (xlsx) + reportlab (pdf tabulka)
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle

ALLOWED_STATUSES = ("pending", "received", "failed", "canceled", "refunded")
_FONT_PATH = "backend/static/fonts/DejaVuSans.ttf"
_FONT_NAME = "DejaVuSans"


# ----------------------------- PDF pomocné -----------------------------
def _ensure_font():
    try:
        pdfmetrics.getFont(_FONT_NAME)
    except Exception:
        pdfmetrics.registerFont(TTFont(_FONT_NAME, _FONT_PATH))

def _pdf_table(buf: BytesIO, title: str, headers: list[str], rows: list[list]):
    _ensure_font()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(A4),
        leftMargin=16, rightMargin=16, topMargin=18, bottomMargin=18
    )
    story = []
    style = ParagraphStyle(name="CZ", fontName=_FONT_NAME, fontSize=12, leading=14)
    story.append(Paragraph(title, style))
    story.append(Spacer(1, 8))
    data = [headers] + rows
    tbl = Table(data, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), _FONT_NAME),
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#f1f3f5")),
        ("GRID", (0,0), (-1,-1), 0.25, colors.HexColor("#ced4da")),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN", (0,0), (-1,0), "CENTER"),
        ("PADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(tbl)
    doc.build(story)


# ------------------------------- INDEX -------------------------------
@admin_bp.route("/payments", methods=["GET"], endpoint="admin_payments_index")
def admin_payments_index():
    vs = (request.args.get("vs") or "").strip()
    status = (request.args.get("status") or "all").strip()
    try:
        limit = int(request.args.get("limit") or 100)
    except Exception:
        limit = 100
    limit = max(1, min(limit, 1000))

    q = db.session.query(Payment, Order).outerjoin(Order, Order.vs == Payment.vs)
    if vs:
        q = q.filter(Payment.vs == vs)
    if status and status != "all":
        q = q.filter(Payment.status == status)

    rows = q.order_by(Payment.id.desc()).limit(limit).all()
    rows_out = [{"p": p, "o": o} for (p, o) in rows]

    total_amount = 0.0
    count = 0
    for r in rows_out:
        amt = getattr(r["p"], "amount_czk", None)
        if amt is not None:
            try:
                total_amount += float(amt)
            except Exception:
                pass
        count += 1

    return render_template(
        "admin/payments/index.html",
        rows=rows_out,
        summary=type("S", (), {"count": count, "total_amount": total_amount})(),
        filters={"vs": vs, "status": status, "limit": limit},
        has_order_detail=hasattr(Order, "id"),
        allowed_statuses=ALLOWED_STATUSES,
    )


# ------------------------------- UPDATE STATUS -------------------------------
@admin_bp.post("/payments/<int:payment_id>/status")
def admin_payment_update_status(payment_id: int):
    new_status = (request.form.get("status") or "").strip()
    if new_status not in ALLOWED_STATUSES:
        flash("Neplatný status.", "danger")
        return redirect(url_for("admin.admin_payments_index"))

    p = db.session.get(Payment, payment_id)
    if not p:
        flash("Platba nebyla nalezena.", "danger")
        return redirect(url_for("admin.admin_payments_index"))

    old_status = p.status
    p.status = new_status
    if new_status == "received" and getattr(p, "received_at", None) is None:
        p.received_at = datetime.utcnow()

    o = db.session.query(Order).filter_by(vs=p.vs).first()
    if o:
        if new_status == "received":
            o.status = "paid"
        elif o.status != "paid":
            o.status = "awaiting_payment"

    db.session.commit()
    flash(f"Status platby #{p.id} změněn na '{new_status}'.", "success")

    # odeslání faktury při přechodu na received
    if old_status != "received" and new_status == "received" and o and (o.customer_email or "").strip():
        try:
            pdf_bytes, inv_no = build_invoice_pdf_bytes(
                order=o,
                payment=p,
                seller={
                    "name": "Náramková Móda",
                    "ico": "IČO: 12345678",
                    "dic": "DIČ: CZ12345678",
                    "addr": "Ulice 1, 110 00 Praha",
                    "email": "info@naramkova-moda.cz",
                    "phone": "+420 777 000 000",
                    "iban": "CZ00 0000 0000 0000 0000 0000",
                }
            )
            msg = Message(
                subject=f"Faktura {inv_no} – Náramková Móda",
                recipients=[o.customer_email],
            )
            msg.body = (
                f"Dobrý den {o.customer_name or ''},\n\n"
                f"děkujeme za platbu. V příloze posíláme fakturu {inv_no}.\n\n"
                f"Hezký den,\nNáramková Móda"
            )
            msg.attach(f"Faktura-{inv_no}.pdf", "application/pdf", pdf_bytes)
            mail.send(msg)
            flash(f"Faktura {inv_no} odeslána na {o.customer_email}.", "success")
        except Exception as e:
            flash(f"Fakturu se nepodařilo odeslat: {e}", "danger")

    return redirect(url_for("admin.admin_payments_index"))


# ------------------------------- EXPORT -------------------------------
@admin_bp.route("/payments/export.<fmt>", methods=["GET"], endpoint="export_payments")
def export_payments(fmt: str):
    payments = Payment.query.order_by(Payment.id.desc()).all()
    rows = []
    for p in payments:
        rows.append([
            p.id,
            p.vs or "",
            float(p.amount_czk or 0.0),
            p.status or "",
            p.received_at.strftime("%d.%m.%Y %H:%M") if p.received_at else "",
            getattr(p, "order_id", "") or "",
        ])

    headers = ["ID", "VS", "Částka", "Status", "Přijato", "Objednávka"]

    fmt = (fmt or "").lower()
    if fmt == "xlsx":
        bio = BytesIO()
        df = pd.DataFrame(rows, columns=headers)
        with pd.ExcelWriter(bio, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Platby")
        bio.seek(0)
        return send_file(
            bio, as_attachment=True,
            download_name="platby.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    if fmt == "pdf":
        bio = BytesIO()
        _pdf_table(bio, "💳 Platby", headers, rows)
        bio.seek(0)
        return send_file(
            bio, as_attachment=True,
            download_name="platby.pdf",
            mimetype="application/pdf"
        )

    flash("Nepodporovaný formát exportu.", "danger")
    return redirect(url_for("admin.admin_payments_index"))
