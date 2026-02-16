from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models.user import User, UserRole
from auth import require_role, get_password_hash

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")

@router.get("/users", response_class=HTMLResponse)
async def users_list(
    request: Request,
    current_user: User = Depends(require_role(['admin'])),
    db: Session = Depends(get_db)
):
    """List all users"""
    users = db.query(User).all()
    
    return templates.TemplateResponse(
        "admin/users.htm",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "users",
            "users": users
        }
    )

@router.get("/users/new", response_class=HTMLResponse)
async def new_user_form(
    request: Request,
    current_user: User = Depends(require_role(['admin'])),
):
    """New user form"""
    return templates.TemplateResponse(
        "admin/user_form.htm",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "users",
            "user": None
        }
    )

@router.post("/users/new")
async def create_user(
    request: Request,
    username: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    role: str = Form(...),
    current_user: User = Depends(require_role(['admin'])),
    db: Session = Depends(get_db)
):
    """Create new user"""
    # Validate password
    if password != password_confirm:
        return templates.TemplateResponse(
            "admin/user_form.htm",
            {
                "request": request,
                "current_user": current_user,
                "active_page": "users",
                "user": None,
                "messages": [{"type": "danger", "text": "رمز عبور و تکرار آن مطابقت ندارد"}]
            }
        )
    
    # Check if username exists
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        return templates.TemplateResponse(
            "admin/user_form.htm",
            {
                "request": request,
                "current_user": current_user,
                "active_page": "users",
                "user": None,
                "messages": [{"type": "danger", "text": "این نام کاربری قبلا استفاده شده است"}]
            }
        )
    
    user = User(
        username=username,
        full_name=full_name,
        password_hash=get_password_hash(password),
        role=UserRole(role),
        is_active=True,
        created_by=current_user.id
    )
    
    db.add(user)
    db.commit()
    
    return RedirectResponse(url="/admin/users", status_code=302)

@router.get("/users/{user_id}/edit", response_class=HTMLResponse)
async def edit_user_form(
    request: Request,
    user_id: int,
    current_user: User = Depends(require_role(['admin'])),
    db: Session = Depends(get_db)
):
    """Edit user form"""
    user = db.query(User).filter(User.id == user_id).first()
    
    return templates.TemplateResponse(
        "admin/user_form.htm",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "users",
            "user": user
        }
    )

@router.post("/users/{user_id}/edit")
async def update_user(
    request: Request,
    user_id: int,
    full_name: str = Form(...),
    role: str = Form(...),
    new_password: str = Form(None),
    current_user: User = Depends(require_role(['admin'])),
    db: Session = Depends(get_db)
):
    """Update user"""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.full_name = full_name
        user.role = UserRole(role)
        
        if new_password:
            user.password_hash = get_password_hash(new_password)
        
        db.commit()
    
    return RedirectResponse(url="/admin/users", status_code=302)

@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(require_role(['admin'])),
    db: Session = Depends(get_db)
):
    """Deactivate user"""
    user = db.query(User).filter(User.id == user_id).first()
    if user and user.id != current_user.id:  # Can't deactivate self
        user.is_active = False
        db.commit()
    
    return RedirectResponse(url="/admin/users", status_code=302)

@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: int,
    current_user: User = Depends(require_role(['admin'])),
    db: Session = Depends(get_db)
):
    """Activate user"""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.is_active = True
        db.commit()
    
    return RedirectResponse(url="/admin/users", status_code=302)
