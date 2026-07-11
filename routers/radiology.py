from typing import List
import os
import uuid

from fastapi import APIRouter, Request, Depends, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from auth import require_role
from database import all_rows, get_admission, get_db, get_radiology_report, now
from utils.validators import validate_image_file

router = APIRouter(prefix="/radiology", tags=["radiology"])
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def radiology_admission_rows(db):
    rows = all_rows(
        db,
        """
        SELECT id FROM admissions
        WHERE admission_type = 'radiology' AND status IN ('paid', 'completed')
        ORDER BY paid_at, created_at
        """,
    )
    return [get_admission(db, row.id) for row in rows]


@router.get("/admissions", response_class=HTMLResponse)
async def radiology_admissions(request: Request, current_user=Depends(require_role(["admin", "radiologist"])), db=Depends(get_db)):
    return templates.TemplateResponse(
        "radiology/admissions.htm",
        {"request": request, "current_user": current_user, "active_page": "radiology", "admissions": radiology_admission_rows(db)},
    )


@router.get("/report/{admission_id}", response_class=HTMLResponse)
async def report_form(request: Request, admission_id: int, current_user=Depends(require_role(["admin", "radiologist"])), db=Depends(get_db)):
    admission = get_admission(db, admission_id)
    if not admission:
        return RedirectResponse(url="/radiology/admissions", status_code=302)
    return templates.TemplateResponse(
        "radiology/report_form.htm",
        {"request": request, "current_user": current_user, "active_page": "radiology", "admission": admission, "report": get_radiology_report(db, admission_id)},
    )


@router.post("/report/{admission_id}")
async def create_report(
    request: Request,
    admission_id: int,
    report_text: str = Form(...),
    images: List[UploadFile] = File(None),
    current_user=Depends(require_role(["admin", "radiologist"])),
    db=Depends(get_db),
):
    admission = get_admission(db, admission_id)
    if not admission:
        return RedirectResponse(url="/radiology/admissions", status_code=302)

    upload_errors = []
    validated_files = []
    if images and images[0].filename:
        for image_file in images:
            if image_file and image_file.filename:
                content = await image_file.read()
                is_valid, error_msg = validate_image_file(image_file.filename, image_file.content_type, len(content))
                if not is_valid:
                    upload_errors.append(f"{image_file.filename}: {error_msg}")
                else:
                    validated_files.append((image_file.filename, content))

    if upload_errors:
        return templates.TemplateResponse(
            "radiology/report_form.htm",
            {
                "request": request,
                "current_user": current_user,
                "active_page": "radiology",
                "admission": admission,
                "report": get_radiology_report(db, admission_id),
                "messages": [{"type": "danger", "text": "<br>".join(upload_errors)}],
            },
        )

    report = get_radiology_report(db, admission_id)
    if report:
        db.execute("UPDATE radiology_reports SET report_text = ? WHERE id = ?", (report_text, report.id))
        report_id = report.id
    else:
        cur = db.execute(
            "INSERT INTO radiology_reports (admission_id, report_text, created_at, created_by) VALUES (?, ?, ?, ?)",
            (admission_id, report_text, now(), current_user.id),
        )
        report_id = cur.lastrowid

    for original_filename, content in validated_files:
        ext = os.path.splitext(original_filename)[1].lower()
        filename = f"{uuid.uuid4()}{ext}"
        with open(os.path.join(UPLOAD_DIR, filename), "wb") as f:
            f.write(content)
        db.execute(
            "INSERT INTO radiology_images (report_id, filename, uploaded_at) VALUES (?, ?, ?)",
            (report_id, filename, now()),
        )
    db.commit()
    return RedirectResponse(url=f"/radiology/report/{admission_id}", status_code=302)


@router.post("/complete/{admission_id}")
async def complete_admission(admission_id: int, current_user=Depends(require_role(["admin", "radiologist"])), db=Depends(get_db)):
    db.execute("UPDATE admissions SET status = 'completed', completed_at = ? WHERE id = ?", (now(), admission_id))
    db.commit()
    return RedirectResponse(url="/radiology/admissions", status_code=302)
