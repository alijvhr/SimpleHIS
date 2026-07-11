from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from auth import verify_password, create_access_token, get_current_user_from_cookie, require_auth, ACCESS_TOKEN_EXPIRE_MINUTES
from database import get_db, get_prescription, one

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def root(request: Request, db=Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    return RedirectResponse(url="/home" if user else "/login", status_code=302)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    error = "نام کاربری یا رمز عبور اشتباه است" if request.query_params.get("error") == "1" else None
    return templates.TemplateResponse("common/login.htm", {"request": request, "error": error})


@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...), db=Depends(get_db)):
    user = one(db, "SELECT * FROM users WHERE username = ? AND is_active = 1", (username,))

    if not user or not verify_password(password, user.password_hash):
        return RedirectResponse(url="/login?error=1", status_code=302)

    response = RedirectResponse(url="/home", status_code=302)
    response.set_cookie(
        key="access_token",
        value=create_access_token(data={"sub": user.id}),
        path="/",
        httponly=False,
        secure=False,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(key="access_token", path="/")
    return response


@router.get("/debug")
async def debug(request: Request):
    return {"cookies": dict(request.cookies)}


@router.get("/home", response_class=HTMLResponse)
async def home(request: Request, current_user=Depends(require_auth)):
    return templates.TemplateResponse(
        "common/home.htm",
        {"request": request, "current_user": current_user, "active_page": "home"},
    )


@router.get("/print/prescription/{prescription_id}", response_class=HTMLResponse)
async def print_prescription(
    request: Request,
    prescription_id: int,
    current_user=Depends(require_auth),
    db=Depends(get_db),
):
    return templates.TemplateResponse(
        "print/prescription.htm",
        {"request": request, "prescription": get_prescription(db, prescription_id)},
    )
