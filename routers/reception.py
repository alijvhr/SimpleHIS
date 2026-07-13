from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, date, timezone

from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from auth import require_role
from config import get_admission_price
from database import all_rows, get_admission, get_db, get_lab_order, get_lab_test, get_patient, get_prescription, now, one, stock_for_drug

router = APIRouter(prefix="/reception", tags=["reception"])
templates = Jinja2Templates(directory="templates")

INSURANCE_PLANS = {
    "none": {"title": "آزاد", "coverage_percent": 0},
    "social": {"title": "تامین اجتماعی", "coverage_percent": 70},
    "health": {"title": "سلامت", "coverage_percent": 80},
    "armed": {"title": "نیروهای مسلح", "coverage_percent": 90},
    "supplemental": {"title": "تکمیلی", "coverage_percent": 95},
}


def money(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def get_admission_invoice(admission_type: str, insurance_provider: str = "none") -> dict:
    plan = INSURANCE_PLANS.get(insurance_provider, INSURANCE_PLANS["none"])
    gross_amount = money(get_admission_price(admission_type))
    coverage_amount = money(gross_amount * Decimal(plan["coverage_percent"]) / Decimal(100))
    patient_amount = max(Decimal("0"), gross_amount - coverage_amount)
    return {
        "insurance_provider": insurance_provider if insurance_provider in INSURANCE_PLANS else "none",
        "insurance_title": plan["title"],
        "coverage_percent": plan["coverage_percent"],
        "gross_amount": gross_amount,
        "coverage_amount": coverage_amount,
        "patient_amount": patient_amount,
    }


def receipt_number(prefix: str, item_id: int) -> str:
    return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{item_id}"


def cashier_messages(request: Request):
    if request.query_params.get("paid") == "1":
        return [{"type": "success", "text": "پرداخت با موفقیت ثبت شد و پرونده به مرحله بعدی ارسال شد."}]
    if request.query_params.get("cancelled") == "1":
        return [{"type": "warning", "text": "درخواست با موفقیت لغو شد."}]
    return []


def parse_form_ids(values) -> list[int]:
    return [int(value) for value in values if value]


def prescription_payment_rows(db, prescriptions) -> list[dict]:
    rows = []
    for prescription in prescriptions:
        shortages = []
        for item in prescription.items:
            current_stock = stock_for_drug(db, item.drug_id)
            if current_stock < item.quantity:
                shortages.append(f"{item.drug.name}: {current_stock}/{item.quantity}")
        rows.append({
            "prescription": prescription,
            "item_count": len(prescription.items),
            "stock_ready": not shortages and bool(prescription.items),
            "shortages": shortages,
        })
    return rows


@router.get("/patients", response_class=HTMLResponse)
async def patients_list(
    request: Request,
    national_id: str = None,
    phone: str = None,
    current_user=Depends(require_role(["admin", "reception"])),
    db=Depends(get_db),
):
    patients = []
    if national_id:
        patients = all_rows(db, "SELECT * FROM patients WHERE national_id LIKE ?", (f"%{national_id}%",))
    elif phone:
        patients = all_rows(db, "SELECT * FROM patients WHERE phone LIKE ?", (f"%{phone}%",))
    return templates.TemplateResponse(
        "reception/patients.htm",
        {"request": request, "current_user": current_user, "active_page": "patients", "patients": patients, "search_query": national_id, "phone_query": phone},
    )


@router.get("/patients/new", response_class=HTMLResponse)
async def new_patient_form(request: Request, current_user=Depends(require_role(["admin", "reception"]))):
    return templates.TemplateResponse(
        "reception/patient_form.htm",
        {"request": request, "current_user": current_user, "active_page": "patients", "patient": None},
    )


@router.get("/patients/{patient_id}", response_class=HTMLResponse)
async def patient_detail(
    request: Request,
    patient_id: int,
    current_user=Depends(require_role(["admin", "reception"])),
    db=Depends(get_db),
):
    patient = get_patient(db, patient_id)
    if not patient:
        return RedirectResponse(url="/reception/patients", status_code=302)

    admissions = [
        get_admission(db, row.id)
        for row in all_rows(db, "SELECT id FROM admissions WHERE patient_id = ? ORDER BY created_at DESC", (patient_id,))
    ]
    prescriptions = [
        get_prescription(db, row.id)
        for row in all_rows(db, "SELECT id FROM prescriptions WHERE patient_id = ? ORDER BY created_at DESC", (patient_id,))
    ]
    lab_orders = [
        get_lab_order(db, row.id)
        for row in all_rows(db, "SELECT id FROM lab_orders WHERE patient_id = ? ORDER BY created_at DESC", (patient_id,))
    ]

    return templates.TemplateResponse(
        "reception/patient_detail.htm",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "patients",
            "patient": patient,
            "admissions": admissions,
            "prescriptions": prescriptions,
            "lab_orders": lab_orders,
        },
    )


@router.post("/patients/new")
async def create_patient(
    request: Request,
    national_id: str = Form(...),
    full_name: str = Form(...),
    phone: str = Form(...),
    birth_date: date = Form(...),
    gender: str = Form(...),
    address: str = Form(None),
    current_user=Depends(require_role(["admin", "reception"])),
    db=Depends(get_db),
):
    cur = db.execute(
        """
        INSERT INTO patients (national_id, full_name, phone, birth_date, gender, address, created_at, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (national_id, full_name, phone, str(birth_date), gender, address, now(), current_user.id),
    )
    db.commit()
    return RedirectResponse(url=f"/reception/admit?patient_id={cur.lastrowid}", status_code=302)


@router.get("/admit", response_class=HTMLResponse)
async def admit_form(
    request: Request,
    patient_id: int = None,
    national_id: str = None,
    current_user=Depends(require_role(["admin", "reception"])),
    db=Depends(get_db),
):
    patient = get_patient(db, patient_id) if patient_id else None
    if national_id:
        patient = one(db, "SELECT * FROM patients WHERE national_id = ?", (national_id,))
    lab_tests = all_rows(db, "SELECT * FROM lab_tests WHERE is_active = 1 ORDER BY category, name")
    return templates.TemplateResponse(
        "reception/admit.htm",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "admit",
            "patient": patient,
            "searched_national_id": national_id or "",
            "patient_not_found": bool(national_id and not patient),
            "insurance_plans": INSURANCE_PLANS,
            "admission_prices": {
                "doctor": get_admission_price("doctor"),
                "laboratory": get_admission_price("laboratory"),
                "radiology": get_admission_price("radiology"),
            },
            "lab_tests": lab_tests,
            "messages": [],
        },
    )


@router.post("/admit")
async def create_admission(
    request: Request,
    patient_id: int = Form(...),
    admission_type: str = Form(...),
    description: str = Form(...),
    radiology_type: str = Form(None),
    current_user=Depends(require_role(["admin", "reception"])),
    db=Depends(get_db),
):
    status = "completed" if admission_type == "laboratory" else "waiting_payment"
    cur = db.execute(
        """
        INSERT INTO admissions (patient_id, admission_type, description, radiology_type, status, created_at, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (patient_id, admission_type, description, radiology_type if admission_type == "radiology" else None, status, now(), current_user.id),
    )
    admission_id = cur.lastrowid

    if admission_type == "laboratory":
        form = await request.form()
        lab_test_ids = parse_form_ids(form.getlist("lab_test_id"))
        tests = [get_lab_test(db, test_id) for test_id in lab_test_ids]
        total_amount = sum((Decimal(str(test.price or 0)) for test in tests), Decimal("0"))
        order = db.execute(
            """
            INSERT INTO lab_orders (patient_id, admission_id, total_amount, status, clinical_note, created_at, created_by)
            VALUES (?, ?, ?, 'waiting_payment', ?, ?, ?)
            """,
            (patient_id, admission_id, str(total_amount), description, now(), current_user.id),
        )
        for test in tests:
            db.execute(
                "INSERT INTO lab_order_items (order_id, test_id, price) VALUES (?, ?, ?)",
                (order.lastrowid, test.id, test.price or 0),
            )
    db.commit()
    return RedirectResponse(url="/reception/cashier", status_code=302)


@router.get("/cashier", response_class=HTMLResponse)
async def cashier(request: Request, current_user=Depends(require_role(["admin", "reception"])), db=Depends(get_db)):
    waiting_admissions = all_rows(db, "SELECT * FROM admissions WHERE status = 'waiting_payment' ORDER BY created_at")
    for admission in waiting_admissions:
        admission.patient = get_patient(db, admission.patient_id)
        admission.price = get_admission_price(admission.admission_type.value)
        admission.invoice = get_admission_invoice(admission.admission_type.value)

    prescription_ids = all_rows(db, "SELECT id FROM prescriptions WHERE status = 'waiting_payment' ORDER BY created_at")
    waiting_prescriptions = [get_prescription(db, row.id) for row in prescription_ids]

    lab_order_ids = all_rows(db, "SELECT id FROM lab_orders WHERE status = 'waiting_payment' ORDER BY created_at")
    waiting_lab_orders = [get_lab_order(db, row.id) for row in lab_order_ids]

    return templates.TemplateResponse(
        "reception/cashier.htm",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "cashier",
            "waiting_admissions": waiting_admissions,
            "waiting_prescriptions": waiting_prescriptions,
            "prescription_rows": prescription_payment_rows(db, waiting_prescriptions),
            "waiting_lab_orders": waiting_lab_orders,
            "insurance_plans": INSURANCE_PLANS,
            "messages": cashier_messages(request),
        },
    )


@router.post("/cashier/pay-admission")
async def pay_admission(
    request: Request,
    admission_id: int = Form(...),
    insurance_provider: str = Form("none"),
    current_user=Depends(require_role(["admin", "reception"])),
    db=Depends(get_db),
):
    admission = get_admission(db, admission_id)
    invoice = get_admission_invoice(admission.admission_type.value, insurance_provider)
    db.execute("UPDATE admissions SET status = 'paid', paid_at = ?, paid_by = ? WHERE id = ?", (now(), current_user.id, admission_id))
    db.execute(
        "INSERT INTO payments (payable_type, payable_id, amount, receipt_number, status, created_at, created_by) VALUES ('admission', ?, ?, ?, 'paid', ?, ?)",
        (admission_id, str(invoice["patient_amount"]), receipt_number("ADM", admission_id), now(), current_user.id),
    )
    db.commit()
    return RedirectResponse(url="/reception/cashier?paid=1", status_code=302)


@router.post("/cashier/cancel-admission")
async def cancel_admission(request: Request, admission_id: int = Form(...), current_user=Depends(require_role(["admin", "reception"])), db=Depends(get_db)):
    db.execute("UPDATE admissions SET status = 'cancelled' WHERE id = ?", (admission_id,))
    db.commit()
    return RedirectResponse(url="/reception/cashier?cancelled=1", status_code=302)


@router.post("/cashier/pay-prescription")
async def pay_prescription(request: Request, prescription_id: int = Form(...), current_user=Depends(require_role(["admin", "reception"])), db=Depends(get_db)):
    prescription = get_prescription(db, prescription_id)
    db.execute("UPDATE prescriptions SET status = 'paid' WHERE id = ?", (prescription_id,))
    db.execute(
        "INSERT INTO payments (payable_type, payable_id, amount, receipt_number, status, created_at, created_by) VALUES ('prescription', ?, ?, ?, 'paid', ?, ?)",
        (prescription_id, prescription.total_amount, receipt_number("RX", prescription_id), now(), current_user.id),
    )
    db.commit()
    return RedirectResponse(url="/reception/cashier?paid=1", status_code=302)


@router.post("/cashier/cancel-prescription")
async def cancel_prescription(request: Request, prescription_id: int = Form(...), current_user=Depends(require_role(["admin", "reception"])), db=Depends(get_db)):
    db.execute("UPDATE prescriptions SET status = 'cancelled' WHERE id = ?", (prescription_id,))
    db.commit()
    return RedirectResponse(url="/reception/cashier?cancelled=1", status_code=302)


@router.post("/cashier/pay-lab-order")
async def pay_lab_order(request: Request, lab_order_id: int = Form(...), current_user=Depends(require_role(["admin", "reception"])), db=Depends(get_db)):
    lab_order = get_lab_order(db, lab_order_id)
    db.execute("UPDATE lab_orders SET status = 'paid', paid_at = ?, paid_by = ? WHERE id = ?", (now(), current_user.id, lab_order_id))
    db.execute(
        "INSERT INTO payments (payable_type, payable_id, amount, receipt_number, status, created_at, created_by) VALUES ('lab_order', ?, ?, ?, 'paid', ?, ?)",
        (lab_order_id, lab_order.total_amount, receipt_number("LAB", lab_order_id), now(), current_user.id),
    )
    db.commit()
    return RedirectResponse(url="/reception/cashier?paid=1", status_code=302)


@router.post("/cashier/cancel-lab-order")
async def cancel_lab_order(request: Request, lab_order_id: int = Form(...), current_user=Depends(require_role(["admin", "reception"])), db=Depends(get_db)):
    db.execute("UPDATE lab_orders SET status = 'cancelled' WHERE id = ?", (lab_order_id,))
    db.commit()
    return RedirectResponse(url="/reception/cashier?cancelled=1", status_code=302)
