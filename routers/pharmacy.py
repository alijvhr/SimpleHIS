from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone
from typing import List
from database import get_db
from models.user import User
from models.patient import Patient
from models.drug import Drug
from models.stock import StockTransaction
from models.prescription import Prescription, PrescriptionItem, PrescriptionStatus
from auth import require_auth, require_role

router = APIRouter(prefix="/pharmacy", tags=["pharmacy"])
templates = Jinja2Templates(directory="templates")

def get_drug_stock(db: Session, drug_id: int) -> int:
    """Calculate current stock for a drug"""
    result = db.query(func.sum(StockTransaction.quantity_change)).filter(
        StockTransaction.drug_id == drug_id
    ).scalar()
    return result if result else 0

@router.get("/inventory", response_class=HTMLResponse)
async def inventory(
    request: Request,
    current_user: User = Depends(require_role(['admin', 'pharmacy'])),
    db: Session = Depends(get_db)
):
    """Drug inventory with calculated stock"""
    drugs = db.query(Drug).all()
    
    # Calculate stock for each drug
    drugs_with_stock = []
    for drug in drugs:
        stock = get_drug_stock(db, drug.id)
        drugs_with_stock.append({
            'drug': drug,
            'stock': stock
        })
    
    return templates.TemplateResponse(
        "pharmacy/inventory.htm",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "inventory",
            "drugs": drugs_with_stock
        }
    )

@router.get("/drug/new", response_class=HTMLResponse)
async def new_drug_form(
    request: Request,
    current_user: User = Depends(require_role(['admin', 'pharmacy'])),
):
    """New drug form"""
    return templates.TemplateResponse(
        "pharmacy/drug_form.htm",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "inventory",
            "drug": None
        }
    )

@router.post("/drug/new")
async def create_drug(
    request: Request,
    name: str = Form(...),
    manufacturer: str = Form(...),
    form: str = Form(...),
    dosage: str = Form(...),
    price: float = Form(...),
    min_threshold: int = Form(...),
    default_instructions: str = Form(...),
    initial_stock: int = Form(0),
    current_user: User = Depends(require_role(['admin', 'pharmacy'])),
    db: Session = Depends(get_db)
):
    """Create new drug"""
    drug = Drug(
        name=name,
        manufacturer=manufacturer,
        form=form,
        dosage=dosage,
        price=price,
        min_threshold=min_threshold,
        default_instructions=default_instructions,
        created_by=current_user.id
    )
    
    db.add(drug)
    db.flush()
    
    # Add initial stock if provided
    if initial_stock > 0:
        stock_tx = StockTransaction(
            drug_id=drug.id,
            quantity_change=initial_stock,
            reason="موجودی اولیه",
            created_by=current_user.id
        )
        db.add(stock_tx)
    
    db.commit()
    
    return RedirectResponse(url="/pharmacy/inventory", status_code=302)

@router.get("/drug/{drug_id}/edit", response_class=HTMLResponse)
async def edit_drug_form(
    request: Request,
    drug_id: int,
    current_user: User = Depends(require_role(['admin', 'pharmacy'])),
    db: Session = Depends(get_db)
):
    """Edit drug form"""
    drug = db.query(Drug).filter(Drug.id == drug_id).first()
    
    return templates.TemplateResponse(
        "pharmacy/drug_form.htm",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "inventory",
            "drug": drug
        }
    )

@router.post("/drug/{drug_id}/edit")
async def update_drug(
    request: Request,
    drug_id: int,
    name: str = Form(...),
    manufacturer: str = Form(...),
    form: str = Form(...),
    dosage: str = Form(...),
    price: float = Form(...),
    min_threshold: int = Form(...),
    default_instructions: str = Form(...),
    current_user: User = Depends(require_role(['admin', 'pharmacy'])),
    db: Session = Depends(get_db)
):
    """Update drug"""
    drug = db.query(Drug).filter(Drug.id == drug_id).first()
    if drug:
        drug.name = name
        drug.manufacturer = manufacturer
        drug.form = form
        drug.dosage = dosage
        drug.price = price
        drug.min_threshold = min_threshold
        drug.default_instructions = default_instructions
        db.commit()
    
    return RedirectResponse(url="/pharmacy/inventory", status_code=302)

@router.get("/restock", response_class=HTMLResponse)
async def restock_form(
    request: Request,
    current_user: User = Depends(require_role(['admin', 'pharmacy'])),
    db: Session = Depends(get_db)
):
    """Restock form"""
    drugs = db.query(Drug).all()
    
    return templates.TemplateResponse(
        "pharmacy/restock.htm",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "inventory",
            "drugs": drugs
        }
    )

@router.post("/restock")
async def restock(
    request: Request,
    drug_id: int = Form(...),
    quantity: int = Form(...),
    reason: str = Form(...),
    current_user: User = Depends(require_role(['admin', 'pharmacy'])),
    db: Session = Depends(get_db)
):
    """Restock drug"""
    stock_tx = StockTransaction(
        drug_id=drug_id,
        quantity_change=quantity,
        reason=reason,
        created_by=current_user.id
    )
    
    db.add(stock_tx)
    db.commit()
    
    return RedirectResponse(url="/pharmacy/inventory", status_code=302)

@router.get("/manual-prescription", response_class=HTMLResponse)
async def manual_prescription_form(
    request: Request,
    national_id: str = None,
    current_user: User = Depends(require_role(['admin', 'pharmacy'])),
    db: Session = Depends(get_db)
):
    """Manual prescription form"""
    patient = None
    
    if national_id:
        patient = db.query(Patient).filter(Patient.national_id == national_id).first()
    
    return templates.TemplateResponse(
        "pharmacy/manual_prescription.htm",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "manual_prescription",
            "patient": patient
        }
    )

@router.post("/manual-prescription")
async def create_manual_prescription(
    request: Request,
    patient_id: int = Form(...),
    total_amount: float = Form(...),
    drug_id: List[int] = Form(...),
    quantity: List[int] = Form(...),
    instructions: List[str] = Form(...),
    current_user: User = Depends(require_role(['admin', 'pharmacy'])),
    db: Session = Depends(get_db)
):
    """Create manual prescription"""
    prescription = Prescription(
        patient_id=patient_id,
        admission_id=None,
        is_manual=True,
        total_amount=total_amount,
        status=PrescriptionStatus.waiting_payment,
        created_by=current_user.id
    )
    
    db.add(prescription)
    db.flush()
    
    # Create prescription items
    for i in range(len(drug_id)):
        if drug_id[i]:
            item = PrescriptionItem(
                prescription_id=prescription.id,
                drug_id=drug_id[i],
                quantity=quantity[i],
                instructions=instructions[i]
            )
            db.add(item)
    
    db.commit()
    
    return RedirectResponse(url="/reception/cashier", status_code=302)

@router.get("/dispense", response_class=HTMLResponse)
async def dispense_list(
    request: Request,
    current_user: User = Depends(require_role(['admin', 'pharmacy'])),
    db: Session = Depends(get_db)
):
    """List paid prescriptions ready for dispensing"""
    prescriptions = db.query(Prescription).filter(
        Prescription.status == PrescriptionStatus.paid
    ).all()
    
    return templates.TemplateResponse(
        "pharmacy/dispense.htm",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "dispense",
            "prescriptions": prescriptions
        }
    )

@router.get("/dispense/{prescription_id}", response_class=HTMLResponse)
async def dispense_detail(
    request: Request,
    prescription_id: int,
    current_user: User = Depends(require_role(['admin', 'pharmacy'])),
    db: Session = Depends(get_db)
):
    """Prescription detail for dispensing"""
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    
    # Check stock availability
    stock_warnings = []
    for item in prescription.items:
        current_stock = get_drug_stock(db, item.drug_id)
        if current_stock < item.quantity:
            stock_warnings.append(
                f"{item.drug.name}: موجودی فعلی {current_stock}، نیاز به {item.quantity}"
            )
    
    return templates.TemplateResponse(
        "pharmacy/dispense_detail.htm",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "dispense",
            "prescription": prescription,
            "stock_warnings": stock_warnings
        }
    )

@router.post("/dispense/{prescription_id}/complete")
async def complete_dispense(
    request: Request,
    prescription_id: int,
    current_user: User = Depends(require_role(['admin', 'pharmacy'])),
    db: Session = Depends(get_db)
):
    """Complete prescription dispensing with stock locking"""
    # Use database transaction with FOR UPDATE to prevent race conditions
    prescription = db.query(Prescription).filter(
        Prescription.id == prescription_id
    ).with_for_update().first()
    
    if not prescription or prescription.status != PrescriptionStatus.paid:
        return RedirectResponse(url="/pharmacy/dispense", status_code=302)
    
    # Check stock availability within the transaction
    stock_errors = []
    for item in prescription.items:
        # Lock the stock transaction rows to prevent concurrent modifications
        current_stock = db.query(func.sum(StockTransaction.quantity_change)).filter(
            StockTransaction.drug_id == item.drug_id
        ).with_for_update().scalar() or 0
        
        if current_stock < item.quantity:
            stock_errors.append(f"{item.drug.name}: موجودی ناکافی")
    
    # If insufficient stock, rollback and return error
    if stock_errors:
        db.rollback()
        prescriptions = db.query(Prescription).filter(
            Prescription.status == PrescriptionStatus.paid
        ).all()
        return templates.TemplateResponse(
            "pharmacy/dispense.htm",
            {
                "request": request,
                "current_user": current_user,
                "active_page": "dispense",
                "prescriptions": prescriptions,
                "messages": [{"type": "danger", "text": "<br>".join(stock_errors)}]
            }
        )
    
    # Reduce stock for each item (within the locked transaction)
    for item in prescription.items:
        stock_tx = StockTransaction(
            drug_id=item.drug_id,
            quantity_change=-item.quantity,
            reason=f"تحویل نسخه {prescription_id}",
            created_by=current_user.id
        )
        db.add(stock_tx)
    
    # Update prescription status
    prescription.status = PrescriptionStatus.dispensed
    prescription.dispensed_at = datetime.now(timezone.utc)
    prescription.dispensed_by = current_user.id
    
    db.commit()
    
    return RedirectResponse(url="/pharmacy/dispense", status_code=302)

@router.get("/search", response_class=HTMLResponse)
async def search_prescriptions(
    request: Request,
    prescription_id: int = None,
    national_id: str = None,
    current_user: User = Depends(require_role(['admin', 'pharmacy'])),
    db: Session = Depends(get_db)
):
    """Search prescriptions"""
    prescriptions = []
    
    if prescription_id:
        prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
        if prescription:
            prescriptions = [prescription]
    elif national_id:
        prescriptions = db.query(Prescription).join(Patient).filter(
            Patient.national_id == national_id
        ).order_by(Prescription.created_at.desc()).all()
    
    return templates.TemplateResponse(
        "pharmacy/search_prescriptions.htm",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "search_prescriptions",
            "prescriptions": prescriptions,
            "prescription_id": prescription_id,
            "national_id": national_id
        }
    )

@router.get("/prescription/{prescription_id}", response_class=HTMLResponse)
async def view_prescription(
    request: Request,
    prescription_id: int,
    current_user: User = Depends(require_role(['admin', 'pharmacy'])),
    db: Session = Depends(get_db)
):
    """View prescription detail"""
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    
    return templates.TemplateResponse(
        "pharmacy/dispense_detail.htm",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "search_prescriptions",
            "prescription": prescription,
            "stock_warnings": []
        }
    )
