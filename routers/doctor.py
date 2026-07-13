from decimal import Decimal
from typing import List

from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from auth import require_role
from database import all_rows, get_admission, get_db, get_drug, get_lab_order, get_lab_test, get_patient, get_prescription, now, one

router = APIRouter(prefix="/doctor", tags=["doctor"])
templates = Jinja2Templates(directory="templates")


def clean_parallel_rows(*columns):
    row_count = max((len(column) for column in columns), default=0)
    for index in range(row_count):
        yield [column[index] if index < len(column) else None for column in columns]


def form_list(form, *names: str) -> list[str]:
    for name in names:
        values = form.getlist(name)
        if values:
            return values
    return []


def doctor_admissions(db):
    admissions = all_rows(
        db,
        """
        SELECT * FROM admissions
        WHERE admission_type = 'doctor' AND status = 'paid'
        ORDER BY paid_at, created_at
        """,
    )
    for admission in admissions:
        admission.patient = get_patient(db, admission.patient_id)
    return admissions


def patient_admissions(db, patient_id: int):
    return [
        get_admission(db, row.id)
        for row in all_rows(db, "SELECT id FROM admissions WHERE patient_id = ? ORDER BY created_at DESC", (patient_id,))
    ]


def patient_prescriptions(db, patient_id: int):
    return [
        get_prescription(db, row.id)
        for row in all_rows(db, "SELECT id FROM prescriptions WHERE patient_id = ? ORDER BY created_at DESC", (patient_id,))
    ]


def patient_lab_orders(db, patient_id: int):
    return [
        get_lab_order(db, row.id)
        for row in all_rows(db, "SELECT id FROM lab_orders WHERE patient_id = ? ORDER BY created_at DESC", (patient_id,))
    ]


def patient_radiology_admissions(db, patient_id: int):
    return [
        get_admission(db, row.id)
        for row in all_rows(
            db,
            "SELECT id FROM admissions WHERE patient_id = ? AND admission_type = 'radiology' ORDER BY created_at DESC",
            (patient_id,),
        )
    ]


@router.get("/patients", response_class=HTMLResponse)
async def doctor_patients(request: Request, current_user=Depends(require_role(["admin", "doctor"])), db=Depends(get_db)):
    return templates.TemplateResponse(
        "doctor/patients.htm",
        {"request": request, "current_user": current_user, "active_page": "doctor_patients", "admissions": doctor_admissions(db)},
    )


@router.get("/patient/{patient_id}/file", response_class=HTMLResponse)
async def show_patient_file(
    request: Request,
    patient_id: int,
    current_user=Depends(require_role(["admin", "doctor"])),
    db=Depends(get_db),
):
    patient = get_patient(db, patient_id)
    if not patient:
        return RedirectResponse(url="/doctor/patients", status_code=302)

    return templates.TemplateResponse(
        "doctor/patient_history.htm",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "doctor_patients",
            "patient": patient,
            "admissions": patient_admissions(db, patient_id),
            "prescriptions": patient_prescriptions(db, patient_id),
            "lab_orders": patient_lab_orders(db, patient_id),
            "radiology_admissions": patient_radiology_admissions(db, patient_id),
        },
    )


@router.get("/patient/{patient_id}/admission/{admission_id}/results", response_class=HTMLResponse)
async def show_admission_results(
    request: Request,
    patient_id: int,
    admission_id: int,
    current_user=Depends(require_role(["admin", "doctor"])),
    db=Depends(get_db),
):
    patient = get_patient(db, patient_id)
    admission = one(
        db,
        "SELECT * FROM admissions WHERE id = ? AND patient_id = ? AND admission_type = 'doctor'",
        (admission_id, patient_id),
    )
    if not patient or not admission:
        return RedirectResponse(url="/doctor/patients", status_code=302)
    admission.patient = patient

    lab_orders = [
        get_lab_order(db, row.id)
        for row in all_rows(
            db,
            "SELECT id FROM lab_orders WHERE patient_id = ? AND admission_id = ? ORDER BY created_at DESC",
            (patient_id, admission_id),
        )
    ]
    if not lab_orders:
        lab_orders = patient_lab_orders(db, patient_id)

    return templates.TemplateResponse(
        "doctor/admission_results.htm",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "doctor_patients",
            "patient": patient,
            "admission": admission,
            "lab_orders": lab_orders,
            "radiology_admissions": patient_radiology_admissions(db, patient_id),
        },
    )


@router.get("/patient/{patient_id}/admission/{admission_id}", response_class=HTMLResponse)
async def patient_file(
    request: Request,
    patient_id: int,
    admission_id: int,
    current_user=Depends(require_role(["admin", "doctor"])),
    db=Depends(get_db),
):
    patient = get_patient(db, patient_id)
    admission = one(
        db,
        "SELECT * FROM admissions WHERE id = ? AND patient_id = ? AND admission_type = 'doctor'",
        (admission_id, patient_id),
    )
    if not patient or not admission:
        return RedirectResponse(url="/doctor/patients", status_code=302)
    admission.patient = patient

    prescriptions = all_rows(db, "SELECT * FROM prescriptions WHERE patient_id = ? ORDER BY created_at DESC LIMIT 5", (patient_id,))
    previous_prescriptions = [get_prescription(db, row.id) for row in prescriptions]

    orders = all_rows(db, "SELECT * FROM lab_orders WHERE patient_id = ? ORDER BY created_at DESC LIMIT 5", (patient_id,))
    previous_lab_orders = [get_lab_order(db, row.id) for row in orders]

    previous_radiology = all_rows(
        db,
        "SELECT * FROM admissions WHERE patient_id = ? AND admission_type = 'radiology' ORDER BY created_at DESC LIMIT 5",
        (patient_id,),
    )

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
            "previous_radiology": previous_radiology,
        },
    )


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
    current_user=Depends(require_role(["admin", "doctor"])),
    db=Depends(get_db),
):
    form = await request.form()
    drug_id = form_list(form, "drug_id", "drug_id[]")
    quantity = form_list(form, "quantity", "quantity[]")
    instructions = form_list(form, "instructions", "instructions[]")
    lab_test_id = form_list(form, "lab_test_id", "lab_test_id[]")
    lab_note = form_list(form, "lab_note", "lab_note[]")
    radiology_type = form_list(form, "radiology_type", "radiology_type[]")
    radiology_description = form_list(form, "radiology_description", "radiology_description[]")

    prescription_rows = []
    prescription_total = Decimal("0")
    for raw_drug_id, raw_quantity, raw_instructions in clean_parallel_rows(drug_id, quantity, instructions):
        if not raw_drug_id:
            continue
        drug = get_drug(db, int(raw_drug_id))
        item_quantity = max(1, int(raw_quantity or 1))
        prescription_total += Decimal(str(drug.price or 0)) * item_quantity
        prescription_rows.append((drug, item_quantity, (raw_instructions or drug.default_instructions or "").strip()))

    if prescription_rows:
        cur = db.execute(
            """
            INSERT INTO prescriptions (patient_id, admission_id, is_manual, total_amount, status, created_at, created_by)
            VALUES (?, ?, 0, ?, 'waiting_payment', ?, ?)
            """,
            (patient_id, admission_id, str(prescription_total), now(), current_user.id),
        )
        prescription_id = cur.lastrowid
        for drug, item_quantity, item_instructions in prescription_rows:
            db.execute(
                "INSERT INTO prescription_items (prescription_id, drug_id, quantity, instructions) VALUES (?, ?, ?, ?)",
                (prescription_id, drug.id, item_quantity, item_instructions or "طبق دستور پزشک"),
            )

    lab_rows = []
    lab_total = Decimal("0")
    for raw_test_id, raw_note in clean_parallel_rows(lab_test_id, lab_note):
        if not raw_test_id:
            continue
        test = get_lab_test(db, int(raw_test_id))
        lab_total += Decimal(str(test.price or 0))
        lab_rows.append((test, (raw_note or "").strip()))

    if lab_rows:
        cur = db.execute(
            """
            INSERT INTO lab_orders (patient_id, admission_id, total_amount, status, clinical_note, created_at, created_by)
            VALUES (?, ?, ?, 'waiting_payment', ?, ?, ?)
            """,
            (patient_id, admission_id, str(lab_total), (lab_clinical_note or "").strip() or None, now(), current_user.id),
        )
        order_id = cur.lastrowid
        for test, note in lab_rows:
            db.execute(
                "INSERT INTO lab_order_items (order_id, test_id, price, notes) VALUES (?, ?, ?, ?)",
                (order_id, test.id, test.price or 0, note or None),
            )

    for raw_type, raw_description in clean_parallel_rows(radiology_type, radiology_description):
        request_type = (raw_type or "").strip()
        description = (raw_description or "").strip()
        if request_type:
            db.execute(
                """
                INSERT INTO admissions (patient_id, admission_type, description, radiology_type, status, created_at, created_by)
                VALUES (?, 'radiology', ?, ?, 'waiting_payment', ?, ?)
                """,
                (patient_id, description or f"درخواست تصویربرداری {request_type}", request_type, now(), current_user.id),
            )

    db.commit()
    return RedirectResponse(url=f"/doctor/patient/{patient_id}/admission/{admission_id}?saved=1", status_code=302)


@router.post("/prescription/create")
async def create_prescription(
    request: Request,
    patient_id: int = Form(...),
    admission_id: int = Form(...),
    total_amount: float = Form(0),
    drug_id: List[str] = Form([]),
    quantity: List[str] = Form([]),
    instructions: List[str] = Form([]),
    current_user=Depends(require_role(["admin", "doctor"])),
    db=Depends(get_db),
):
    return await create_clinical_orders(request, patient_id, admission_id, drug_id, quantity, instructions, [], [], None, [], [], current_user, db)


@router.post("/complete/{admission_id}")
async def complete_visit(admission_id: int, current_user=Depends(require_role(["admin", "doctor"])), db=Depends(get_db)):
    db.execute("UPDATE admissions SET status = 'completed', completed_at = ? WHERE id = ?", (now(), admission_id))
    db.commit()
    return RedirectResponse(url="/doctor/patients", status_code=302)
