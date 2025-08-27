from io import BytesIO
from datetime import datetime

from flask import render_template, send_file, redirect, url_for, flash
from flask_login import login_required

from backend.admin import admin_bp
from backend.admin.models import SoldProduct  # uprav, pokud máš jiný model/název

# Export závislosti
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle

_FONT_PATH = "backend/static/fonts/DejaVuSans.ttf"
_FONT_NAME = "DejaVuSans"

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

# ----------------------------- LIST -----------------------------
@admin_bp.route("/sold")
@login_required
def sold_products():
    sold = SoldProduct.query.order_by(SoldProduct.sold_at.desc()).all()
    return render_template("admin/sold/list.html", sold_products=sold)

# ----------------------------- EXPORT -----------------------------
@admin_bp.get("/sold/export.<fmt>", endpoint="export_sold")
@login_required
def export_sold(fmt: str):
    items = SoldProduct.query.order_by(SoldProduct.sold_at.desc()).all()

    rows = []
    for it in items:
        name = getattr(it, "name", "") or ""
        price = getattr(it, "price", None)
        if price is None:
            price = getattr(it, "price_czk", None)
        try:
            price = float(price) if price is not None else None
        except Exception:
            pass

        qty = getattr(it, "quantity", 1) or 1
        customer_name = getattr(it, "customer_name", "") or ""
        customer_email = getattr(it, "customer_email", "") or ""
        customer_address = getattr(it, "customer_address", "") or ""
        note = getattr(it, "note", "") or ""
        payment_type = getattr(it, "payment_type", "") or ""
        sold_at = getattr(it, "sold_at", None)
        sold_at_str = sold_at.strftime("%d.%m.%Y %H:%M") if isinstance(sold_at, datetime) else (str(sold_at) if sold_at else "")

        rows.append([
            name,
            price if price is not None else "",
            qty,
            customer_name,
            customer_email,
            customer_address,
            note,
            payment_type,
            sold_at_str,
        ])

    headers = ["Název", "Cena", "Množství", "Zákazník", "Email", "Adresa", "Poznámka", "Typ platby", "Datum"]

    fmt = (fmt or "").lower()
    if fmt == "xlsx":
        bio = BytesIO()
        df = pd.DataFrame(rows, columns=headers)
        with pd.ExcelWriter(bio, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Prodané")
        bio.seek(0)
        return send_file(
            bio, as_attachment=True,
            download_name="prodané.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    if fmt == "pdf":
        bio = BytesIO()
        _pdf_table(bio, "🧾 Prodané produkty", headers, rows)
        bio.seek(0)
        return send_file(
            bio, as_attachment=True,
            download_name="prodané.pdf",
            mimetype="application/pdf"
        )

    flash("Nepodporovaný formát exportu.", "danger")
    return redirect(url_for("admin.sold_products"))
