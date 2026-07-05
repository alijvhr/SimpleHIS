from datetime import date
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import get_db
from models.drug import Drug
from models.patient import Patient, Gender
from models.admission import Admission
from models.user import User
from auth import require_role
from utils.validators import validate_iranian_national_id

router = APIRouter(prefix="/api", tags=["api"])

def patient_payload(patient: Patient, db: Session):
    """Serialize patient demographics plus last visit summary for admission lookup."""
    last_admission = db.query(Admission).filter(
        Admission.patient_id == patient.id
    ).order_by(Admission.created_at.desc()).first()

    return {
        "id": patient.id,
        "national_id": patient.national_id,
        "full_name": patient.full_name,
        "phone": patient.phone,
        "birth_date": patient.birth_date.isoformat() if patient.birth_date else None,
        "gender": patient.gender.value,
        "address": patient.address,
        "last_visit": {
            "id": last_admission.id,
            "type": last_admission.admission_type.value,
            "status": last_admission.status.value,
            "description": last_admission.description,
            "created_at": last_admission.created_at.isoformat() if last_admission.created_at else None,
        } if last_admission else None,
    }

@router.get("/drugs/search")
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

@router.get("/patients/lookup")
async def lookup_patient(
    national_id: str,
    current_user: User = Depends(require_role(['admin', 'reception', 'pharmacy'])),
    db: Session = Depends(get_db)
):
    """Lookup a patient by national ID for non-blocking admission workflows."""
    normalized_id = ''.join(filter(str.isdigit, national_id or ''))
    if len(normalized_id) != 10:
        return JSONResponse({
            "exists": False,
            "valid": False,
            "message": "کد ملی باید ۱۰ رقم باشد."
        }, status_code=400)

    if not validate_iranian_national_id(normalized_id):
        return JSONResponse({
            "exists": False,
            "valid": False,
            "message": "کد ملی وارد شده معتبر نیست."
        }, status_code=400)

    patient = db.query(Patient).filter(Patient.national_id == normalized_id).first()
    if not patient:
        return JSONResponse({
            "exists": False,
            "valid": True,
            "national_id": normalized_id,
            "message": "پرونده‌ای برای این کد ملی یافت نشد."
        })

    return JSONResponse({
        "exists": True,
        "valid": True,
        "patient": patient_payload(patient, db)
    })

@router.post("/patients/quick-create")
async def quick_create_patient(
    request: Request,
    current_user: User = Depends(require_role(['admin', 'reception'])),
    db: Session = Depends(get_db)
):
    """Create a patient inline and return the new profile for the admission form."""
    data = await request.json()
    national_id = ''.join(filter(str.isdigit, data.get("national_id", "")))

    if not validate_iranian_national_id(national_id):
        return JSONResponse({"ok": False, "message": "کد ملی وارد شده معتبر نیست."}, status_code=400)

    if db.query(Patient).filter(Patient.national_id == national_id).first():
        return JSONResponse({"ok": False, "message": "این بیمار قبلا ثبت شده است."}, status_code=409)

    try:
        birth_date = date.fromisoformat(data.get("birth_date", ""))
        gender = Gender(data.get("gender"))
    except (TypeError, ValueError):
        return JSONResponse({"ok": False, "message": "تاریخ تولد یا جنسیت معتبر نیست."}, status_code=400)

    full_name = (data.get("full_name") or "").strip()
    phone = (data.get("phone") or "").strip()
    if not full_name or not phone:
        return JSONResponse({"ok": False, "message": "نام و تلفن بیمار الزامی است."}, status_code=400)

    patient = Patient(
        national_id=national_id,
        full_name=full_name,
        phone=phone,
        birth_date=birth_date,
        gender=gender,
        address=(data.get("address") or "").strip() or None,
        created_by=current_user.id
    )

    db.add(patient)
    db.commit()
    db.refresh(patient)

    return JSONResponse({
        "ok": True,
        "patient": patient_payload(patient, db)
    }, status_code=201)
