# backend/admin/sold_routes.py
import io
import os
from datetime import datetime, timedelta
from decimal import Decimal

from flask import (
    Blueprint, request, render_template, send_file, url_for, redirect, flash, current_app
)
from flask_login import login_required
from flask_mail import Message

from backend.admin import admin_bp  # zachováno
from backend.extensions import db, mail
from backend.admin.models import SoldProduct
from backend.invoicing import build_invoice_pdf_bytes  # využijeme existující generátor FA


# -----------------------------
# Pomocné funkce – parsování/čísla
# -----------------------------

def _parse_date(s: str):
    """Bezpečné parsování data ve formátu YYYY-MM-DD, vrací datetime nebo None."""
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except Exception:
        return None


def _to_float(v) -> float:
    """Robustní převod na float (podpora Decimal, řetězců s čárkou atd.)."""
    if v is None:
        return 0.0
    if isinstance(v, float):
        return v
    if isinstance(v, int):
        return float(v)
    if isinstance(v, Decimal):
        return float(v)
    try:
        s = str(v).strip().replace(",", ".")
        return float(s) if s else 0.0
    except Exception:
        return 0.0


def _get_first_attr(obj, *names):
    """Vrátí první nenull/neen-prázdný atribut z dodaných názvů, jinak None."""
    for n in names:
        if hasattr(obj, n):
            val = getattr(obj, n)
            if val not in (None, ""):
                return val
    return None


def _guess_unit_price_czk(sp) -> float:
    """Najdi nejpravděpodobnější pole s jednotkovou cenou (CZK)."""
    cand = _get_first_attr(
        sp,
        "unit_price_czk", "price_czk",
        "unit_price", "price",
        "unit", "unit_czk", "sold_unit_price_czk", "final_price_czk",
    )
    return round(_to_float(cand), 2)


def _guess_quantity(sp) -> float:
    """Najdi množství; fallback na 1.0, pokud nic rozumného nenalezeno."""
    cand = _get_first_attr(sp, "quantity", "qty", "count", "pieces", "amount_units")
    q = _to_float(cand)
    return q if q > 0 else 1.0


def _guess_total_czk(sp) -> float:
    """
    Najdi celkovou cenu; když chybí nebo je 0/None, dopočítej unit * qty.
    """
    cand = _get_first_attr(sp, "total_czk", "total_price_czk", "amount_czk", "amount")
    total = _to_float(cand)
    if total > 0:
        return round(total, 2)
    unit = _guess_unit_price_czk(sp)
    qty = _guess_quantity(sp)
    return round(unit * qty, 2)


def _sold_datetime(sp):
    """Vrať datetime pro setřídění/filtr (preferuj sold_at, jinak created_at)."""
    return _get_first_attr(sp, "sold_at", "created_at")


def _base_query(filters: dict):
    """
    Základní dotaz pro SoldProduct s podporou ?from & ?to (včetně).
    Třídí dle sold_at desc, pokud je k dispozici; jinak dle id desc.
    """
    q = SoldProduct.query
    d_from = _parse_date(filters.get("from"))
    d_to = _parse_date(filters.get("to"))

    if hasattr(SoldProduct, "sold_at"):
        if d_from:
            q = q.filter(SoldProduct.sold_at >= d_from)
        if d_to:
            q = q.filter(SoldProduct.sold_at < (d_to + timedelta(days=1)))
        q = q.order_by(SoldProduct.sold_at.desc())
    else:
        if hasattr(SoldProduct, "id"):
            q = q.order_by(SoldProduct.id.desc())

    return q


def _to_row_dict(sp: SoldProduct):
    """Mapování záznamu na řádek do šablony/exportů (včetně dopočtu cen)."""
    sold_dt = _sold_datetime(sp)
    return {
        "id": getattr(sp, "id", None),
        "order_id": _get_first_attr(sp, "order_id", "order_code"),
        "product_name": _get_first_attr(sp, "product_name", "name"),
        "quantity": _guess_quantity(sp),
        "unit_price_czk": _guess_unit_price_czk(sp),
        "total_czk": _guess_total_czk(sp),
        "status": getattr(sp, "status", None),
        "customer_email": _get_first_attr(sp, "customer_email", "email"),
        "vs": getattr(sp, "vs", None),
        "sold_at": sold_dt,
    }


# -----------------------------
# Seznam + filtry
# -----------------------------

@admin_bp.route("/sold")
@login_required
def sold_products():
    """
    Seznam prodaných s filtry ?from=YYYY-MM-DD&to=YYYY-MM-DD
    a souhrnem (počet, suma).
    """
    filters = {
        "from": request.args.get("from", "").strip(),
        "to": request.args.get("to", "").strip(),
    }

    q = _base_query(filters)
    items = q.all()

    # Manuální filtr dle datumu, pokud model nemá sold_at sloupec
    d_from = _parse_date(filters.get("from"))
    d_to_excl = _parse_date(filters.get("to"))
    if d_to_excl:
        d_to_excl = d_to_excl + timedelta(days=1)

    if not hasattr(SoldProduct, "sold_at") and (d_from or d_to_excl):
        filtered = []
        for sp in items:
            dt = _sold_datetime(sp)
            if isinstance(dt, datetime):
                if d_from and dt < d_from:
                    continue
                if d_to_excl and dt >= d_to_excl:
                    continue
            filtered.append(sp)
        items = filtered

    rows = [_to_row_dict(sp) for sp in items]

    # Souhrn
    count = len(rows)
    total_amount = round(sum(_to_float(r["total_czk"]) for r in rows), 2)

    # Řazení (nejnovější nahoře)
    rows.sort(key=lambda r: r["sold_at"] or datetime.min, reverse=True)

    return render_template(
        "admin/sold/list.html",
        filters=filters,
        rows=rows,
        summary={"count": count, "total_amount": total_amount},
    )


# -----------------------------
# Export: Excel (XLSX)
# -----------------------------

@admin_bp.route("/sold/export.xlsx")
@login_required
def sold_export_xlsx():
    """
    Export do Excelu s aktuálními filtry.
    Vyžaduje knihovnu openpyxl (pip install openpyxl).
    """
    try:
        import openpyxl
        from openpyxl.utils import get_column_letter
    except ImportError:
        flash("Chybí balík openpyxl. Nainstaluj: pip install openpyxl", "danger")
        return redirect(url_for("admin.sold_products", **request.args))

    filters = {
        "from": request.args.get("from", "").strip(),
        "to": request.args.get("to", "").strip(),
    }
    q = _base_query(filters)
    items = q.all()

    # Manuální datum filtr, pokud není sold_at
    d_from = _parse_date(filters.get("from"))
    d_to_excl = _parse_date(filters.get("to"))
    if d_to_excl:
        d_to_excl = d_to_excl + timedelta(days=1)
    if not hasattr(SoldProduct, "sold_at") and (d_from or d_to_excl):
        filtered = []
        for sp in items:
            dt = _sold_datetime(sp)
            if isinstance(dt, datetime):
                if d_from and dt < d_from:
                    continue
                if d_to_excl and dt >= d_to_excl:
                    continue
            filtered.append(sp)
        items = filtered

    data = [_to_row_dict(sp) for sp in items]

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Prodané položky"

    headers = [
        "ID", "Objednávka", "Produkt", "Množství",
        "Cena/ks (Kč)", "Celkem (Kč)", "Status",
        "E-mail", "VS", "Prodané"
    ]
    ws.append(headers)

    for r in data:
        ws.append([
            r["id"], r["order_id"], r["product_name"], r["quantity"],
            r["unit_price_czk"], r["total_czk"], r["status"],
            r["customer_email"], r["vs"],
            r["sold_at"].strftime("%Y-%m-%d %H:%M") if isinstance(r["sold_at"], datetime) else ""
        ])

    # Auto šířky
    for col_idx, _ in enumerate(headers, start=1):
        max_len = 0
        for row in ws.iter_rows(min_col=col_idx, max_col=col_idx):
            cell = row[0]
            if cell.value is not None:
                max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[get_column_letter(col_idx)].width = min(max_len + 2, 40)

    bio = io.BytesIO()
    wb.save(bio)
    bio.seek(0)
    filename = f"sold_{filters.get('from','')}_{filters.get('to','')}.xlsx".replace("__", "_").strip("_")
    return send_file(
        bio,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=filename or "sold.xlsx",
    )


# -----------------------------
# PDF – pomocná registrace CZ fontu
# -----------------------------

def _register_cz_fonts(pdfmetrics, TTFont):
    """
    Zkusí zaregistrovat Unicode TTF font pro diakritiku.
    Preferuje DejaVu Sans, pak Noto Sans, nakonec Windows Arial.
    Vrací (regular_name, bold_name) nebo (None, None), když nic nenašel.
    """
    root = current_app.root_path  # backend/
    candidates = [
        # DejaVu Sans
        (os.path.join(root, "static", "fonts", "DejaVuSans.ttf"),
         os.path.join(root, "static", "fonts", "DejaVuSans-Bold.ttf"),
         "DejaVuSans", "DejaVuSans-Bold"),
        # Noto Sans
        (os.path.join(root, "static", "fonts", "NotoSans-Regular.ttf"),
         os.path.join(root, "static", "fonts", "NotoSans-Bold.ttf"),
         "NotoSans", "NotoSans-Bold"),
        # Windows Arial (poslední záchrana)
        (r"C:\Windows\Fonts\arial.ttf",
         r"C:\Windows\Fonts\arialbd.ttf",
         "ArialTT", "ArialTT-Bold"),
    ]

    for reg_path, bold_path, reg_name, bold_name in candidates:
        if os.path.isfile(reg_path):
            try:
                pdfmetrics.registerFont(TTFont(reg_name, reg_path))
                if os.path.isfile(bold_path):
                    pdfmetrics.registerFont(TTFont(bold_name, bold_path))
                else:
                    bold_name = reg_name  # fallback na regular, pokud bold chybí
                return reg_name, bold_name
            except Exception:
                continue
    return None, None


# -----------------------------
# Export: PDF report seznamu (s CZ fontem)
# -----------------------------

@admin_bp.route("/sold/export.pdf")
@login_required
def sold_export_pdf():
    """
    Jednoduchý PDF report (seznam). Vyžaduje reportlab (pip install reportlab).
    Registruje Unicode TTF font (DejaVu/Noto/Arial), aby fungovala čeština.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except ImportError:
        flash("Chybí balík reportlab. Nainstaluj: pip install reportlab", "danger")
        return redirect(url_for("admin.sold_products", **request.args))

    # Registrace CZ fontu
    regular_font, bold_font = _register_cz_fonts(pdfmetrics, TTFont)
    if not regular_font:
        flash(
            "Pro korektní češtinu v PDF vlož TTF font do backend/static/fonts/ "
            "(např. DejaVuSans.ttf a DejaVuSans-Bold.ttf). Zatím používám Helvetica.",
            "warning",
        )
    title_font = bold_font or "Helvetica-Bold"
    text_font = regular_font or "Helvetica"

    # Data
    filters = {
        "from": request.args.get("from", "").strip(),
        "to": request.args.get("to", "").strip(),
    }
    q = _base_query(filters)
    items = q.all()

    # Manuální datum filtr, pokud není sold_at
    d_from = _parse_date(filters.get("from"))
    d_to_excl = _parse_date(filters.get("to"))
    if d_to_excl:
        d_to_excl = d_to_excl + timedelta(days=1)
    if not hasattr(SoldProduct, "sold_at") and (d_from or d_to_excl):
        filtered = []
        for sp in items:
            dt = _sold_datetime(sp)
            if isinstance(dt, datetime):
                if d_from and dt < d_from:
                    continue
                if d_to_excl and dt >= d_to_excl:
                    continue
            filtered.append(sp)
        items = filtered

    data = [_to_row_dict(sp) for sp in items]

    # PDF
    bio = io.BytesIO()
    c = canvas.Canvas(bio, pagesize=A4)
    w, h = A4

    # Header
    c.setFont(title_font, 14)
    c.drawString(20 * mm, (h - 20 * mm), "Report – Prodané položky")

    c.setFont(text_font, 10)
    c.drawString(20 * mm, (h - 27 * mm), f"Filtr: od {filters.get('from') or '-'} do {filters.get('to') or '-'}")
    c.drawString(20 * mm, (h - 33 * mm), f"Počet: {len(data)}")

    # Záhlaví tabulky
    def draw_header(y_pos):
        c.setFont(title_font, 9)
        c.drawString(20 * mm, y_pos, "ID")
        c.drawString(35 * mm, y_pos, "Objednávka")
        c.drawString(65 * mm, y_pos, "Produkt")
        c.drawString(120 * mm, y_pos, "Celkem Kč")
        c.drawString(150 * mm, y_pos, "Prodané")
        return y_pos - 6 * mm

    y = h - 45 * mm
    y = draw_header(y)

    # Řádky
    c.setFont(text_font, 9)
    for r in data:
        if y < 20 * mm:
            c.showPage()
            c.setFont(text_font, 9)
            y = h - 20 * mm
            y = draw_header(y)

        c.drawString(20 * mm, y, str(r["id"] or ""))
        c.drawString(35 * mm, y, str(r["order_id"] or ""))
        c.drawString(65 * mm, y, str((r["product_name"] or "")[:32]))
        c.drawRightString(145 * mm, y, f"{_to_float(r['total_czk']):.2f}")
        dt = r["sold_at"]
        c.drawString(150 * mm, y, dt.strftime("%Y-%m-%d") if isinstance(dt, datetime) else "")
        y -= 6 * mm

    c.showPage()
    c.save()
    bio.seek(0)

    filename = f"sold_{filters.get('from','')}_{filters.get('to','')}.pdf".replace("__", "_").strip("_")
    return send_file(
        bio,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename or "sold.pdf",
    )


# -----------------------------
# Faktura – náhled (PDF)
# -----------------------------

@admin_bp.route("/invoice/<int:sold_id>.pdf")
@login_required
def invoice_preview_pdf(sold_id: int):
    """
    Náhled faktury pro konkrétní SoldProduct (PDF).
    Využívá build_invoice_pdf_bytes(sp) z backend.invoicing.
    """
    sp = SoldProduct.query.get_or_404(sold_id)
    pdf_bytes = build_invoice_pdf_bytes(sp)
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=False,
        download_name=f"invoice_{sold_id}.pdf",
    )


# -----------------------------
# Odeslání faktury e-mailem (jedna položka)
# -----------------------------

@admin_bp.route("/invoice/<int:sold_id>/email", methods=["POST"])
@login_required
def invoice_send_email(sold_id: int):
    """
    Pošle fakturu e-mailem na 'customer_email' (pokud existuje).
    Přikládá PDF generované přes build_invoice_pdf_bytes.
    """
    sp = SoldProduct.query.get_or_404(sold_id)
    to_addr = getattr(sp, "customer_email", None)

    if not to_addr:
        flash("U záznamu není vyplněn e-mail zákazníka.", "warning")
        return redirect(url_for("admin.sold_products"))

    pdf_bytes = build_invoice_pdf_bytes(sp)

    try:
        subject = f"Faktura #{getattr(sp, 'id', '')} – Náramková Móda"
        body = (
            "Dobrý den,\n\n"
            "v příloze zasíláme fakturu k Vaší objednávce.\n"
            "Děkujeme za nákup.\n\n"
            "S pozdravem\nNáramková Móda"
        )
        msg = Message(subject=subject, recipients=[to_addr], body=body)
        msg.attach(
            filename=f"invoice_{sp.id}.pdf",
            content_type="application/pdf",
            data=pdf_bytes,
        )
        mail.send(msg)
        flash(f"E-mail s fakturou byl odeslán na {to_addr}.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Nepodařilo se odeslat e-mail: {e}", "danger")

    return redirect(url_for("admin.sold_products"))


# =============================
# NOVÉ: Odeslání faktury podle ORDER_ID (pro „auto po zaplacení“)
#  - Použij z adminu/servisu po změně stavu na 'paid' / 'zaplaceno'
#  - Vrací dict s výsledkem; volání je idempotentní v tom smyslu,
#    že když pro objednávku není žádný SoldProduct, jen vrátí info.
# =============================

def send_invoice_for_order(order_id: int) -> dict:
    """
    Najde první SoldProduct pro daný order_id, vygeneruje PDF a:
      - pokud už je invoice označená jako odeslaná (invoice_sent_at), NIC neposílá (idempotentní),
      - jinak pošle e-mail, uloží PDF na disk a zapíše info do DB (pokud má model pole).
    """
    sp = (SoldProduct.query
          .filter(SoldProduct.order_id == order_id)
          .order_by(SoldProduct.id.asc())
          .first())

    if not sp:
        return {"ok": False, "error": "No SoldProduct for this order_id."}

    # 1) idempotence: pokud existuje flag, nepřeposílat
    already_sent = False
    if hasattr(sp, "invoice_sent_at") and getattr(sp, "invoice_sent_at", None):
        already_sent = True

    # 2) vygeneruj PDF
    pdf_bytes = build_invoice_pdf_bytes(sp)

    # 3) ulož PDF na disk (ať máš archiv)
    try:
        inv_dir = os.path.join(current_app.root_path, "static", "invoices")
        os.makedirs(inv_dir, exist_ok=True)
        filename = f"invoice_order_{getattr(sp, 'order_id', 'x')}_sold_{sp.id}.pdf"
        file_path = os.path.join(inv_dir, filename)
        with open(file_path, "wb") as f:
            f.write(pdf_bytes)
        saved_rel = f"/static/invoices/{filename}"
    except Exception:
        saved_rel = None

    result = {
        "ok": True,
        "emailed": False,
        "sold_id": getattr(sp, "id", None),
        "saved_path": saved_rel,
        "already_sent": already_sent,
    }

    # 4) pokud už bylo dříve odesláno, skonči (jen informativně vrátíme)
    if already_sent:
        return result

    # 5) pošli e-mail (jen pokud máme adresu)
    to_addr = getattr(sp, "customer_email", None) or getattr(sp, "email", None)
    if not to_addr:
        return result

    try:
        subject = f"Faktura #{getattr(sp, 'id', '')} – Náramková Móda"
        body = (
            "Dobrý den,\n\n"
            "v příloze zasíláme fakturu k Vaší objednávce.\n"
            "Děkujeme za nákup.\n\n"
            "S pozdravem\nNáramková Móda"
        )
        msg = Message(subject=subject, recipients=[to_addr], body=body)
        # přiložíme stejné PDF, které jsme uložili
        msg.attach(
            filename=os.path.basename(saved_rel) if saved_rel else f"invoice_{sp.id}.pdf",
            content_type="application/pdf",
            data=pdf_bytes,
        )
        from backend.extensions import mail  # lokální import, aby se nerozbilo jinde
        mail.send(msg)
        result["emailed"] = True

        # 6) zapíšeme do DB flag (pokud model má sloupce)
        dirty = False
        if hasattr(sp, "invoice_sent_at") and not getattr(sp, "invoice_sent_at", None):
            sp.invoice_sent_at = datetime.utcnow()
            dirty = True
        if saved_rel and hasattr(sp, "invoice_filename") and not getattr(sp, "invoice_filename", None):
            sp.invoice_filename = saved_rel
            dirty = True
        if dirty:
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
    except Exception as e:
        current_app.logger.exception(f"[invoice] send failed for order_id={order_id}: {e}")
        return {"ok": False, "error": str(e), **result}

    return result


# -----------------------------
# VOLITELNÉ: ruční spuštění podle ORDER_ID z UI
# -----------------------------

@admin_bp.route("/sold/order/<int:order_id>/email", methods=["POST"])
@login_required
def invoice_send_email_for_order(order_id: int):
    """
    Ruční odeslání faktury podle order_id (vezme první SoldProduct té objednávky).
    Hodí se pro rychlé „přeposlání“, když došla změna e-mailu apod.
    """
    res = send_invoice_for_order(order_id)
    if res.get("ok") and res.get("emailed"):
        flash(f"Faktura byla odeslána na {res.get('to')}.", "success")
    elif res.get("ok") and not res.get("emailed"):
        flash("Faktura nebyla odeslána – u objednávky není e-mail zákazníka.", "warning")
    else:
        flash(f"Fakturu se nepodařilo odeslat: {res.get('error', 'neznámá chyba')}", "danger")

    # zpět kamkoliv – ideálně na detail objednávky, pokud máš
    return redirect(request.referrer or url_for("admin.sold_products"))
