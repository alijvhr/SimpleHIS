from datetime import datetime, timezone
import re

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from auth import require_role
from database import get_db
from models.lab_order import LabOrder, LabOrderStatus
from models.lab_result import LabResult
from models.user import User

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
    patient_gender = order_item.order.patient.gender.value
    if patient_gender == "female":
        return order_item.test.female_normal_range
    return order_item.test.male_normal_range


@router.get("/orders", response_class=HTMLResponse)
async def lab_orders(
    request: Request,
    current_user: User = Depends(require_role(["admin", "laboratory"])),
    db: Session = Depends(get_db),
):
    orders = db.query(LabOrder).filter(
        LabOrder.status.in_([
            LabOrderStatus.waiting_payment,
            LabOrderStatus.paid,
            LabOrderStatus.collected,
            LabOrderStatus.resulted,
        ])
    ).order_by(LabOrder.created_at.asc()).all()

    return templates.TemplateResponse(
        "lab/orders.htm",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "lab",
            "orders": orders,
        },
    )


@router.post("/orders/{order_id}/collect")
async def collect_sample(
    order_id: int,
    current_user: User = Depends(require_role(["admin", "laboratory"])),
    db: Session = Depends(get_db),
):
    order = db.query(LabOrder).filter(LabOrder.id == order_id).first()
    if order and order.status == LabOrderStatus.paid:
        order.status = LabOrderStatus.collected
        db.commit()
    return RedirectResponse(url="/lab/orders", status_code=302)


@router.get("/orders/{order_id}/results", response_class=HTMLResponse)
async def result_form(
    request: Request,
    order_id: int,
    current_user: User = Depends(require_role(["admin", "laboratory"])),
    db: Session = Depends(get_db),
):
    order = db.query(LabOrder).filter(LabOrder.id == order_id).first()
    if not order:
        return RedirectResponse(url="/lab/orders", status_code=302)

    return templates.TemplateResponse(
        "lab/result_form.htm",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "lab",
            "order": order,
        },
    )


@router.post("/orders/{order_id}/results")
async def save_results(
    order_id: int,
    result_value: list[str] = Form([]),
    item_id: list[str] = Form([]),
    current_user: User = Depends(require_role(["admin", "laboratory"])),
    db: Session = Depends(get_db),
):
    order = db.query(LabOrder).filter(LabOrder.id == order_id).first()
    if not order or order.status not in [LabOrderStatus.paid, LabOrderStatus.collected, LabOrderStatus.resulted]:
        return RedirectResponse(url="/lab/orders", status_code=302)

    saved_item_ids = set()
    for raw_item_id, raw_value in zip(item_id, result_value):
        value = (raw_value or "").strip()
        if not raw_item_id or not value:
            continue
        order_item = next((item for item in order.items if item.id == int(raw_item_id)), None)
        if not order_item:
            continue
        flag = result_flag(value, item_normal_range(order_item))
        if order_item.result:
            order_item.result.value = value
            order_item.result.flag = flag
            order_item.result.entered_at = datetime.now(timezone.utc)
            order_item.result.entered_by = current_user.id
        else:
            db.add(LabResult(
                order_item_id=order_item.id,
                value=value,
                flag=flag,
                entered_by=current_user.id,
            ))
        saved_item_ids.add(order_item.id)

    if all(item.result or item.id in saved_item_ids for item in order.items):
        order.status = LabOrderStatus.resulted
        order.completed_at = datetime.now(timezone.utc)
    elif order.status == LabOrderStatus.paid:
        order.status = LabOrderStatus.collected

    db.commit()
    return RedirectResponse(url=f"/lab/orders/{order_id}/report", status_code=302)


@router.get("/orders/{order_id}/report", response_class=HTMLResponse)
async def report(
    request: Request,
    order_id: int,
    current_user: User = Depends(require_role(["admin", "laboratory", "doctor"])),
    db: Session = Depends(get_db),
):
    order = db.query(LabOrder).filter(LabOrder.id == order_id).first()
    if not order:
        return RedirectResponse(url="/lab/orders", status_code=302)

    return templates.TemplateResponse(
        "lab/report.htm",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "lab",
            "order": order,
        },
    )
