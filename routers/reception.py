from decimal import Decimal, ROUND_HALF_UP
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date, timezone
from database import get_db
from models.user import User
from models.patient import Patient, Gender
from models.admission import Admission, AdmissionType, AdmissionStatus
from models.payment import Payment, PayableType, PaymentStatus
from models.prescription import Prescription, PrescriptionStatus
from models.stock import StockTransaction
from models.lab_order import LabOrder, LabOrderStatus
from models.lab_order import LabOrderItem
from models.lab_test import LabTest
from auth import require_role
from config import get_admission_price

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
    if request.query_params.get("error") == "not_found":
        return [{"type": "danger", "text": "درخواست مورد نظر پیدا نشد."}]
    if request.query_params.get("error") == "invalid_status":
        return [{"type": "danger", "text": "این درخواست دیگر در وضعیت قابل پرداخت نیست."}]
    return []

def get_drug_stock(db: Session, drug_id: int) -> int:
    result = db.query(func.sum(StockTransaction.quantity_change)).filter(
        StockTransaction.drug_id == drug_id
    ).scalar()
    return result if result else 0

def parse_form_ids(values) -> list[int]:
    if not values:
        return []
    if not isinstance(values, list):
        values = [values]
    ids = []
    for value in values:
        try:
            ids.append(int(value))
        except (TypeError, ValueError):
            continue
    return ids

def prescription_payment_rows(db: Session, prescriptions: list[Prescription]) -> list[dict]:
    rows = []
    for prescription in prescriptions:
        shortages = []
        for item in prescription.items:
            current_stock = get_drug_stock(db, item.drug_id)
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
    current_user: User = Depends(require_role(['admin', 'reception'])),
    db: Session = Depends(get_db)
):
    """Patient search and list"""
    patients = []
    
    if national_id:
        patients = db.query(Patient).filter(Patient.national_id.contains(national_id)).all()
    elif phone:
        patients = db.query(Patient).filter(Patient.phone.contains(phone)).all()
    
    return templates.TemplateResponse(
        "reception/patients.htm",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "patients",
            "patients": patients,
            "search_query": national_id,
            "phone_query": phone
        }
    )

@router.get("/patients/new", response_class=HTMLResponse)
async def new_patient_form(
    request: Request,
    current_user: User = Depends(require_role(['admin', 'reception'])),
):
    """New patient form"""
    return templates.TemplateResponse(
        "reception/patient_form.htm",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "patients",
            "patient": None
        }
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
    current_user: User = Depends(require_role(['admin', 'reception'])),
    db: Session = Depends(get_db)
):
    """Create new patient"""
    national_id = ''.join(filter(str.isdigit, national_id))

    # The UI workflow accepts any 10-digit national ID and keeps uniqueness enforced.
    if len(national_id) != 10:
        return templates.TemplateResponse(
            "reception/patient_form.htm",
            {
                "request": request,
                "current_user": current_user,
                "active_page": "patients",
                "patient": None,
                "messages": [{"type": "danger", "text": "کد ملی وارد شده نامعتبر است"}]
            }
        )
    
    # Check if patient already exists
    existing = db.query(Patient).filter(Patient.national_id == national_id).first()
    if existing:
        return templates.TemplateResponse(
            "reception/patient_form.htm",
            {
                "request": request,
                "current_user": current_user,
                "active_page": "patients",
                "patient": None,
                "messages": [{"type": "danger", "text": "بیمار با این کد ملی قبلا ثبت شده است"}]
            }
        )
    
    patient = Patient(
        national_id=national_id,
        full_name=full_name,
        phone=phone,
        birth_date=birth_date,
        gender=Gender(gender),
        address=address,
        created_by=current_user.id
    )

    try:
        db.add(patient)
        db.commit()
        db.refresh(patient)
    except Exception:
        db.rollback()
        return templates.TemplateResponse(
            "reception/patient_form.htm",
            {
                "request": request,
                "current_user": current_user,
                "active_page": "patients",
                "patient": None,
                "messages": [{"type": "danger", "text": "خطا در ذخیره‌سازی بیمار. لطفاً بعداً دوباره تلاش کنید."}]
            }
        )
    return RedirectResponse(url=f"/reception/admit?patient_id={patient.id}", status_code=302)

@router.get("/admit", response_class=HTMLResponse)
async def admit_form(
    request: Request,
    patient_id: int = None,
    national_id: str = None,
    current_user: User = Depends(require_role(['admin', 'reception'])),
    db: Session = Depends(get_db)
):
    """Admission form"""
    patient = None
    searched_national_id = ''.join(filter(str.isdigit, national_id or '')) if national_id else ''
    
    if patient_id:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
    elif searched_national_id:
        patient = db.query(Patient).filter(Patient.national_id == searched_national_id).first()

    patient_not_found = bool(searched_national_id and len(searched_national_id) == 10 and not patient)
    lab_tests = db.query(LabTest).filter(
        LabTest.is_active == True
    ).order_by(LabTest.category.asc(), LabTest.name.asc()).all()
    
    return templates.TemplateResponse(
        "reception/admit.htm",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "admit",
            "patient": patient,
            "searched_national_id": searched_national_id,
            "patient_not_found": patient_not_found,
            "insurance_plans": INSURANCE_PLANS,
            "admission_prices": {
                "doctor": get_admission_price("doctor"),
                "laboratory": get_admission_price("laboratory"),
                "radiology": get_admission_price("radiology"),
            },
            "lab_tests": lab_tests,
            "messages": [{"type": "danger", "text": "بیمار مورد نظر پیدا نشد."}] if request.query_params.get("error") == "not_found" else []
        }
    )

@router.post("/admit")
async def create_admission(
    request: Request,
    patient_id: int = Form(...),
    admission_type: str = Form(...),
    description: str = Form(...),
    radiology_type: str = Form(None),
    current_user: User = Depends(require_role(['admin', 'reception'])),
    db: Session = Depends(get_db)
):
    """Create admission"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        return RedirectResponse(url="/reception/admit?error=not_found", status_code=302)

    admission = Admission(
        patient_id=patient_id,
        admission_type=AdmissionType(admission_type),
        description=description,
        radiology_type=radiology_type if admission_type == 'radiology' else None,
        status=AdmissionStatus.completed if admission_type == 'laboratory' else AdmissionStatus.waiting_payment,
        created_by=current_user.id
    )
    
    try:
        form = await request.form()
        lab_test_ids = parse_form_ids(form.getlist("lab_test_id")) if admission_type == "laboratory" else []
        selected_tests = []
        if admission_type == "laboratory":
            selected_tests = db.query(LabTest).filter(
                LabTest.id.in_(lab_test_ids),
                LabTest.is_active == True
            ).all() if lab_test_ids else []
            if not selected_tests:
                return RedirectResponse(url=f"/reception/admit?patient_id={patient_id}&error=lab_tests_required", status_code=302)

        db.add(admission)
        db.flush()

        if admission_type == "laboratory":
            total_amount = sum((test.price or 0) for test in selected_tests)
            lab_order = LabOrder(
                patient_id=patient_id,
                admission_id=admission.id,
                total_amount=total_amount,
                status=LabOrderStatus.waiting_payment,
                clinical_note=description,
                created_by=current_user.id
            )
            db.add(lab_order)
            db.flush()
            for test in selected_tests:
                db.add(LabOrderItem(
                    order_id=lab_order.id,
                    test_id=test.id,
                    price=test.price or 0
                ))

        db.commit()
    except Exception:
        db.rollback()
        return RedirectResponse(url=f"/reception/admit?patient_id={patient_id}&error=create_failed", status_code=302)
    
    return RedirectResponse(url="/reception/cashier", status_code=302)

@router.get("/cashier", response_class=HTMLResponse)
async def cashier(
    request: Request,
    current_user: User = Depends(require_role(['admin', 'reception'])),
    db: Session = Depends(get_db)
):
    """Cashier page - payments and cancellations"""
    waiting_admissions = db.query(Admission).filter(
        Admission.status == AdmissionStatus.waiting_payment
    ).order_by(Admission.created_at.asc()).all()
    
    waiting_prescriptions = db.query(Prescription).filter(
        Prescription.status == PrescriptionStatus.waiting_payment
    ).order_by(Prescription.created_at.asc()).all()
    prescription_rows = prescription_payment_rows(db, waiting_prescriptions)

    waiting_lab_orders = db.query(LabOrder).filter(
        LabOrder.status == LabOrderStatus.waiting_payment
    ).order_by(LabOrder.created_at.asc()).all()
    
    # Add prices to admissions
    for admission in waiting_admissions:
        admission.price = get_admission_price(admission.admission_type.value)
        admission.invoice = get_admission_invoice(admission.admission_type.value)
    
    messages = cashier_messages(request)
    
    return templates.TemplateResponse(
        "reception/cashier.htm",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "cashier",
            "waiting_admissions": waiting_admissions,
            "waiting_prescriptions": waiting_prescriptions,
            "prescription_rows": prescription_rows,
            "waiting_lab_orders": waiting_lab_orders,
            "insurance_plans": INSURANCE_PLANS,
            "messages": messages
        }
    )

@router.post("/cashier/pay-admission")
async def pay_admission(
    request: Request,
    admission_id: int = Form(...),
    insurance_provider: str = Form("none"),
    current_user: User = Depends(require_role(['admin', 'reception'])),
    db: Session = Depends(get_db)
):
    """Pay for admission"""
    admission = db.query(Admission).filter(Admission.id == admission_id).first()
    if not admission:
        return RedirectResponse(url="/reception/cashier?error=not_found", status_code=302)
    if admission.status != AdmissionStatus.waiting_payment:
        return RedirectResponse(url="/reception/cashier?error=invalid_status", status_code=302)

    invoice = get_admission_invoice(admission.admission_type.value, insurance_provider)
    admission.status = AdmissionStatus.paid
    admission.paid_at = datetime.now(timezone.utc)
    admission.paid_by = current_user.id

    payment = Payment(
        payable_type=PayableType.admission,
        payable_id=admission_id,
        amount=invoice["patient_amount"],
        receipt_number=receipt_number("ADM", admission_id),
        status=PaymentStatus.paid,
        created_by=current_user.id
    )

    db.add(payment)
    db.commit()
    
    return RedirectResponse(url="/reception/cashier?paid=1", status_code=302)

@router.post("/cashier/cancel-admission")
async def cancel_admission(
    request: Request,
    admission_id: int = Form(...),
    current_user: User = Depends(require_role(['admin', 'reception'])),
    db: Session = Depends(get_db)
):
    """Cancel admission"""
    admission = db.query(Admission).filter(Admission.id == admission_id).first()
    if not admission:
        return RedirectResponse(url="/reception/cashier?error=not_found", status_code=302)
    if admission.status == AdmissionStatus.waiting_payment:
        admission.status = AdmissionStatus.cancelled
        db.commit()
    
    return RedirectResponse(url="/reception/cashier?cancelled=1", status_code=302)

@router.post("/cashier/pay-prescription")
async def pay_prescription(
    request: Request,
    prescription_id: int = Form(...),
    current_user: User = Depends(require_role(['admin', 'reception'])),
    db: Session = Depends(get_db)
):
    """Pay for prescription"""
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not prescription:
        return RedirectResponse(url="/reception/cashier?error=not_found", status_code=302)
    if prescription.status != PrescriptionStatus.waiting_payment:
        return RedirectResponse(url="/reception/cashier?error=invalid_status", status_code=302)

    prescription.status = PrescriptionStatus.paid

    payment = Payment(
        payable_type=PayableType.prescription,
        payable_id=prescription_id,
        amount=prescription.total_amount,
        receipt_number=receipt_number("RX", prescription_id),
        status=PaymentStatus.paid,
        created_by=current_user.id
    )

    db.add(payment)
    db.commit()
    
    return RedirectResponse(url="/reception/cashier?paid=1", status_code=302)

@router.post("/cashier/cancel-prescription")
async def cancel_prescription(
    request: Request,
    prescription_id: int = Form(...),
    current_user: User = Depends(require_role(['admin', 'reception'])),
    db: Session = Depends(get_db)
):
    """Cancel prescription"""
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not prescription:
        return RedirectResponse(url="/reception/cashier?error=not_found", status_code=302)
    if prescription.status == PrescriptionStatus.waiting_payment:
        prescription.status = PrescriptionStatus.cancelled
        db.commit()
    
    return RedirectResponse(url="/reception/cashier?cancelled=1", status_code=302)

@router.post("/cashier/pay-lab-order")
async def pay_lab_order(
    request: Request,
    lab_order_id: int = Form(...),
    current_user: User = Depends(require_role(['admin', 'reception'])),
    db: Session = Depends(get_db)
):
    """Pay for laboratory order."""
    lab_order = db.query(LabOrder).filter(LabOrder.id == lab_order_id).first()
    if not lab_order:
        return RedirectResponse(url="/reception/cashier?error=not_found", status_code=302)
    if lab_order.status != LabOrderStatus.waiting_payment:
        return RedirectResponse(url="/reception/cashier?error=invalid_status", status_code=302)

    lab_order.status = LabOrderStatus.paid
    lab_order.paid_at = datetime.now(timezone.utc)
    lab_order.paid_by = current_user.id

    payment = Payment(
        payable_type=PayableType.lab_order,
        payable_id=lab_order_id,
        amount=lab_order.total_amount,
        receipt_number=receipt_number("LAB", lab_order_id),
        status=PaymentStatus.paid,
        created_by=current_user.id
    )

    db.add(payment)
    db.commit()

    return RedirectResponse(url="/reception/cashier?paid=1", status_code=302)

@router.post("/cashier/cancel-lab-order")
async def cancel_lab_order(
    request: Request,
    lab_order_id: int = Form(...),
    current_user: User = Depends(require_role(['admin', 'reception'])),
    db: Session = Depends(get_db)
):
    """Cancel laboratory order."""
    lab_order = db.query(LabOrder).filter(LabOrder.id == lab_order_id).first()
    if not lab_order:
        return RedirectResponse(url="/reception/cashier?error=not_found", status_code=302)
    if lab_order.status == LabOrderStatus.waiting_payment:
        lab_order.status = LabOrderStatus.cancelled
        db.commit()

    return RedirectResponse(url="/reception/cashier?cancelled=1", status_code=302)
