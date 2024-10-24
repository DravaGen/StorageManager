from typing import Optional

from pydantic import EmailStr

from pydantic import BaseModel, Field, model_validator


class UserCreateForm(BaseModel):
    """Схема создания пользователя"""

    name: str = Field(..., max_length=30)
    email: str = Field(
        ...,
        pattern=r"^[a-zA-Z0-9]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
        max_length=40
    )
    password: str = Field(..., min_length=8, max_length=32)


class UserUpdateForm(BaseModel):
    """Схема обновления данных пользователя"""

    name: Optional[str] = Field(None, max_length=30)
    email: Optional[str] = Field(None, max_length=40)
    password: Optional[str] = Field(None, min_length=8, max_length=32)

    @model_validator(mode="after")
    def validate_path(self):
        """Проверяет что форма не пустая"""

        if not any(self.model_dump().values()):
            raise ValueError("an empty request")

        return self


class UserSchema(BaseModel):
    """Схема пользователя"""

    id: int
    name: str
    email: str
    password: str

    class Config:
        from_attributes = True
