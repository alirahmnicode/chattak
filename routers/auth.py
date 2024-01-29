import json
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi import responses, status, Form
from sqlalchemy.orm import Session
from pydantic.error_wrappers import ValidationError

from dbmanagement import schemas, crud
from dependencies.dependencies import get_db
from utilities.user_auth import authenticate_user, create_access_token

templates = Jinja2Templates(directory="templates")
router = APIRouter()


@router.get("/register")
def register(request: Request):
    return templates.TemplateResponse("auth/register.html", {"request": request})


@router.post("/register")
def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    errors = []
    try:
        user = schemas.UserCreate(username=username, email=email, password=password)
        crud.create_user(user=user, db=db)
        return responses.RedirectResponse(
            "/?alert=Successfully%20Registered", status_code=status.HTTP_302_FOUND
        )
    except ValidationError as e:
        errors_list = json.loads(e.json())
        for item in errors_list:
            errors.append(item.get("loc")[0] + ": " + item.get("msg"))
        return templates.TemplateResponse(
            "auth/register.html", {"request": request, "errors": errors}
        )
    
@router.get("/login")
def login(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.post("/login")
def login(request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    errors = []
    user = crud.get_user_by_username(username=username, db=db)
    
    if not user:
        errors.append("Incorrect email or password")
        return templates.TemplateResponse("auth/login.html", {"request": request,"errors":errors})
    
    is_authenticate = authenticate_user(user, password)

    if is_authenticate:
        access_token = create_access_token(data={"sub": user.username})
        response = responses.RedirectResponse(
                "/?alert=Successfully Logged In", status_code=status.HTTP_302_FOUND
            )
        response.set_cookie(key="access_token",value=f"Bearer {access_token}",httponly=True)
        return response
