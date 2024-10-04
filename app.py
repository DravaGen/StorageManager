from fastapi import FastAPI

from config import FastApiConfig
from src.handlers import api_router


app = FastAPI(
    title=FastApiConfig.TITLE,
    description=FastApiConfig.DESCRIPTION,
    version=FastApiConfig.VERSION
)
app.include_router(api_router)
