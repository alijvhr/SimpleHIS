from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime, date
from database import get_db
from models.user import User
from models.patient import Patient, Gender
from models.admission import Admission, AdmissionType, AdmissionStatus
from models.payment import Payment, PayableType, PaymentStatus
from models.prescription import Prescription, PrescriptionStatus
from auth import require_auth, require_role

router = APIRouter(prefix="/reception", tags=["reception"])
templates = Jinja2Templates(directory="templates")

def add_message(request: Request, message_type: str, text: str):
    """Add flash message"""
    if not hasattr(request.state, 'messages'):
        request.state.messages = []
    request.state.messages.append({"type": message_type, "text": text})

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
    
    if patient_id:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
    elif national_id:
        patient = db.query(Patient).filter(Patient.national_id == national_id).first()
    
    return templates.TemplateResponse(
        "reception/admit.htm",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "admit",
            "patient": patient
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
    admission = Admission(
        patient_id=patient_id,
        admission_type=AdmissionType(admission_type),
        description=description,
        radiology_type=radiology_type if admission_type == 'radiology' else None,
        status=AdmissionStatus.waiting_payment,
        created_by=current_user.id
    )
    
    db.add(admission)
    db.commit()
    
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
    ).all()
    
    waiting_prescriptions = db.query(Prescription).filter(
        Prescription.status == PrescriptionStatus.waiting_payment
    ).all()
    
    messages = getattr(request.state, 'messages', [])
    
    return templates.TemplateResponse(
        "reception/cashier.htm",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "cashier",
            "waiting_admissions": waiting_admissions,
            "waiting_prescriptions": waiting_prescriptions,
            "messages": messages
        }
    )

@router.post("/cashier/pay-admission")
async def pay_admission(
    request: Request,
    admission_id: int = Form(...),
    amount: float = Form(...),
    current_user: User = Depends(require_role(['admin', 'reception'])),
    db: Session = Depends(get_db)
):
    """Pay for admission"""
    admission = db.query(Admission).filter(Admission.id == admission_id).first()
    if admission:
        admission.status = AdmissionStatus.paid
        admission.paid_at = datetime.utcnow()
        admission.paid_by = current_user.id
        
        payment = Payment(
            payable_type=PayableType.admission,
            payable_id=admission_id,
            amount=amount,
            status=PaymentStatus.paid,
            created_by=current_user.id
        )
        
        db.add(payment)
        db.commit()
    
    return RedirectResponse(url="/reception/cashier?success=1", status_code=302)

@router.post("/cashier/cancel-admission")
async def cancel_admission(
    request: Request,
    admission_id: int = Form(...),
    current_user: User = Depends(require_role(['admin', 'reception'])),
    db: Session = Depends(get_db)
):
    """Cancel admission"""
    admission = db.query(Admission).filter(Admission.id == admission_id).first()
    if admission:
        admission.status = AdmissionStatus.cancelled
        db.commit()
    
    return RedirectResponse(url="/reception/cashier", status_code=302)

@router.post("/cashier/pay-prescription")
async def pay_prescription(
    request: Request,
    prescription_id: int = Form(...),
    current_user: User = Depends(require_role(['admin', 'reception'])),
    db: Session = Depends(get_db)
):
    """Pay for prescription"""
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if prescription:
        prescription.status = PrescriptionStatus.paid
        
        payment = Payment(
            payable_type=PayableType.prescription,
            payable_id=prescription_id,
            amount=prescription.total_amount,
            status=PaymentStatus.paid,
            created_by=current_user.id
        )
        
        db.add(payment)
        db.commit()
    
    return RedirectResponse(url="/reception/cashier?success=1", status_code=302)

@router.post("/cashier/cancel-prescription")
async def cancel_prescription(
    request: Request,
    prescription_id: int = Form(...),
    current_user: User = Depends(require_role(['admin', 'reception'])),
    db: Session = Depends(get_db)
):
    """Cancel prescription"""
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if prescription:
        prescription.status = PrescriptionStatus.cancelled
        db.commit()
    
    return RedirectResponse(url="/reception/cashier", status_code=302)
