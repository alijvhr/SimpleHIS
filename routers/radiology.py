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
    # Create report
    report = RadiologyReport(
        admission_id=admission_id,
        report_text=report_text,
        created_by=current_user.id
    )
    
    db.add(report)
    db.flush()
    
    # Handle image uploads
    if images and images[0].filename:
        for image_file in images:
            if image_file and image_file.filename:
                # Generate unique filename
                ext = os.path.splitext(image_file.filename)[1]
                filename = f"{uuid.uuid4()}{ext}"
                filepath = os.path.join(UPLOAD_DIR, filename)
                
                # Save file
                with open(filepath, "wb") as f:
                    content = await image_file.read()
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
