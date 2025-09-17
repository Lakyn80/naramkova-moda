from datetime import datetime
from flask import request, render_template, redirect, url_for, flash
from backend.extensions import db
from . import admin_bp
from backend.admin.models import Payment, Order

# jediný helper, který potřebujeme: automatické poslání faktury
from backend.admin.sold_routes import send_invoice_for_order

# ⬇️ DOPLNĚNO: hook, který vytvoří záznam(y) v Prodaných a (případně) pošle FA
from backend.services.order_paid_hook import on_order_marked_paid

ALLOWED_STATUSES = ("pending", "received", "failed", "canceled", "refunded")

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

    p.status = new_status
    if new_status == "received" and getattr(p, "received_at", None) is None:
        try:
            p.received_at = datetime.utcnow()
        except Exception:
            pass

    o = db.session.query(Order).filter_by(vs=p.vs).first()
    if o:
        if new_status == "received":
            o.status = "paid"
        elif o.status != "paid":
            o.status = "awaiting_payment"

    db.session.commit()

    # Automatické vytvoření záznamu v „Prodané“ a odeslání faktury (pokud to hook řeší)
    if new_status == "received" and o:
        try:
            res = on_order_marked_paid(o.id)  # vytvoří sold rows, email, (telegram jen v hooku)
        except Exception:
            res = None

        # Fallback: pokud hook NEposlal e-mail s FA, pošli původní cestou
        if not (isinstance(res, dict) and res.get("emailed")):
            try:
                send_invoice_for_order(o.id)
            except Exception:
                pass

    flash(f"Status platby #{p.id} změněn na '{new_status}'.", "success")
    return redirect(url_for("admin.admin_payments_index"))

