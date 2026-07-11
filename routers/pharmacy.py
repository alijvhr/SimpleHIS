from decimal import Decimal
from typing import List
from datetime import datetime, timezone

from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from auth import require_role
from database import all_rows, get_db, get_drug, get_patient, get_prescription, now, one, stock_for_drug

router = APIRouter(prefix="/pharmacy", tags=["pharmacy"])
templates = Jinja2Templates(directory="templates")


def get_drug_stock(db, drug_id: int) -> int:
    return stock_for_drug(db, drug_id)


def prescription_stock_summary(db, prescription) -> dict:
    warnings = []
    lines = []
    for item in prescription.items:
        current_stock = get_drug_stock(db, item.drug_id)
        shortage = max(0, item.quantity - current_stock)
        lines.append({
            "item": item,
            "current_stock": current_stock,
            "shortage": shortage,
            "is_low_after_dispense": current_stock - item.quantity < item.drug.min_threshold,
        })
        if shortage:
            warnings.append(f"{item.drug.name}: موجودی فعلی {current_stock}، نیاز {item.quantity}")
    return {"lines": lines, "warnings": warnings, "ready": not warnings and bool(prescription.items)}


def payable_prescription_rows(db, prescriptions) -> list[dict]:
    return [
        {"prescription": prescription, "item_count": len(prescription.items), "stock": prescription_stock_summary(db, prescription)}
        for prescription in prescriptions
    ]


def prescriptions_by_status(db, status):
    rows = all_rows(db, "SELECT id FROM prescriptions WHERE status = ? ORDER BY created_at", (status,))
    return [get_prescription(db, row.id) for row in rows]


@router.get("/inventory", response_class=HTMLResponse)
async def inventory(request: Request, current_user=Depends(require_role(["admin", "pharmacy"])), db=Depends(get_db)):
    drugs = all_rows(db, "SELECT * FROM drugs ORDER BY name")
    return templates.TemplateResponse(
        "pharmacy/inventory.htm",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "inventory",
            "drugs": [{"drug": drug, "stock": get_drug_stock(db, drug.id)} for drug in drugs],
        },
    )


@router.get("/drug/new", response_class=HTMLResponse)
async def new_drug_form(request: Request, current_user=Depends(require_role(["admin", "pharmacy"]))):
    return templates.TemplateResponse(
        "pharmacy/drug_form.htm",
        {"request": request, "current_user": current_user, "active_page": "inventory", "drug": None},
    )


@router.post("/drug/new")
async def create_drug(
    request: Request,
    name: str = Form(...),
    manufacturer: str = Form(...),
    form: str = Form(...),
    dosage: str = Form(...),
    price: float = Form(...),
    min_threshold: int = Form(...),
    default_instructions: str = Form(...),
    initial_stock: int = Form(0),
    current_user=Depends(require_role(["admin", "pharmacy"])),
    db=Depends(get_db),
):
    cur = db.execute(
        """
        INSERT INTO drugs (name, manufacturer, form, dosage, price, min_threshold, default_instructions, created_at, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (name, manufacturer, form, dosage, price, min_threshold, default_instructions, now(), current_user.id),
    )
    if initial_stock > 0:
        db.execute(
            "INSERT INTO stock_transactions (drug_id, quantity_change, reason, created_at, created_by) VALUES (?, ?, ?, ?, ?)",
            (cur.lastrowid, initial_stock, "موجودی اولیه", now(), current_user.id),
        )
    db.commit()
    return RedirectResponse(url="/pharmacy/inventory", status_code=302)


@router.get("/drug/{drug_id}/edit", response_class=HTMLResponse)
async def edit_drug_form(request: Request, drug_id: int, current_user=Depends(require_role(["admin", "pharmacy"])), db=Depends(get_db)):
    return templates.TemplateResponse(
        "pharmacy/drug_form.htm",
        {"request": request, "current_user": current_user, "active_page": "inventory", "drug": get_drug(db, drug_id)},
    )


@router.post("/drug/{drug_id}/edit")
async def update_drug(
    request: Request,
    drug_id: int,
    name: str = Form(...),
    manufacturer: str = Form(...),
    form: str = Form(...),
    dosage: str = Form(...),
    price: float = Form(...),
    min_threshold: int = Form(...),
    default_instructions: str = Form(...),
    current_user=Depends(require_role(["admin", "pharmacy"])),
    db=Depends(get_db),
):
    db.execute(
        """
        UPDATE drugs SET name = ?, manufacturer = ?, form = ?, dosage = ?, price = ?, min_threshold = ?, default_instructions = ?
        WHERE id = ?
        """,
        (name, manufacturer, form, dosage, price, min_threshold, default_instructions, drug_id),
    )
    db.commit()
    return RedirectResponse(url="/pharmacy/inventory", status_code=302)


@router.get("/restock", response_class=HTMLResponse)
async def restock_form(request: Request, current_user=Depends(require_role(["admin", "pharmacy"])), db=Depends(get_db)):
    return templates.TemplateResponse(
        "pharmacy/restock.htm",
        {"request": request, "current_user": current_user, "active_page": "inventory", "drugs": all_rows(db, "SELECT * FROM drugs ORDER BY name")},
    )


@router.post("/restock")
async def restock(
    request: Request,
    drug_id: int = Form(...),
    quantity: int = Form(...),
    reason: str = Form(...),
    current_user=Depends(require_role(["admin", "pharmacy"])),
    db=Depends(get_db),
):
    db.execute(
        "INSERT INTO stock_transactions (drug_id, quantity_change, reason, created_at, created_by) VALUES (?, ?, ?, ?, ?)",
        (drug_id, quantity, reason, now(), current_user.id),
    )
    db.commit()
    return RedirectResponse(url="/pharmacy/inventory", status_code=302)


@router.get("/manual-prescription", response_class=HTMLResponse)
async def manual_prescription_form(request: Request, national_id: str = None, current_user=Depends(require_role(["admin", "pharmacy"])), db=Depends(get_db)):
    patient = one(db, "SELECT * FROM patients WHERE national_id = ?", (national_id,)) if national_id else None
    return templates.TemplateResponse(
        "pharmacy/manual_prescription.htm",
        {"request": request, "current_user": current_user, "active_page": "manual_prescription", "patient": patient},
    )


@router.post("/manual-prescription")
async def create_manual_prescription(
    request: Request,
    patient_id: int = Form(...),
    total_amount: float = Form(0),
    drug_id: List[str] = Form([]),
    quantity: List[str] = Form([]),
    instructions: List[str] = Form(...),
    current_user=Depends(require_role(["admin", "pharmacy"])),
    db=Depends(get_db),
):
    rows = []
    total = Decimal("0")
    for index, raw_drug_id in enumerate(drug_id):
        if not raw_drug_id:
            continue
        drug = get_drug(db, int(raw_drug_id))
        item_quantity = max(1, int(quantity[index] if index < len(quantity) else 1))
        item_instructions = instructions[index] if index < len(instructions) else ""
        rows.append((drug, item_quantity, (item_instructions or drug.default_instructions or "").strip()))
        total += Decimal(str(drug.price or 0)) * item_quantity

    cur = db.execute(
        """
        INSERT INTO prescriptions (patient_id, admission_id, is_manual, total_amount, status, created_at, created_by)
        VALUES (?, NULL, 1, ?, 'waiting_payment', ?, ?)
        """,
        (patient_id, str(total), now(), current_user.id),
    )
    for drug, item_quantity, item_instructions in rows:
        db.execute(
            "INSERT INTO prescription_items (prescription_id, drug_id, quantity, instructions) VALUES (?, ?, ?, ?)",
            (cur.lastrowid, drug.id, item_quantity, item_instructions or "طبق دستور"),
        )
    db.commit()
    return RedirectResponse(url="/reception/cashier", status_code=302)


@router.get("/dispense", response_class=HTMLResponse)
async def dispense_list(request: Request, current_user=Depends(require_role(["admin", "pharmacy"])), db=Depends(get_db)):
    prescriptions = prescriptions_by_status(db, "paid")
    return templates.TemplateResponse(
        "pharmacy/dispense.htm",
        {"request": request, "current_user": current_user, "active_page": "dispense", "prescriptions": prescriptions, "prescription_rows": payable_prescription_rows(db, prescriptions)},
    )


@router.get("/dispense/{prescription_id}", response_class=HTMLResponse)
async def dispense_detail(request: Request, prescription_id: int, current_user=Depends(require_role(["admin", "pharmacy"])), db=Depends(get_db)):
    prescription = get_prescription(db, prescription_id)
    if not prescription:
        return RedirectResponse(url="/pharmacy/dispense", status_code=302)
    stock = prescription_stock_summary(db, prescription)
    return templates.TemplateResponse(
        "pharmacy/dispense_detail.htm",
        {"request": request, "current_user": current_user, "active_page": "dispense", "prescription": prescription, "stock_warnings": stock["warnings"], "stock_lines": stock["lines"], "can_dispense": prescription.status == "paid" and stock["ready"]},
    )


@router.post("/dispense/{prescription_id}/complete")
async def complete_dispense(request: Request, prescription_id: int, current_user=Depends(require_role(["admin", "pharmacy"])), db=Depends(get_db)):
    prescription = get_prescription(db, prescription_id)
    if not prescription or prescription.status != "paid":
        return RedirectResponse(url="/pharmacy/dispense", status_code=302)

    for item in prescription.items:
        db.execute(
            "INSERT INTO stock_transactions (drug_id, quantity_change, reason, created_at, created_by) VALUES (?, ?, ?, ?, ?)",
            (item.drug_id, -item.quantity, f"تحویل نسخه {prescription_id}", now(), current_user.id),
        )
    db.execute(
        "UPDATE prescriptions SET status = 'dispensed', dispensed_at = ?, dispensed_by = ? WHERE id = ?",
        (now(), current_user.id, prescription_id),
    )
    db.commit()
    return RedirectResponse(url="/pharmacy/dispense", status_code=302)


@router.get("/search", response_class=HTMLResponse)
async def search_prescriptions(
    request: Request,
    prescription_id: int = None,
    national_id: str = None,
    current_user=Depends(require_role(["admin", "pharmacy"])),
    db=Depends(get_db),
):
    prescriptions = []
    if prescription_id:
        prescription = get_prescription(db, prescription_id)
        prescriptions = [prescription] if prescription else []
    elif national_id:
        rows = all_rows(
            db,
            """
            SELECT p.id FROM prescriptions p
            JOIN patients pt ON pt.id = p.patient_id
            WHERE pt.national_id = ?
            ORDER BY p.created_at DESC
            """,
            (national_id,),
        )
        prescriptions = [get_prescription(db, row.id) for row in rows]
    return templates.TemplateResponse(
        "pharmacy/search_prescriptions.htm",
        {"request": request, "current_user": current_user, "active_page": "search_prescriptions", "prescriptions": prescriptions, "prescription_id": prescription_id, "national_id": national_id},
    )


@router.get("/prescription/{prescription_id}", response_class=HTMLResponse)
async def view_prescription(request: Request, prescription_id: int, current_user=Depends(require_role(["admin", "pharmacy"])), db=Depends(get_db)):
    prescription = get_prescription(db, prescription_id)
    if not prescription:
        return RedirectResponse(url="/pharmacy/search", status_code=302)
    stock = prescription_stock_summary(db, prescription)
    return templates.TemplateResponse(
        "pharmacy/dispense_detail.htm",
        {"request": request, "current_user": current_user, "active_page": "search_prescriptions", "prescription": prescription, "stock_warnings": stock["warnings"], "stock_lines": stock["lines"], "can_dispense": prescription.status == "paid" and stock["ready"]},
    )
