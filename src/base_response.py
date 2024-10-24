from pydantic import BaseModel


class ResponseOK(BaseModel):
    """Схема базового ответа"""

    response: str = "ok"
