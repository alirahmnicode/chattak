from typing import Annotated, List

from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session

from dbmanagement import models, schemas
from dbmanagement import crud
from dbmanagement.crud import create_user
from utilities.user_auth import create_access_token, authenticate_user, get_current_user
from .models import Token
from dependencies.dependencies import get_db


router = APIRouter()


@router.post("/signup/")
async def user_register(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
) -> Token:
    db_user = crud.get_object(db=db, model=models.User, username=user.username)

    if db_user is None:
        new_user = create_user(db=db, user=user)
        access_token = create_access_token(data={"sub": new_user.username})
        return Token(access_token=access_token, token_type="bearer")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this username is already exist!",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/login/")
async def login(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
) -> Token:
    db_user = crud.get_object(db=db, model=models.User, username=user.username)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    else:
        is_authenticate = authenticate_user(user_in_db=db_user, password=user.password)
        if is_authenticate:
            access_token = create_access_token(data={"sub": user.username})
            return Token(access_token=access_token, token_type="bearer")


@router.get("/contacts/", response_model=List[schemas.Contact])
async def contacts(
    current_user: Annotated[schemas.User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    user_contacts = crud.get_user_contacts(db=db, user_id=current_user.id)
    return user_contacts


@router.post("/contacts/{contact_id}/")
async def contacts(
    current_user: Annotated[schemas.User, Depends(get_current_user)],
    contact_id: int,
    db: Session = Depends(get_db),
):
    new_contact = crud.create_user_contact(
        db=db, owner_id=current_user.id, contact_id=contact_id
    )
    return new_contact


@router.get("/me/", response_model=schemas.User)
def me(
    current_user: Annotated[schemas.User, Depends(get_current_user)],
):
    return current_user


@router.get("/search/", response_model=List[schemas.User])
def search_user(
    current_user: Annotated[schemas.User, Depends(get_current_user)],
    username: str | None = None,
    db=Depends(get_db),
):
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username cannot be none! user query parameter.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    users = crud.search_user(db=db, username=username)
    return users
