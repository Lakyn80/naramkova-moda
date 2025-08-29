# backend/invoicing.py
from io import BytesIO
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import mm


def _register_fonts():
    """
    Zkusí načíst DejaVuSans.ttf z backend/static/fonts bez ohledu na working dir.
    Pokud není k dispozici, nechá defaultní font (diakritika pak nemusí být 100%).
    """
    try:
        pdfmetrics.getFont("DejaVuSans")
        return
    except Exception:
        pass

    here = Path(__file__).resolve()
    ttf = here.parent / "static" / "fonts" / "DejaVuSans.ttf"
    if ttf.exists():
        pdfmetrics.registerFont(TTFont("DejaVuSans", str(ttf)))


def _p(text: str, size: int = 10, bold: bool = False) -> Paragraph:
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


def format_czk(v: float) -> str:
    return f"{v:,.2f} Kč".replace(",", " ").replace(".", ",")


def build_invoice_pdf_bytes(order, payment, seller=None):
    """
    Vygeneruje PDF fakturu do bytes a vrátí (pdf_bytes, invoice_number).

    order: objekt/struct s poli:
        .id, .customer_name, .customer_email, .customer_address, .items (list), .total_czk
        položka v .items: dict nebo objekt s: name, quantity, price_czk
    payment: objekt/struct s poli:
        .id, .vs, .amount_czk, .received_at, .payment_type
    seller: dict s údaji o dodavateli (name, ico, dic, addr, email, phone, iban) – volitelné
    """
    _register_fonts()

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )

    story = []

    # Výchozí dodavatel, pokud nepředán
    seller = seller or {
        "name": "Náramková Móda",
        "ico": "IČO: 12345678",
        "dic": "DIČ: CZ12345678",
        "addr": "Ulice 1, 110 00 Praha",
        "email": "info@naramkova-moda.cz",
        "phone": "+420 777 000 000",
        "iban": "CZ00 0000 0000 0000 0000 0000",
    }

    inv_no = f"NM-{int(getattr(order, 'id', 0) or 0):06d}-{int(getattr(payment, 'id', 0) or 0)}"
    issued = datetime.utcnow().strftime("%d.%m.%Y")
    paid_dt = getattr(payment, "received_at", None) or datetime.utcnow()
    paid = paid_dt.strftime("%d.%m.%Y")

    # Hlavička
    story.append(_p("DAŇOVÝ DOKLAD / FAKTURA", size=16, bold=True))
    story.append(Spacer(1, 4))
    story.append(_p(f"Číslo dokladu: {inv_no}", bold=True))
    story.append(_p(f"Datum vystavení: {issued}"))
    story.append(_p(f"Datum zdanitelného plnění: {paid}"))
    story.append(Spacer(1, 8))

    # Dodavatel / Odběratel
    left = [
        _p("<b>Dodavatel</b>"),
        _p(seller.get("name", "")),
        _p(seller.get("addr", "")),
        _p(seller.get("ico", "")),
        _p(seller.get("dic", "")),
        _p(f"IBAN: {seller.get('iban', '')}"),
        _p(f"Email: {seller.get('email', '')} | Tel: {seller.get('phone', '')}"),
    ]
    cust_addr = (getattr(order, "customer_address", "") or "").replace("\n", "<br/>")
    right = [
        _p("<b>Odběratel</b>"),
        _p(getattr(order, "customer_name", "") or ""),
        _p(cust_addr),
        _p(getattr(order, "customer_email", "") or ""),
    ]

    table_party = Table([[left, right]], colWidths=[90 * mm, 82 * mm])
    table_party.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    story.append(table_party)
    story.append(Spacer(1, 10))

    # Položky
    data = [["Položka", "Množství", "Cena/ks", "Cena celkem"]]
    total = 0.0

    items = getattr(order, "items", []) or []
    for it in items:
        # podporuj dict i objekt
        name = getattr(it, "name", None) or (it.get("name") if isinstance(it, dict) else "")
        qty = getattr(it, "quantity", None) or (it.get("quantity") if isinstance(it, dict) else 1) or 1
        price = getattr(it, "price_czk", None) or (it.get("price_czk") if isinstance(it, dict) else 0.0) or 0.0
        line = float(price) * int(qty)
        total += line
        data.append([name, str(qty), format_czk(float(price)), format_czk(line)])

    # Pokud má order.total_czk, ber ho jako zdroj pravdy
    total = float(getattr(order, "total_czk", total) or total)

    tbl = Table(data, colWidths=[90 * mm, 22 * mm, 30 * mm, 30 * mm])
    tbl.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "DejaVuSans"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f3f5")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#ced4da")),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(tbl)
    story.append(Spacer(1, 6))

    # Souhrn
    payment_type = getattr(payment, "payment_type", "Bankovní převod")
    vs = getattr(payment, "vs", "") or ""
    summary = Table(
        [["Způsob úhrady", "VS", "Celkem"], [payment_type, str(vs), format_czk(total)]],
        colWidths=[60 * mm, 40 * mm, 42 * mm],
    )
    summary.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "DejaVuSans"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f3f5")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#ced4da")),
                ("ALIGN", (-1, 0), (-1, -1), "RIGHT"),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(summary)
    story.append(Spacer(1, 8))
    story.append(
        _p(
            "Poznámka: Tento doklad byl vystaven elektronicky a je platný bez podpisu a razítka.",
            size=9,
        )
    )

    doc.build(story)
    return buf.getvalue(), inv_no
