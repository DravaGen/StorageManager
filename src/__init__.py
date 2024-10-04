from config import Config
from .services import FileService


if Config.BASE_DIRECTORY.exists() is False:
    Config.BASE_DIRECTORY.mkdir(exist_ok=True)

FileService.files_initialization()
