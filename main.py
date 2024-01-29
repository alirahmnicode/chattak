from typing import Annotated
from fastapi import Depends, FastAPI, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from dbmanagement.schemas import User

from routers import users, chat, auth
from dbmanagement import models, crud
from dbmanagement.database import engine
from utilities.user_auth import get_current_user

from dependencies.dependencies import get_db

app = FastAPI()

app.include_router(users.router)
app.include_router(chat.router)
app.include_router(auth.router)

templates = Jinja2Templates(directory="templates")

models.Base.metadata.create_all(bind=engine)


@app.get("/")
async def home(
    request: Request,
):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
    )

@app.get("/message")
async def message(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token").split(" ")[1]
    user = await get_current_user(token=token, db=db)
    user_contacts = crud.get_user_contacts(db=db, user_id=user.id)
    return templates.TemplateResponse(
        request=request,
        name="message.html",
        context={"user": user, "contacts": user_contacts},
    )
