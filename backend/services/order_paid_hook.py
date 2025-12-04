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
    created = 0
    existing = {(s.product_id, s.order_id) for s in SoldProduct.query.filter_by(order_id=order.id).all()}
    items: list[OrderItem] = OrderItem.query.filter_by(order_id=order.id).all()

    for it in items:
        key = (it.product_id, order.id)
        if key in existing:
            continue
        s = SoldProduct(
            product_id=it.product_id,
            order_id=order.id,
            quantity=it.quantity,
            price=it.price,
            sold_at=datetime.utcnow(),
            buyer_name=order.name,
            buyer_email=order.email,
            vs=getattr(order, "vs", None),
        )
        db.session.add(s)
        created += 1

    if created:
        db.session.flush()
    return created

def _make_invoice_proxy(order: Order) -> _SoldProxy:
    """Složí souhrnný 'sold_product' pro celou objednávku (1 PDF, žádný spam)."""
    total_items, items_count = _sum_order_items(order)
    # pokud máš shipping v modelu Order, vem ho; jinak ho nech na invoicing (má fix 89 Kč)
    # shipping = _to_dec(getattr(order, "shipping_czk", 0))  # <- kdybys chtěl

    name = f"Objednávka #{order.id} — {items_count} položek"
    return _SoldProxy(
        id=order.id,
        order_id=order.id,
        created_at=getattr(order, "created_at", None),
        sold_at=datetime.utcnow(),
        buyer_name=order.name,
        email=order.email,
        address=order.address,
        note=getattr(order, "note", None),
        name=name,
        quantity=1.0,
        unit_price_czk=float(total_items),  # kompat. s _unit_price()
        total_czk=float(total_items),       # kompat. s _total()
        vs=getattr(order, "vs", None),
    )

def _send_invoice_email(order: Order, pdf_bytes: bytes, filename: str) -> None:
    subject = f"Faktura k objednávce #{order.id}"
    body = (
        f"Dobrý den {order.name or ''},\n\n"
        "děkujeme za Vaši objednávku. V příloze posíláme fakturu (PDF).\n"
        "V případě nesrovnalostí odpovězte prosím na tento e-mail.\n\n"
        "Hezký den,\nNáramková Móda"
    )
    attachments = [{
        "filename": filename,
        "content": pdf_bytes,
        "mimetype": "application/pdf",
    }]
    send_email(to=order.email, subject=subject, body=body, attachments=attachments)

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

    # 2) PDF (souhrn celé objednávky do 1 dokladu)
    proxy = _make_invoice_proxy(order)
    pdf_bytes = build_invoice_pdf_bytes(proxy)
    filename = f"Invoice-Order-{order.id}.pdf"

    # 3) E-mail
    try:
        _send_invoice_email(order, pdf_bytes, filename)
    except Exception:
        current_app.logger.exception("Odeslání e-mailu s fakturou selhalo")

    # 4) Telegram (pokud máš)
    _notify_telegram(order)

    return {"ok": True, "sold_rows_created": created_rows, "emailed": bool(order.email)}
