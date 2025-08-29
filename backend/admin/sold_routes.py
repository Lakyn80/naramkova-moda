# backend/admin/sold_routes.py
import io, csv
from datetime import datetime
from decimal import Decimal, InvalidOperation

from flask import render_template, request, redirect, url_for, flash, send_file, Response
from flask_login import login_required
from flask_mail import Message

from backend.admin import admin_bp
from backend.extensions import db, mail
from backend.admin.models import SoldProduct
from backend.invoicing import build_invoice_pdf_bytes


# ───────────────── LIST (bez trailing slash): /admin/sold ─────────────────
@admin_bp.get("/sold", endpoint="sold_list")
@login_required
def sold_list():
    items = (
        db.session.query(SoldProduct)
        .order_by(SoldProduct.sold_at.desc().nullslast())
        .all()
    )
    return render_template("admin/sold/list.html", sold_products=items)


# ──────────────── Faktura – náhled + odeslání e-mailem ───────────────────
@admin_bp.get("/sold/<int:sold_id>/invoice.pdf", endpoint="sold_invoice_pdf")
@login_required
def sold_invoice_pdf(sold_id: int):
    sold = db.session.get(SoldProduct, sold_id)
    if not sold:
        from flask import abort; abort(404)
    pdf_bytes = build_invoice_pdf_bytes(sold)
    return send_file(io.BytesIO(pdf_bytes), mimetype="application/pdf",
                     as_attachment=False, download_name=f"faktura_{sold.id}.pdf")

@admin_bp.post("/sold/<int:sold_id>/invoice/send", endpoint="sold_send_invoice")
@login_required
def sold_send_invoice(sold_id: int):
    sold = db.session.get(SoldProduct, sold_id)
    if not sold:
        from flask import abort; abort(404)

    target_email = (request.form.get("email") or sold.customer_email or "").strip()
    if not target_email:
        flash("Chybí e-mail pro odeslání.", "warning")
        return redirect(request.headers.get("Referer") or url_for("admin.sold_list"))

    pdf_bytes = build_invoice_pdf_bytes(sold)
    msg = Message(
        subject=f"Faktura #{sold.id} – Náramková Móda",
        recipients=[target_email],
        body=(
            f"Dobrý den {sold.customer_name or ''},\n\n"
            "v příloze posíláme fakturu k Vaší objednávce.\n"
            "Děkujeme za nákup.\n\n"
            "Náramková Móda"
        ),
    )
    msg.attach(filename=f"faktura_{sold.id}.pdf", content_type="application/pdf", data=pdf_bytes)
    try:
        mail.send(msg)
        flash(f"Faktura byla odeslána na {target_email}.", "success")
    except Exception as e:
        flash(f"E-mail se nepodařilo odeslat: {e}", "danger")

    return redirect(request.headers.get("Referer") or url_for("admin.sold_list"))


# ─────────────────────────── EXPORT XLSX ───────────────────────────
@admin_bp.get("/sold/export.xlsx", endpoint="sold_export_xlsx")
@login_required
def sold_export_xlsx():
    rows = (
        db.session.query(SoldProduct)
        .order_by(SoldProduct.sold_at.desc().nullslast())
        .all()
    )
    try:
        from openpyxl import Workbook
        from openpyxl.utils import get_column_letter

        wb = Workbook()
        ws = wb.active
        ws.title = "Prodané"
        ws.append(["Datum","Název","Množství","Cena","Zákazník","Email","Adresa","Poznámka","Typ platby"])

        for r in rows:
            date_str = r.sold_at.strftime("%d.%m.%Y %H:%M") if r.sold_at else ""
            price = float(Decimal(str(r.price or "0")))
            ws.append([date_str, r.name or "", r.quantity or 1, price,
                       r.customer_name or "", r.customer_email or "",
                       (r.customer_address or ""), r.note or "", r.payment_type or ""])

        for i, w in enumerate([18,28,10,12,20,26,36,26,16], start=1):
            ws.column_dimensions[get_column_letter(i)].width = w

        bio = io.BytesIO(); wb.save(bio); bio.seek(0)
        return send_file(bio, as_attachment=True, download_name="sold_export.xlsx",
                         mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception:
        # fallback CSV – ať se vždy něco stáhne
        out = io.StringIO(); w = csv.writer(out, delimiter=';')
        w.writerow(["Datum","Název","Množství","Cena","Zákazník","Email","Adresa","Poznámka","Typ platby"])
        for r in rows:
            date_str = r.sold_at.strftime("%d.%m.%Y %H:%M") if r.sold_at else ""
            w.writerow([date_str, r.name or "", r.quantity or 1, str(r.price or ""),
                        r.customer_name or "", r.customer_email or "",
                        (r.customer_address or "").replace("\n"," "), r.note or "", r.payment_type or ""])
        return Response(out.getvalue(), mimetype="text/csv",
                        headers={"Content-Disposition": 'attachment; filename=\"sold_export.csv\"'})


# ─────────────────────────── EXPORT PDF ───────────────────────────
@admin_bp.get("/sold/export.pdf", endpoint="sold_export_pdf")
@login_required
def sold_export_pdf():
    rows = (
        db.session.query(SoldProduct)
        .order_by(SoldProduct.sold_at.desc().nullslast())
        .all()
    )
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet

        bio = io.BytesIO()
        doc = SimpleDocTemplate(bio, pagesize=landscape(A4),
                                leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)

        styles = getSampleStyleSheet()
        elements = [Paragraph("Report – Prodané produkty", styles["Heading2"]), Spacer(1, 8)]

        data = [["Datum","Název","Množství","Cena (Kč)","Zákazník","Email","Adresa","Poznámka","Typ platby"]]
        total = Decimal("0")
        for r in rows:
            qty = r.quantity or 1
            price = Decimal(str(r.price or "0"))
            total += price * qty
            data.append([
                r.sold_at.strftime("%d.%m.%Y %H:%M") if r.sold_at else "",
                r.name or "", qty, f"{price:.2f}",
                r.customer_name or "", r.customer_email or "", (r.customer_address or ""),
                r.note or "", r.payment_type or ""
            ])
        data.append(["","","","","","","","Součet", f"{total:.2f}"])

        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),colors.lightgrey),
            ("GRID",(0,0),(-1,-1),0.25,colors.grey),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
            ("ALIGN",(2,1),(3,-2),"RIGHT"),
            ("BACKGROUND",(-2,-1),(-1,-1),colors.lightgrey),
            ("FONTNAME",(-2,-1),(-1,-1),"Helvetica-Bold"),
            ("ALIGN",(-1,-1),(-1,-1),"RIGHT"),
        ]))

        elements.append(table)
        doc.build(elements); bio.seek(0)
        return send_file(bio, as_attachment=True, download_name="sold_report.pdf", mimetype="application/pdf")
    except Exception:
        return sold_export_xlsx()
