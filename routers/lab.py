from datetime import datetime, timezone
import re

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from auth import require_role
from database import all_rows, get_db, get_lab_order, now, one

router = APIRouter(prefix="/lab", tags=["lab"])
templates = Jinja2Templates(directory="templates")


def parse_range(range_text: str | None):
    if not range_text:
        return None, None
    numbers = re.findall(r"-?\d+(?:\.\d+)?", range_text)
    if len(numbers) >= 2:
        low = float(numbers[0])
        high = float(numbers[1])
        return min(low, high), max(low, high)
    if len(numbers) == 1 and range_text.strip().startswith("<"):
        return None, float(numbers[0])
    if len(numbers) == 1 and range_text.strip().startswith(">"):
        return float(numbers[0]), None
    return None, None


def result_flag(value: str, normal_range: str | None) -> str | None:
    try:
        numeric_value = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    low, high = parse_range(normal_range)
    if low is not None and numeric_value < low:
        return "low"
    if high is not None and numeric_value > high:
        return "high"
    return "normal"


def item_normal_range(order_item):
    if order_item.order.patient.gender.value == "female":
        return order_item.test.female_normal_range
    return order_item.test.male_normal_range


@router.get("/orders", response_class=HTMLResponse)
async def lab_orders(request: Request, current_user=Depends(require_role(["admin", "laboratory"])), db=Depends(get_db)):
    rows = all_rows(
        db,
        """
        SELECT id FROM lab_orders
        WHERE status IN ('waiting_payment', 'paid', 'collected', 'resulted')
        ORDER BY created_at
        """,
    )
    orders = [get_lab_order(db, row.id) for row in rows]
    return templates.TemplateResponse("lab/orders.htm", {"request": request, "current_user": current_user, "active_page": "lab", "orders": orders})


@router.post("/orders/{order_id}/collect")
async def collect_sample(order_id: int, current_user=Depends(require_role(["admin", "laboratory"])), db=Depends(get_db)):
    db.execute("UPDATE lab_orders SET status = 'collected' WHERE id = ?", (order_id,))
    db.commit()
    return RedirectResponse(url="/lab/orders", status_code=302)


@router.get("/orders/{order_id}/results", response_class=HTMLResponse)
async def result_form(request: Request, order_id: int, current_user=Depends(require_role(["admin", "laboratory"])), db=Depends(get_db)):
    order = get_lab_order(db, order_id)
    if not order:
        return RedirectResponse(url="/lab/orders", status_code=302)
    for item in order.items:
        item.order = order
    return templates.TemplateResponse("lab/result_form.htm", {"request": request, "current_user": current_user, "active_page": "lab", "order": order})


@router.post("/orders/{order_id}/results")
async def save_results(
    order_id: int,
    result_value: list[str] = Form([]),
    item_id: list[str] = Form([]),
    current_user=Depends(require_role(["admin", "laboratory"])),
    db=Depends(get_db),
):
    order = get_lab_order(db, order_id)
    for item in order.items:
        item.order = order

    saved_item_ids = set()
    for raw_item_id, raw_value in zip(item_id, result_value):
        value = (raw_value or "").strip()
        if not raw_item_id or not value:
            continue
        order_item = next((item for item in order.items if item.id == int(raw_item_id)), None)
        flag = result_flag(value, item_normal_range(order_item))
        existing = one(db, "SELECT * FROM lab_results WHERE order_item_id = ?", (order_item.id,))
        if existing:
            db.execute(
                "UPDATE lab_results SET value = ?, flag = ?, entered_at = ?, entered_by = ? WHERE order_item_id = ?",
                (value, flag, now(), current_user.id, order_item.id),
            )
        else:
            db.execute(
                "INSERT INTO lab_results (order_item_id, value, flag, entered_at, entered_by) VALUES (?, ?, ?, ?, ?)",
                (order_item.id, value, flag, now(), current_user.id),
            )
        saved_item_ids.add(order_item.id)

    if all(item.result or item.id in saved_item_ids for item in order.items):
        db.execute("UPDATE lab_orders SET status = 'resulted', completed_at = ? WHERE id = ?", (now(), order_id))
    else:
        db.execute("UPDATE lab_orders SET status = 'collected' WHERE id = ?", (order_id,))
    db.commit()
    return RedirectResponse(url=f"/lab/orders/{order_id}/report", status_code=302)


@router.get("/orders/{order_id}/report", response_class=HTMLResponse)
async def report(request: Request, order_id: int, current_user=Depends(require_role(["admin", "laboratory", "doctor"])), db=Depends(get_db)):
    order = get_lab_order(db, order_id)
    if not order:
        return RedirectResponse(url="/lab/orders", status_code=302)
    return templates.TemplateResponse("lab/report.htm", {"request": request, "current_user": current_user, "active_page": "lab", "order": order})
