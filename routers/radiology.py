from fastapi import APIRouter, Request, Depends, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List
import os
import uuid
from database import get_db
from models.user import User
from models.admission import Admission, AdmissionStatus, AdmissionType
from models.radiology import RadiologyReport, RadiologyImage
from auth import require_auth, require_role
from utils.validators import validate_image_file

router = APIRouter(prefix="/radiology", tags=["radiology"])
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/admissions", response_class=HTMLResponse)
async def radiology_admissions(
    request: Request,
    current_user: User = Depends(require_role(['admin', 'radiologist'])),
    db: Session = Depends(get_db)
):
    """List radiology admissions"""
    admissions = db.query(Admission).filter(
        Admission.admission_type == AdmissionType.radiology,
        Admission.status.in_([AdmissionStatus.paid, AdmissionStatus.completed])
    ).all()
    
    return templates.TemplateResponse(
        "radiology/admissions.htm",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "radiology",
            "admissions": admissions
        }
    )

@router.get("/report/{admission_id}", response_class=HTMLResponse)
async def report_form(
    request: Request,
    admission_id: int,
    current_user: User = Depends(require_role(['admin', 'radiologist'])),
    db: Session = Depends(get_db)
):
    """Radiology report form"""
    admission = db.query(Admission).filter(Admission.id == admission_id).first()
    report = db.query(RadiologyReport).filter(RadiologyReport.admission_id == admission_id).first()
    
    return templates.TemplateResponse(
        "radiology/report_form.htm",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "radiology",
            "admission": admission,
            "report": report
        }
    )

@router.post("/report/{admission_id}")
async def create_report(
    request: Request,
    admission_id: int,
    report_text: str = Form(...),
    images: List[UploadFile] = File(None),
    current_user: User = Depends(require_role(['admin', 'radiologist'])),
    db: Session = Depends(get_db)
):
    """Create radiology report"""
    # Handle image uploads with validation
    upload_errors = []
    if images and images[0].filename:
        for image_file in images:
            if image_file and image_file.filename:
                # Read file content to get size
                content = await image_file.read()
                file_size = len(content)
                
                # Validate image
                is_valid, error_msg = validate_image_file(
                    image_file.filename,
                    image_file.content_type,
                    file_size
                )
                
                if not is_valid:
                    upload_errors.append(f"{image_file.filename}: {error_msg}")
                    continue
                
    # If there are validation errors, return to form
    if upload_errors:
        admission = db.query(Admission).filter(Admission.id == admission_id).first()
        return templates.TemplateResponse(
            "radiology/report_form.htm",
            {
                "request": request,
                "current_user": current_user,
                "active_page": "admissions",
                "admission": admission,
                "messages": [{"type": "danger", "text": "<br>".join(upload_errors)}]
            }
        )
    
    # Create report
    report = RadiologyReport(
        admission_id=admission_id,
        report_text=report_text,
        created_by=current_user.id
    )
    
    db.add(report)
    db.flush()
    
    # Save validated images
    if images and images[0].filename:
        for image_file in images:
            if image_file and image_file.filename:
                # Re-read content (it was consumed during validation)
                await image_file.seek(0)
                content = await image_file.read()
                
                # Generate unique filename
                ext = os.path.splitext(image_file.filename)[1].lower()
                filename = f"{uuid.uuid4()}{ext}"
                filepath = os.path.join(UPLOAD_DIR, filename)
                
                # Save file
                with open(filepath, "wb") as f:
                    f.write(content)
                
                # Create image record
                img = RadiologyImage(
                    report_id=report.id,
                    filename=filename
                )
                db.add(img)
    
    db.commit()
    
    return RedirectResponse(url=f"/radiology/report/{admission_id}", status_code=302)

@router.post("/complete/{admission_id}")
async def complete_admission(
    admission_id: int,
    current_user: User = Depends(require_role(['admin', 'radiologist'])),
    db: Session = Depends(get_db)
):
    """Complete radiology admission"""
    admission = db.query(Admission).filter(Admission.id == admission_id).first()
    if admission:
        admission.status = AdmissionStatus.completed
        admission.completed_at = datetime.now(timezone.utc)
        db.commit()
    
    return RedirectResponse(url="/radiology/admissions", status_code=302)
