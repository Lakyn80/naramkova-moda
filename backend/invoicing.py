# backend/invoicing.py
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import mm

# Registrace fontů s háčky/čárkami (soubor DejaVuSans.ttf měj ve složce backend/static/fonts/)
def _register_fonts():
    try:
        pdfmetrics.getFont("DejaVuSans")
    except:
        pdfmetrics.registerFont(TTFont("DejaVuSans", "backend/static/fonts/DejaVuSans.ttf"))

def _p(text, size=10, bold=False):
    style = ParagraphStyle(
        name="CZ",
        fontName="DejaVuSans",
        fontSize=size,
        leading=size + 2,
        spaceAfter=2,
    )
    if bold:
        text = f"<b>{text}</b>"
    return Paragraph(text, style)

def format_czk(v):
    return f"{v:,.2f} Kč".replace(",", " ").replace(".", ",")

def build_invoice_pdf_bytes(order, payment, seller=None):
    """
    order: objekt objednávky (očekává .id, .customer_name, .customer_email, .customer_address, .items, .total_czk)
           položky: [{'name':..., 'quantity':..., 'price_czk':...}] nebo model s podobnými atributy
    payment: objekt platby (očekává .id, .vs, .amount_czk, .received_at)
    seller: dict s údaji o dodavateli (název, ico, dic, adresa, email, telefon, iban), nepovinné
    """
    _register_fonts()
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=16*mm, bottomMargin=16*mm
    )

    styles = getSampleStyleSheet()
    story = []

    # Hlavička
    seller = seller or {
        "name": "Náramková Móda",
        "ico": "IČO: 12345678",
        "dic": "DIČ: CZ12345678",
        "addr": "Ulice 1, 110 00 Praha",
        "email": "info@naramkova-moda.cz",
        "phone": "+420 777 000 000",
        "iban": "CZ00 0000 0000 0000 0000 0000",
    }

    inv_no = f"NM-{order.id:06d}-{payment.id}"
    issued = datetime.utcnow().strftime("%d.%m.%Y")
    paid = payment.received_at.strftime("%d.%m.%Y") if getattr(payment, "received_at", None) else issued

    story.append(_p("DAŇOVÝ DOKLAD / FAKTURA", size=16, bold=True))
    story.append(Spacer(1, 4))
    story.append(_p(f"Číslo dokladu: {inv_no}", bold=True))
    story.append(_p(f"Datum vystavení: {issued}"))
    story.append(_p(f"Datum zdanitelného plnění: {paid}"))
    story.append(Spacer(1, 8))

    # Prodávající / Kupující
    left = [
        _p("<b>Dodavatel</b>"), _p(seller["name"]),
        _p(seller["addr"]), _p(seller["ico"]), _p(seller["dic"]),
        _p(f"IBAN: {seller['iban']}"),
        _p(f"Email: {seller['email']} | Tel: {seller['phone']}"),
    ]
    cust_addr = (order.customer_address or "").replace("\n", "<br/>")
    right = [
        _p("<b>Odběratel</b>"), _p(order.customer_name or ""),
        _p(cust_addr), _p(order.customer_email or ""),
    ]

    table_party = Table(
        [[left, right]], colWidths=[90*mm, 82*mm]
    )
    table_party.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 12),
    ]))
    story.append(table_party)
    story.append(Spacer(1, 10))

    # Položky
    data = [["Položka", "Množství", "Cena/ks", "Cena celkem"]]
    total = 0.0
    # order.items může být list dictů nebo modelů. Přizpůsobíme:
    for it in getattr(order, "items", []):
        name = getattr(it, "name", None) or it.get("name", "")
        qty = getattr(it, "quantity", None) or it.get("quantity", 1)
        price = getattr(it, "price_czk", None) or it.get("price_czk", 0.0)
        line = (price or 0.0) * (qty or 0)
        total += line
        data.append([name, str(qty), format_czk(price or 0.0), format_czk(line)])

    # Pokud máš `order.total_czk`, ber ho jako zdroj pravdy:
    total = float(getattr(order, "total_czk", total) or 0.0)

    tbl = Table(data, colWidths=[90*mm, 22*mm, 30*mm, 30*mm])
    tbl.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), "DejaVuSans"),
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#f1f3f5")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.black),
        ("GRID", (0,0), (-1,-1), 0.25, colors.HexColor("#ced4da")),
        ("ALIGN", (1,1), (-1,-1), "RIGHT"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("PADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 6))

    # Souhrn
    summary = Table([
        ["Způsob úhrady", "VS", "Celkem"],
        [getattr(payment, "payment_type", "Bankovní převod"), str(payment.vs or ""), format_czk(total)],
    ], colWidths=[60*mm, 40*mm, 42*mm])
    summary.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), "DejaVuSans"),
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#f1f3f5")),
        ("GRID", (0,0), (-1,-1), 0.25, colors.HexColor("#ced4da")),
        ("ALIGN", (-1,0), (-1,-1), "RIGHT"),
        ("PADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(summary)
    story.append(Spacer(1, 8))
    story.append(_p("Poznámka: Tento doklad byl vystaven elektronicky a je platný bez podpisu a razítka.", size=9))

    doc.build(story)
    return buf.getvalue(), inv_no
