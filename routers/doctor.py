from decimal import Decimal
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List
from database import get_db
from models.user import User
from models.patient import Patient
from models.admission import Admission, AdmissionStatus, AdmissionType
from models.prescription import Prescription, PrescriptionItem, PrescriptionStatus
from models.drug import Drug
from models.lab_order import LabOrder, LabOrderItem, LabOrderStatus
from models.lab_test import LabTest
from auth import require_role

router = APIRouter(prefix="/doctor", tags=["doctor"])
templates = Jinja2Templates(directory="templates")

@router.get("/patients", response_class=HTMLResponse)
async def doctor_patients(
    request: Request,
    current_user: User = Depends(require_role(['admin', 'doctor'])),
    db: Session = Depends(get_db)
):
    """List paid doctor admissions"""
    admissions = db.query(Admission).filter(
        Admission.admission_type == AdmissionType.doctor,
        Admission.status == AdmissionStatus.paid
    ).order_by(Admission.paid_at.asc(), Admission.created_at.asc()).all()
    
    return templates.TemplateResponse(
        "doctor/patients.htm",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "doctor_patients",
            "admissions": admissions
        }
    )

@router.get("/patient/{patient_id}/admission/{admission_id}", response_class=HTMLResponse)
async def patient_file(
    request: Request,
    patient_id: int,
    admission_id: int,
    current_user: User = Depends(require_role(['admin', 'doctor'])),
    db: Session = Depends(get_db)
):
    """Patient file with prescription form"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    admission = db.query(Admission).filter(
        Admission.id == admission_id,
        Admission.patient_id == patient_id,
        Admission.admission_type == AdmissionType.doctor
    ).first()
    if not patient or not admission:
        return RedirectResponse(url="/doctor/patients", status_code=302)
    
    # Get previous prescriptions
    previous_prescriptions = db.query(Prescription).filter(
        Prescription.patient_id == patient_id,
        Prescription.id != admission.prescription.id if admission.prescription else True
    ).order_by(Prescription.created_at.desc()).limit(5).all()

    previous_lab_orders = db.query(LabOrder).filter(
        LabOrder.patient_id == patient_id
    ).order_by(LabOrder.created_at.desc()).limit(5).all()

    previous_radiology = db.query(Admission).filter(
        Admission.patient_id == patient_id,
        Admission.admission_type == AdmissionType.radiology
    ).order_by(Admission.created_at.desc()).limit(5).all()
    
    return templates.TemplateResponse(
        "doctor/patient_file.htm",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "doctor_patients",
            "patient": patient,
            "admission": admission,
            "previous_prescriptions": previous_prescriptions,
            "previous_lab_orders": previous_lab_orders,
            "previous_radiology": previous_radiology
        }
    )

def clean_parallel_rows(*columns):
    row_count = max((len(column) for column in columns), default=0)
    for index in range(row_count):
        yield [column[index] if index < len(column) else None for column in columns]

@router.post("/orders/create")
async def create_clinical_orders(
    request: Request,
    patient_id: int = Form(...),
    admission_id: int = Form(...),
    drug_id: List[str] = Form([]),
    quantity: List[str] = Form([]),
    instructions: List[str] = Form([]),
    lab_test_id: List[str] = Form([]),
    lab_note: List[str] = Form([]),
    lab_clinical_note: str = Form(None),
    radiology_type: List[str] = Form([]),
    radiology_description: List[str] = Form([]),
    current_user: User = Depends(require_role(['admin', 'doctor'])),
    db: Session = Depends(get_db)
):
    """Create medications, laboratory requests, and radiology requests from one visit."""
    admission = db.query(Admission).filter(
        Admission.id == admission_id,
        Admission.patient_id == patient_id,
        Admission.admission_type == AdmissionType.doctor,
        Admission.status == AdmissionStatus.paid
    ).first()
    if not admission:
        return RedirectResponse(url="/doctor/patients", status_code=302)

    prescription_rows = []
    prescription_total = Decimal("0")
    for raw_drug_id, raw_quantity, raw_instructions in clean_parallel_rows(drug_id, quantity, instructions):
        if not raw_drug_id:
            continue
        drug = db.query(Drug).filter(Drug.id == int(raw_drug_id)).first()
        if not drug:
            continue
        item_quantity = max(1, int(raw_quantity or 1))
        prescription_total += Decimal(str(drug.price or 0)) * item_quantity
        prescription_rows.append((drug, item_quantity, (raw_instructions or drug.default_instructions or "").strip()))

    if prescription_rows:
        prescription = Prescription(
            patient_id=patient_id,
            admission_id=admission_id,
            is_manual=False,
            total_amount=prescription_total,
            status=PrescriptionStatus.waiting_payment,
            created_by=current_user.id
        )
        db.add(prescription)
        db.flush()

        for drug, item_quantity, item_instructions in prescription_rows:
            db.add(PrescriptionItem(
                prescription_id=prescription.id,
                drug_id=drug.id,
                quantity=item_quantity,
                instructions=item_instructions or "طبق دستور پزشک"
            ))

    lab_rows = []
    lab_total = Decimal("0")
    for raw_test_id, raw_note in clean_parallel_rows(lab_test_id, lab_note):
        if not raw_test_id:
            continue
        test = db.query(LabTest).filter(LabTest.id == int(raw_test_id), LabTest.is_active == True).first()
        if not test:
            continue
        lab_total += Decimal(str(test.price or 0))
        lab_rows.append((test, (raw_note or "").strip()))

    if lab_rows:
        lab_order = LabOrder(
            patient_id=patient_id,
            admission_id=admission_id,
            total_amount=lab_total,
            status=LabOrderStatus.waiting_payment,
            clinical_note=(lab_clinical_note or "").strip() or None,
            created_by=current_user.id
        )
        db.add(lab_order)
        db.flush()

        for test, note in lab_rows:
            db.add(LabOrderItem(
                order_id=lab_order.id,
                test_id=test.id,
                price=test.price or 0,
                notes=note or None
            ))

    for raw_type, raw_description in clean_parallel_rows(radiology_type, radiology_description):
        request_type = (raw_type or "").strip()
        description = (raw_description or "").strip()
        if not request_type:
            continue
        db.add(Admission(
            patient_id=patient_id,
            admission_type=AdmissionType.radiology,
            description=description or f"درخواست تصویربرداری {request_type}",
            radiology_type=request_type,
            status=AdmissionStatus.waiting_payment,
            created_by=current_user.id
        ))

    db.commit()

    return RedirectResponse(
        url=f"/doctor/patient/{patient_id}/admission/{admission_id}?saved=1",
        status_code=302
    )

@router.post("/prescription/create")
async def create_prescription(
    request: Request,
    patient_id: int = Form(...),
    admission_id: int = Form(...),
    total_amount: float = Form(0),
    drug_id: List[str] = Form([]),
    quantity: List[str] = Form([]),
    instructions: List[str] = Form([]),
    current_user: User = Depends(require_role(['admin', 'doctor'])),
    db: Session = Depends(get_db)
):
    """Backward-compatible prescription endpoint."""
    return await create_clinical_orders(
        request=request,
        patient_id=patient_id,
        admission_id=admission_id,
        drug_id=drug_id,
        quantity=quantity,
        instructions=instructions,
        lab_test_id=[],
        lab_note=[],
        lab_clinical_note=None,
        radiology_type=[],
        radiology_description=[],
        current_user=current_user,
        db=db
    )

@router.post("/complete/{admission_id}")
async def complete_visit(
    admission_id: int,
    current_user: User = Depends(require_role(['admin', 'doctor'])),
    db: Session = Depends(get_db)
):
    """Complete visit"""
    admission = db.query(Admission).filter(Admission.id == admission_id).first()
    if admission:
        admission.status = AdmissionStatus.completed
        admission.completed_at = datetime.now(timezone.utc)
        db.commit()
    
    return RedirectResponse(url="/doctor/patients", status_code=302)
