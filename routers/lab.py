import re

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from auth import require_role
from database import all_rows, get_db, get_lab_order, now, one

router = APIRouter(prefix="/lab", tags=["lab"])
templates = Jinja2Templates(directory="templates")


def parse_range(range_text: str | None):
    if not range_text:
        return None, None
    text = str(range_text).strip()
    number = r"[-+]?\d+(?:\.\d+)?"

    upper_match = re.match(rf"^(?:<=|<|\u2264)\s*({number})", text)
    if upper_match:
        return None, float(upper_match.group(1))

    lower_match = re.match(rf"^(?:>=|>|\u2265)\s*({number})", text)
    if lower_match:
        return float(lower_match.group(1)), None

    range_match = re.search(rf"({number})\s*(?:-|\u2013|\u2014|\bto\b)\s*({number})", text, re.IGNORECASE)
    if range_match:
        low = float(range_match.group(1))
        high = float(range_match.group(2))
        return min(low, high), max(low, high)

    numbers = re.findall(number, text)
    if len(numbers) >= 2:
        low = float(numbers[0])
        high = float(numbers[1])
        return min(low, high), max(low, high)
    return None, None


def result_flag(value: str, normal_range: str | None) -> str | None:
    try:
        numeric_value = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    low, high = parse_range(normal_range)
    if low is None and high is None:
        return None
    if low is not None and numeric_value < low:
        return "low"
    if high is not None and numeric_value > high:
        return "high"
    return "normal"


def item_normal_range(order_item):
    if order_item.order.patient.gender.value == "female":
        return order_item.test.female_normal_range
    return order_item.test.male_normal_range


def result_form_context(request: Request, current_user, order, messages=None):
    return {
        "request": request,
        "current_user": current_user,
        "active_page": "lab",
        "order": order,
        "messages": messages or [],
    }


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
    return templates.TemplateResponse("lab/result_form.htm", result_form_context(request, current_user, order))


@router.post("/orders/{order_id}/results")
async def save_results(
    request: Request,
    order_id: int,
    current_user=Depends(require_role(["admin", "laboratory"])),
    db=Depends(get_db),
):
    order = get_lab_order(db, order_id)
    if not order:
        return RedirectResponse(url="/lab/orders", status_code=302)
    for item in order.items:
        item.order = order

    form = await request.form()
    submitted_results = {
        item.id: form.get(f"result_value_{item.id}", "")
        for item in order.items
        if f"result_value_{item.id}" in form
    }

    if not submitted_results:
        item_ids = form.getlist("item_id[]") or form.getlist("item_id")
        result_values = form.getlist("result_value[]") or form.getlist("result_value")
        order_items_by_id = {item.id: item for item in order.items}
        for raw_item_id, raw_value in zip(item_ids, result_values):
            try:
                item_id = int(raw_item_id)
            except (TypeError, ValueError):
                continue
            if item_id in order_items_by_id:
                submitted_results[item_id] = raw_value

    if not submitted_results:
        return templates.TemplateResponse(
            "lab/result_form.htm",
            result_form_context(
                request,
                current_user,
                order,
                [{"type": "warning", "text": "No lab result fields were received. Please reload the page and try again."}],
            ),
        )

    saved_item_ids = set()
    for item in order.items:
        raw_value = submitted_results.get(item.id, "")
        value = (raw_value or "").strip()
        if not value:
            continue
        flag = result_flag(value, item_normal_range(item))
        existing = one(db, "SELECT * FROM lab_results WHERE order_item_id = ?", (item.id,))
        if existing:
            db.execute(
                "UPDATE lab_results SET value = ?, flag = ?, entered_at = ?, entered_by = ? WHERE order_item_id = ?",
                (value, flag, now(), current_user.id, item.id),
            )
        else:
            db.execute(
                "INSERT INTO lab_results (order_item_id, value, flag, entered_at, entered_by) VALUES (?, ?, ?, ?, ?)",
                (item.id, value, flag, now(), current_user.id),
            )
        saved_item_ids.add(item.id)

    if not saved_item_ids:
        return templates.TemplateResponse(
            "lab/result_form.htm",
            result_form_context(
                request,
                current_user,
                order,
                [{"type": "warning", "text": "No result values were saved. Enter at least one result value before saving."}],
            ),
        )

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
