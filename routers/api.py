import sqlite3
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from auth import require_role

router = APIRouter(prefix="/api", tags=["api"])


def get_db():
    db = sqlite3.connect("hospital.db")
    db.row_factory = sqlite3.Row
    try:
        yield db
    finally:
        db.close()


def get_drug_stock(db, drug_id):
    row = db.execute(
        "SELECT SUM(quantity_change) AS stock FROM stock_transactions WHERE drug_id = ?",
        (drug_id,),
    ).fetchone()
    return row["stock"] or 0


def patient_payload(patient, db):
    last_admission = db.execute(
        """
        SELECT id, admission_type, status, description, created_at
        FROM admissions
        WHERE patient_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (patient["id"],),
    ).fetchone()

    return {
        "id": patient["id"],
        "national_id": patient["national_id"],
        "full_name": patient["full_name"],
        "phone": patient["phone"],
        "birth_date": patient["birth_date"],
        "gender": patient["gender"],
        "address": patient["address"],
        "last_visit": {
            "id": last_admission["id"],
            "type": last_admission["admission_type"],
            "status": last_admission["status"],
            "description": last_admission["description"],
            "created_at": last_admission["created_at"],
        } if last_admission else None,
    }


@router.get("/drugs/search")
async def search_drugs(q: str, db=Depends(get_db)):
    drugs = db.execute(
        """
        SELECT id, name, manufacturer, form, dosage, default_instructions, price, min_threshold
        FROM drugs
        WHERE name LIKE ?
        LIMIT 10
        """,
        (f"%{q}%",),
    ).fetchall()

    return JSONResponse([
        {
            "id": drug["id"],
            "name": drug["name"],
            "manufacturer": drug["manufacturer"],
            "form": drug["form"],
            "dosage": drug["dosage"],
            "default_instructions": drug["default_instructions"],
            "price": float(drug["price"]),
            "stock": get_drug_stock(db, drug["id"]),
            "min_threshold": drug["min_threshold"],
        }
        for drug in drugs
    ])


@router.get("/lab-tests/search")
async def search_lab_tests(q: str, db=Depends(get_db)):
    tests = db.execute(
        """
        SELECT id, code, name, category, sample_type, unit, price, male_normal_range, female_normal_range
        FROM lab_tests
        WHERE is_active = 1 AND (name LIKE ? OR code LIKE ?)
        ORDER BY category, name
        LIMIT 12
        """,
        (f"%{q}%", f"%{q}%"),
    ).fetchall()

    return JSONResponse([
        {
            "id": test["id"],
            "code": test["code"],
            "name": test["name"],
            "category": test["category"],
            "sample_type": test["sample_type"],
            "unit": test["unit"],
            "price": float(test["price"] or 0),
            "male_normal_range": test["male_normal_range"],
            "female_normal_range": test["female_normal_range"],
        }
        for test in tests
    ])


@router.get("/patients/lookup")
async def lookup_patient(
    national_id: str,
    current_user=Depends(require_role(["admin", "reception", "pharmacy"])),
    db=Depends(get_db),
):
    patient = db.execute(
        "SELECT * FROM patients WHERE national_id = ?",
        (national_id,),
    ).fetchone()

    if not patient:
        return JSONResponse({
            "exists": False,
            "valid": True,
            "national_id": national_id,
            "message": "پرونده ای برای این کد ملی یافت نشد.",
        })

    return JSONResponse({
        "exists": True,
        "valid": True,
        "patient": patient_payload(patient, db),
    })


@router.post("/patients/quick-create")
async def quick_create_patient(
    request: Request,
    current_user=Depends(require_role(["admin", "reception"])),
    db=Depends(get_db),
):
    data = await request.json()

    cursor = db.execute(
        """
        INSERT INTO patients
        (national_id, full_name, phone, birth_date, gender, address, created_at, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data.get("national_id"),
            data.get("full_name"),
            data.get("phone"),
            data.get("birth_date"),
            data.get("gender"),
            data.get("address"),
            datetime.now(timezone.utc).isoformat(),
            current_user.id,
        ),
    )
    db.commit()

    patient = db.execute(
        "SELECT * FROM patients WHERE id = ?",
        (cursor.lastrowid,),
    ).fetchone()

    return JSONResponse({
        "ok": True,
        "patient": patient_payload(patient, db),
    }, status_code=201)
