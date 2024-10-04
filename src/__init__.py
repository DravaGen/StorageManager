from config import Config
from .services import FileService


if not Config.BASE_DIRECTORY.exists():
    Config.BASE_DIRECTORY.mkdir(parents=True, exist_ok=True)

FileService.files_initialization()
