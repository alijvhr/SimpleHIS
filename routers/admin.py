from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from auth import require_role, get_password_hash
from database import all_rows, get_db, one, now

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")


def users(db):
    return all_rows(db, "SELECT * FROM users ORDER BY id")


@router.get("/users", response_class=HTMLResponse)
async def users_list(request: Request, current_user=Depends(require_role(["admin"])), db=Depends(get_db)):
    return templates.TemplateResponse(
        "admin/users.htm",
        {"request": request, "current_user": current_user, "active_page": "users", "users": users(db)},
    )


@router.get("/users/new", response_class=HTMLResponse)
async def new_user_form(request: Request, current_user=Depends(require_role(["admin"]))):
    return templates.TemplateResponse(
        "admin/user_form.htm",
        {"request": request, "current_user": current_user, "active_page": "users", "user": None},
    )


@router.post("/users/new")
async def create_user(
    request: Request,
    username: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    current_user=Depends(require_role(["admin"])),
    db=Depends(get_db),
):
    db.execute(
        """
        INSERT INTO users (username, full_name, password_hash, role, is_active, created_at, created_by)
        VALUES (?, ?, ?, ?, 1, ?, ?)
        """,
        (username, full_name, get_password_hash(password), role, now(), current_user.id),
    )
    db.commit()
    return RedirectResponse(url="/admin/users", status_code=302)


@router.get("/users/{user_id}/edit", response_class=HTMLResponse)
async def edit_user_form(request: Request, user_id: int, current_user=Depends(require_role(["admin"])), db=Depends(get_db)):
    return templates.TemplateResponse(
        "admin/user_form.htm",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "users",
            "user": one(db, "SELECT * FROM users WHERE id = ?", (user_id,)),
        },
    )


@router.post("/users/{user_id}/edit")
async def update_user(
    request: Request,
    user_id: int,
    username: str = Form(...),
    full_name: str = Form(...),
    role: str = Form(...),
    new_password: str = Form(None),
    current_user=Depends(require_role(["admin"])),
    db=Depends(get_db),
):
    if new_password:
        db.execute(
            "UPDATE users SET username = ?, full_name = ?, role = ?, password_hash = ? WHERE id = ?",
            (username, full_name, role, get_password_hash(new_password), user_id),
        )
    else:
        db.execute("UPDATE users SET username = ?, full_name = ?, role = ? WHERE id = ?", (username, full_name, role, user_id))
    db.commit()
    return RedirectResponse(url="/admin/users", status_code=302)


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(request: Request, user_id: int, current_user=Depends(require_role(["admin"])), db=Depends(get_db)):
    db.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user_id,))
    db.commit()
    return RedirectResponse(url="/admin/users", status_code=302)


@router.post("/users/{user_id}/activate")
async def activate_user(request: Request, user_id: int, current_user=Depends(require_role(["admin"])), db=Depends(get_db)):
    db.execute("UPDATE users SET is_active = 1 WHERE id = ?", (user_id,))
    db.commit()
    return RedirectResponse(url="/admin/users", status_code=302)


@router.post("/users/{user_id}/delete")
async def delete_user(request: Request, user_id: int, current_user=Depends(require_role(["admin"])), db=Depends(get_db)):
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()
    return RedirectResponse(url="/admin/users", status_code=302)
