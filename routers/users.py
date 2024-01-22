from typing import Annotated
from typing_extensions import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from dbmanagement import schemas
from dbmanagement.crud import create_user, get_user_by_username
from utilities.user_auth import create_access_token, authenticate_user
from .models import Token
from dependencies.dependencies import get_db


router = APIRouter()


@router.post("/signup/")
async def user_register(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
) -> Token:
    new_user = create_user(db=db, user=user)
    access_token = create_access_token(data={"sub": new_user.username})
    return Token(access_token=access_token, token_type="bearer")


@router.post("/login/")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
) -> Token:
    user = get_user_by_username(db=db, username=form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    else:
        is_authenticate = authenticate_user(
            user_in_db=user, password=form_data.password
        )
        if is_authenticate:
            access_token = create_access_token(data={"sub": user.username})
            return Token(access_token=access_token, token_type="bearer")
