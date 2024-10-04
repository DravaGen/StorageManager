import os
from dotenv import load_dotenv
from pathlib import Path
from distutils.util import strtobool


load_dotenv()


class Config:
    """Общие настройки"""

    NAME = "StorageManager"  # Название проекта
    BASE_DIRECTORY = Path(os.getenv("BASE_DIRECTORY"))  # Базовое расположение файлов

    DEBUG = strtobool(os.getenv("DEBUG"))  # Режим отладки


class PostgreSQLConfig:
    """Настройки PostgreSQL"""

    DB_USER = os.getenv("PSQL_USER")  # Пользователь базы данных
    DB_PASSWORD = os.getenv("PSQL_PASSWORD")  # Пароль от базы данных
    DB_NAME = os.getenv("PSQL_DATABASE")  # Имя базы данных
    DB_HOST = os.getenv("PSQL_HOST") or "localhost"  # Хостинг базы данных
    DB_PORT = os.getenv("PSQL_PORT") or "5432"  # Порт базы данных


class FastApiConfig:
    """Настройки FastApi"""

    TITLE = Config.NAME  # Название api
    VERSION = "0.0.1"  # Версия api
    DESCRIPTION = f"API для работы с {Config.NAME}"  # Описание api
