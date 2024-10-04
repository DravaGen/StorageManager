from fastapi import FastAPI

from config import Config, FastApiConfig
from src.handlers import api_router


app = FastAPI(
    title=FastApiConfig.TITLE,
    description=FastApiConfig.DESCRIPTION,
    version=FastApiConfig.VERSION,
    debug=Config.DEBUG
)
app.include_router(api_router)
