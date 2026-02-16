from fastapi import APIRouter, Request, Depends, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from auth import verify_password, create_access_token, get_current_user_from_cookie, require_auth

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def root():
    """Redirect root to home"""
    return RedirectResponse(url="/home", status_code=302)

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("common/login.htm", {"request": request})

@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Login endpoint"""
    user = db.query(User).filter(User.username == username, User.is_active == True).first()
    
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "common/login.htm",
            {"request": request, "error": "نام کاربری یا رمز عبور اشتباه است"}
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user.id})
    
    # Redirect to home with cookie
    response = RedirectResponse(url="/home", status_code=302)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=28800,  # 8 hours
        samesite="lax"
    )
    return response

@router.get("/logout")
async def logout():
    """Logout endpoint"""
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response

@router.get("/home", response_class=HTMLResponse)
async def home(request: Request, current_user: User = Depends(require_auth)):
    """Home dashboard"""
    return templates.TemplateResponse(
        "common/home.htm",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "home"
        }
    )

@router.get("/print/prescription/{prescription_id}", response_class=HTMLResponse)
async def print_prescription(
    request: Request,
    prescription_id: int,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Print prescription"""
    from models.prescription import Prescription
    
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    
    return templates.TemplateResponse(
        "print/prescription.htm",
        {
            "request": request,
            "prescription": prescription
        }
    )
