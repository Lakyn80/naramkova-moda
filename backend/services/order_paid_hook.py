# backend/services/order_paid_hook.py
from __future__ import annotations
import os
import io
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from flask import current_app
from backend.extensions import db
from backend.models import Order, OrderItem, SoldProduct
from backend.api.utils.email import send_email
from backend.invoicing import build_invoice_pdf_bytes

# ---- pomocné ---------------------------------------------------------------

def _to_dec(x) -> Decimal:
    try:
        return Decimal(str(x))
    except Exception:
        return Decimal("0")

def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

# Pseudo objekt, aby šel použít build_invoice_pdf_bytes(sold_product)
@dataclass
class _SoldProxy:
    # identifikace / data
    id: int
    order_id: int
    created_at: datetime | None
    sold_at: datetime | None

    # zákazník
    buyer_name: str | None
    email: str | None
    address: str | None
    note: str | None

    # obsah (souhrn celé objednávky)
    name: str                 # např. "Objednávka #123 – 3 položky"
    quantity: float           # 1 (souhrn)
    unit_price_czk: float     # celková cena bez poštovného (pro kompat.)
    total_czk: float          # celková cena položek (bez poštovného)

    # platba
    vs: str | None

# ---- logika ----------------------------------------------------------------

def _sum_order_items(order: Order) -> tuple[Decimal, int]:
    items: list[OrderItem] = OrderItem.query.filter_by(order_id=order.id).all()
    total = Decimal("0")
    count = 0
    for it in items:
        qty = _to_dec(it.quantity or 0)
        price = _to_dec(it.price or 0)
        total += qty * price
        count += int(qty)
    return total, count

def _ensure_sold_rows(order: Order) -> int:
    """Vytvoří chybějící SoldProduct řádky za položky objednávky, idempotentně."""
    marker = f"order-{order.id}"
    try:
        existing_rows = SoldProduct.query.filter_by(payment_type=marker).all()
    except Exception:
        existing_rows = []

    existing_keys = {
        (
            (getattr(sp, "name", "") or "").strip().lower(),
            int(getattr(sp, "quantity", 0) or 0),
            str(_to_dec(getattr(sp, "price", 0))),
        )
        for sp in existing_rows
    }

    items: list[OrderItem] = OrderItem.query.filter_by(order_id=order.id).all()
    created = 0

    note_parts = [f"Objednávka #{order.id}"]
    if getattr(order, "vs", None):
        note_parts.append(f"VS {order.vs}")
    if getattr(order, "note", None):
        note_parts.append(str(order.note))
    base_note = " | ".join(note_parts)

    for it in items:
        key = (
            (getattr(it, "product_name", "") or "").strip().lower(),
            int(getattr(it, "quantity", 0) or 0),
            str(_to_dec(getattr(it, "price", 0))),
        )
        if key in existing_keys:
            continue

        price_dec = _to_dec(getattr(it, "price", 0))
        if price_dec < Decimal("1.00"):
            current_app.logger.warning(
                "SoldProduct skip: abnormally low price %.4f for order #%s item '%s'",
                float(price_dec),
                order.id,
                getattr(it, "product_name", None),
            )
            continue

        sp = SoldProduct(
            original_product_id=getattr(it, "product_id", None),
            name=getattr(it, "product_name", None) or getattr(it, "name", None) or "Položka",
            price=f"{price_dec:.2f}",
            quantity=int(getattr(it, "quantity", 1) or 1),
            customer_name=getattr(order, "customer_name", None),
            customer_email=getattr(order, "customer_email", None),
            customer_address=getattr(order, "customer_address", None),
            note=base_note,
            payment_type=marker,
            sold_at=datetime.utcnow(),
        )
        db.session.add(sp)
        created += 1

    if created:
        db.session.flush()
    return created

def _make_invoice_proxy(order: Order) -> _SoldProxy:
    """Složí souhrnný 'sold_product' pro celou objednávku (1 PDF, žádný spam)."""
    total_items, items_count = _sum_order_items(order)
    # pokud máš shipping v modelu Order, vem ho; jinak ho nech na invoicing (má fix 89 Kč)
    # shipping = _to_dec(getattr(order, "shipping_czk", 0))  # <- kdybys chtěl

    name = f"Objednávka #{order.id} – {items_count} položek"
    return _SoldProxy(
        id=order.id,
        order_id=order.id,
        created_at=getattr(order, "created_at", None),
        sold_at=datetime.utcnow(),
        buyer_name=getattr(order, "customer_name", None),
        email=getattr(order, "customer_email", None),
        address=getattr(order, "customer_address", None),
        note=getattr(order, "note", None),
        name=name,
        quantity=1.0,
        unit_price_czk=float(total_items),  # kompat. s _unit_price()
        total_czk=float(total_items),       # kompat. s _total()
        vs=getattr(order, "vs", None),
    )

def _send_invoice_email(order: Order, pdf_bytes: bytes, filename: str) -> None:
    recipient = getattr(order, "customer_email", None)
    if not recipient:
        return

    subject = f"Faktura k objednávce #{order.id}"
    body = (
        f"Dobrý den {getattr(order, 'customer_name', '')},\n\n"
        "děkujeme za Vaši objednávku. V příloze posíláme fakturu (PDF).\n"
        "V případě nesrovnalostí odpovězte prosím na tento e-mail.\n\n"
        "Hezký den,\nNáramková Móda"
    )
    attachments = [{
        "filename": filename,
        "content": pdf_bytes,
        "mimetype": "application/pdf",
    }]
    send_email(subject=subject, recipients=[recipient], body=body, attachments=attachments)

def _notify_telegram(order: Order) -> None:
    """
    Volitelné: pokud máš utilitu/servis na Telegram, zavolej ji tady.
    Nechávám prázdné, ať ti to nic nekazí.
    """
    try:
        # from backend.integrations.telegram import notify_paid  # příklad
        # notify_paid(order_id=order.id, total=..., vs=order.vs)
        pass
    except Exception:
        current_app.logger.exception("Telegram notifikace selhala")

# ---- veřejná API -----------------------------------------------------------

def on_order_marked_paid(order_id: int) -> dict:
    """
    Volat POUZE při přechodu objednávky do stavu 'paid' / 'zaplaceno'.
    1) doplní SoldProduct (idempotentně)
    2) vytvoří souhrnný objekt a vygeneruje 1 PDF přes build_invoice_pdf_bytes(...)
    3) odešle e-mailem fakturu
    4) (volitelně) pošle Telegram
    """
    order: Order | None = Order.query.get(order_id)
    if not order:
        return {"ok": False, "error": "Order not found"}

    # 1) SoldProduct
    created_rows = _ensure_sold_rows(order)

    try:
        if created_rows:
            db.session.commit()
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception("Commit po vytvoření sold_product selhal")
        return {"ok": False, "error": f"DB commit failed: {exc}"}

    # 2) PDF (souhrn celé objednávky do 1 dokladu)
    proxy = _make_invoice_proxy(order)
    pdf_bytes = build_invoice_pdf_bytes(proxy)
    filename = f"Invoice-Order-{order.id}.pdf"

    # 3) E-mail
    emailed = False
    try:
        _send_invoice_email(order, pdf_bytes, filename)
        emailed = True
    except Exception:
        current_app.logger.exception("Odeslání e-mailu s fakturou selhalo")

    # 4) Telegram (pokud máš)
    _notify_telegram(order)

    return {"ok": True, "sold_rows_created": created_rows, "emailed": emailed}
