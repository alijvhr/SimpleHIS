from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import get_db
from models.drug import Drug

router = APIRouter(prefix="/api", tags=["api"])

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
