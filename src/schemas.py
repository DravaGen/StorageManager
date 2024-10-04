from typing import Optional
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field, model_validator, field_validator


class FileSchema(BaseModel):
    """Схема файла"""

    id: int  # Идентификатор
    name: str  # Название файла
    extension: str  # Расширение файла
    size: int  # Размер файда в байтах
    path: str  # Путь к файлу
    created_at: datetime = Field(datetime.now(), description="YYYY-MM-Thh:mm:ss")
    # Дата создания файла (хранить в ISO .isoformat())
    updated_at: datetime | None = None
    # Дата обновления файла  (хранить в ISO .isoformat())
    comment: str | None = None  # Коментарий к файлу


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


class UpdateFileSchema(BaseModel):
    """Схема для обновления данных файла"""

    name: Optional[str] = Field(default=None, description="Имя файла")
    path: Optional[str] = Field(default=None, description="Путь к файлу")
    comment: Optional[str] = Field(default=None, description="Комментарий к файлу")


    @model_validator(mode="after")
    def validate_params(self):
        """Валидация данных"""

        if not any(self.model_dump().values()):
            raise ValueError("an empty request")

        return self


    @field_validator("name")
    @classmethod
    def validate_name(cls, name):
        """Валидирование названия файла"""

        # Проверять за запрещенные симновы 

        return name


    @field_validator("path")
    @classmethod
    def validate_path(cls, path):
        """Валидирование пути к файлу"""

        # Проверять на корректность пути

        return path


    @field_validator("comment")
    @classmethod
    def validate_comment(cls, comment):
        """Валидирование комментария"""

        # Возможные ограничения по длине

        return comment


class ResponseOK(BaseModel):
    """Схема базового ответа"""

    response: str = "ok"
