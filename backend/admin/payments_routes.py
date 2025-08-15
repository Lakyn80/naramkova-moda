# 📁 backend/admin/payments_routes.py
from __future__ import annotations
from datetime import datetime
from decimal import Decimal, InvalidOperation
from flask import request, render_template, redirect, Response, flash
from flask_login import login_required
from backend.extensions import db
from backend.admin.models import Payment, Order
from backend.admin import admin_bp  # stávající admin blueprint

def _parse_date(s: str | None):
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None

def _to_decimal(x) -> Decimal:
    try:
        return Decimal(str(x))
    except Exception:
        raise InvalidOperation()

@admin_bp.route("/payments", methods=["GET"])
@login_required
def admin_payments_index():
    """
    Seznam plateb s filtrem.
    GET parametry: vs, status (received|pending|refunded), from, to, limit
    """
    vs = (request.args.get("vs") or "").strip()
    status = (request.args.get("status") or "").strip()
    from_date = (request.args.get("from") or "").strip()
    to_date = (request.args.get("to") or "").strip()
    try:
        limit = int(request.args.get("limit") or 100)
    except ValueError:
        limit = 100
    limit = max(1, min(limit, 500))

    q = Payment.query
    if vs:
        q = q.filter(Payment.vs == vs)
    if status:
        q = q.filter(Payment.status == status)

    dfrom = _parse_date(from_date)
    dto = _parse_date(to_date)
    if dfrom:
        q = q.filter(Payment.received_at >= dfrom)
    if dto:
        dto = dto.replace(hour=23, minute=59, second=59, microsecond=999999)
        q = q.filter(Payment.received_at <= dto)

    payments = (
        q.order_by(Payment.received_at.desc(), Payment.id.desc())
        .limit(limit)
        .all()
    )

    # mapování objednávek podle VS (pro odkaz)
    orders_by_vs = {}
    if payments:
        vs_list = list({p.vs for p in payments if p.vs})
        if vs_list:
            for o in Order.query.filter(Order.vs.in_(vs_list)).all():
                orders_by_vs[o.vs] = o

    # ⬇⬇⬇ JEDINÁ ZMĚNA: renderujeme z global templates: backend/templates/admin/payments/index.html
    return render_template(
        "admin/payments/index.html",
        payments=payments,
        orders_by_vs=orders_by_vs,
        vs=vs,
        status=status,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
    )

@admin_bp.route("/payments/add", methods=["POST"])
@login_required
def admin_payments_add():
    """
    Ruční přidání/označení platby.
    Pokud existuje objednávka se stejným VS a status je 'received' → objednávka = 'paid'.
    """
    vs = (request.form.get("vs") or "").strip()
    amount_raw = (request.form.get("amountCzk") or "").strip()
    reference = (request.form.get("reference") or "").strip()
    status = (request.form.get("status") or "received").strip() or "received"

    if not vs:
        flash("Chybí VS.", "danger")
        return redirect("/admin/payments")

    try:
        amount = _to_decimal(amount_raw)
        if amount < 0:
            raise InvalidOperation()
    except InvalidOperation:
        flash("Neplatná částka.", "danger")
        return redirect("/admin/payments")

    p = Payment(
        vs=vs,
        amount_czk=amount,
        reference=reference,
        status=status,
        received_at=datetime.utcnow(),
    )
    db.session.add(p)

    # spáruj s objednávkou
    order = Order.query.filter_by(vs=vs).first()
    if order and status == "received":
        order.status = "paid"

    db.session.commit()
    flash("Platba uložena.", "success")
    return redirect(f"/admin/payments?vs={vs}")

@admin_bp.route("/payments/<int:payment_id>/status", methods=["POST"])
@login_required
def admin_payments_update_status(payment_id: int):
    """
    Změna statusu jedné platby.
    Při 'received' přepne případnou objednávku na 'paid'.
    """
    p = Payment.query.get_or_404(payment_id)
    new_status = (request.form.get("status") or "").strip()
    if new_status not in {"received", "pending", "refunded"}:
        flash("Neplatný status.", "danger")
        return redirect("/admin/payments")

    p.status = new_status
    if new_status == "received":
        order = Order.query.filter_by(vs=p.vs).first()
        if order:
            order.status = "paid"

    db.session.commit()
    flash("Status platby aktualizován.", "success")
    return redirect(f"/admin/payments?vs={p.vs}")

@admin_bp.route("/payments/<int:payment_id>/link", methods=["POST"])
@login_required
def admin_payments_link_order(payment_id: int):
    """
    Ruční spárování (přepne objednávku na 'paid', je-li platba 'received').
    """
    p = Payment.query.get_or_404(payment_id)
    order = Order.query.filter_by(vs=p.vs).first()
    if order:
        if (p.status or "pending") == "received":
            order.status = "paid"
        db.session.commit()
        flash(f"Platba spárována s objednávkou #{order.id}.", "success")
    else:
        flash("Objednávka s tímto VS neexistuje.", "warning")
    return redirect(f"/admin/payments?vs={p.vs}")

@admin_bp.route("/payments/export.csv", methods=["GET"])
@login_required
def admin_payments_export_csv():
    """
    Export filtrového seznamu plateb do CSV.
    """
    vs = (request.args.get("vs") or "").strip()
    status = (request.args.get("status") or "").strip()
    from_date = (request.args.get("from") or "").strip()
    to_date = (request.args.get("to") or "").strip()
    try:
        limit = int(request.args.get("limit") or 100)
    except ValueError:
        limit = 100
    limit = max(1, min(limit, 500))

    q = Payment.query
    if vs:
        q = q.filter(Payment.vs == vs)
    if status:
        q = q.filter(Payment.status == status)

    dfrom = _parse_date(from_date)
    dto = _parse_date(to_date)
    if dfrom:
        q = q.filter(Payment.received_at >= dfrom)
    if dto:
        dto = dto.replace(hour=23, minute=59, second=59, microsecond=999999)
        q = q.filter(Payment.received_at <= dto)

    pays = q.order_by(Payment.received_at.desc(), Payment.id.desc()).limit(limit).all()

    # CSV
    import io, csv
    sio = io.StringIO()
    w = csv.writer(sio, lineterminator="\n")
    w.writerow(["id", "vs", "amount_czk", "reference", "status", "received_at", "order_id"])

    orders_by_vs = {}
    if pays:
        vs_list = list({p.vs for p in pays if p.vs})
        if vs_list:
            for o in Order.query.filter(Order.vs.in_(vs_list)).all():
                orders_by_vs[o.vs] = o.id

    for p in pays:
        w.writerow([
            p.id,
            p.vs or "",
            f"{float(p.amount_czk or 0):.2f}",
            p.reference or "",
            p.status or "",
            (p.received_at.isoformat(sep=" ", timespec="seconds") if p.received_at else ""),
            orders_by_vs.get(p.vs, "") if p.vs else "",
        ])

    out = sio.getvalue().encode("utf-8-sig")
    filename = f"payments_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        out,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
