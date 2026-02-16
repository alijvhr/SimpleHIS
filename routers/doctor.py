from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from database import get_db
from models.user import User
from models.patient import Patient
from models.admission import Admission, AdmissionStatus, AdmissionType
from models.prescription import Prescription, PrescriptionItem, PrescriptionStatus
from models.drug import Drug
from auth import require_auth, require_role

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
    ).all()
    
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
    admission = db.query(Admission).filter(Admission.id == admission_id).first()
    
    # Get previous prescriptions
    previous_prescriptions = db.query(Prescription).filter(
        Prescription.patient_id == patient_id,
        Prescription.id != admission.prescription.id if admission.prescription else True
    ).order_by(Prescription.created_at.desc()).limit(5).all()
    
    return templates.TemplateResponse(
        "doctor/patient_file.htm",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "doctor_patients",
            "patient": patient,
            "admission": admission,
            "previous_prescriptions": previous_prescriptions
        }
    )

@router.post("/prescription/create")
async def create_prescription(
    request: Request,
    patient_id: int = Form(...),
    admission_id: int = Form(...),
    total_amount: float = Form(...),
    drug_id: List[int] = Form(...),
    quantity: List[int] = Form(...),
    instructions: List[str] = Form(...),
    current_user: User = Depends(require_role(['admin', 'doctor'])),
    db: Session = Depends(get_db)
):
    """Create prescription"""
    # Create prescription
    prescription = Prescription(
        patient_id=patient_id,
        admission_id=admission_id,
        is_manual=False,
        total_amount=total_amount,
        status=PrescriptionStatus.waiting_payment,
        created_by=current_user.id
    )
    
    db.add(prescription)
    db.flush()
    
    # Create prescription items
    for i in range(len(drug_id)):
        if drug_id[i]:  # Only add items with selected drugs
            item = PrescriptionItem(
                prescription_id=prescription.id,
                drug_id=drug_id[i],
                quantity=quantity[i],
                instructions=instructions[i]
            )
            db.add(item)
    
    db.commit()
    
    return RedirectResponse(url="/doctor/patients", status_code=302)

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
        admission.completed_at = datetime.utcnow()
        db.commit()
    
    return RedirectResponse(url="/doctor/patients", status_code=302)

@router.get("/api/drugs/search")
async def search_drugs(
    q: str,
    db: Session = Depends(get_db)
):
    """API endpoint for drug search autocomplete"""
    drugs = db.query(Drug).filter(Drug.name.contains(q)).limit(10).all()
    
    return JSONResponse([
        {
            "id": drug.id,
            "name": drug.name,
            "manufacturer": drug.manufacturer,
            "form": drug.form,
            "dosage": drug.dosage,
            "default_instructions": drug.default_instructions,
            "price": float(drug.price)
        }
        for drug in drugs
    ])
