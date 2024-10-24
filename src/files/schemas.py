from typing import Optional
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field, model_validator, field_validator


class FileSchema(BaseModel):
    """Схема файла"""

    id: int  # Идентификатор
    owner_id: int  # Пользователь которую принадлежит файл
    name: str  # Название файла
    extension: str  # Расширение файла
    size: int  # Размер файда в байтах
    path: str  # Путь к файлу
    created_at: datetime = Field(datetime.now().isoformat())  # Дата создания файла
    updated_at: datetime | None = None  # Дата обновления файла
    comment: str | None = Field(None, max_length=255)  # Коментарий к файлу

    class Config:
        from_attributes = True

    @staticmethod
    def get_full_name(name: str, extension: str) -> str:
        """Название файла с расширением в зависимости от данных"""

        return f"{name}.{extension}"

    @property
    def full_name(self) -> str:
        """Название файла с расширением"""

        return self.get_full_name(self.name, self.extension)

    @property
    def directory(self) -> Path:
        """Возвращает директорию где лежит файл"""

        return Path(self.path)

    @staticmethod
    def get_full_path(directory: str, full_name: str) -> Path:
        """Возвращает путь к файлу в зависимости от данных"""

        return Path(directory, full_name)

    @property
    def full_path(self):
        """Возвращает полный путь к файлу"""

        return self.get_full_path(self.directory, self.full_name)


class FileCreateSchema(BaseModel):
    """Схема создания файла"""

    name: str = Field(..., max_length=255)
    extension: str = Field(..., max_length=10)
    size: int = Field(..., ge=0,  le=2147483647)
    path: str = Field(..., max_length=255)


class FileUpdateForm(BaseModel):
    """Схема для обновления данных файла"""

    name: Optional[str] = Field(
        None,
        max_length=265,
        description="Имя файла"
    )
    path: Optional[str] = Field(
        None,
        max_length=255,
        description="Путь к файлу"
    )
    comment: Optional[str] = Field(
        None,
        max_length=255,
        description="Комментарий к файлу"
    )

    @model_validator(mode="after")
    def validate_params(self):
        """Проверяет что форма не пустая"""

        if not any(self.model_dump().values()):
            raise ValueError("an empty request")

        return self


class FailFilesInitialization(Exception):
    """Исключение которое пробрасывается при неудачной инициализации файлов"""
    pass
