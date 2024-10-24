from fastapi import FastAPI

from config import Config, FastApiConfig
from src.auth.handlers import auth_router
from src.files.handlers import files_router
from src.users.handlers import users_router


app = FastAPI(
    title=FastApiConfig.TITLE,
    description=FastApiConfig.DESCRIPTION,
    version=FastApiConfig.VERSION,
    debug=Config.DEBUG
)

app.include_router(
    auth_router,
    prefix="/auth",
    tags=["Auth"],
    include_in_schema=Config.DEBUG
)

app.include_router(files_router, prefix="/files", tags=["Files"])
app.include_router(users_router, prefix="/users", tags=["Users"])
