from fastapi import APIRouter, Depends, Body
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import UserSchema, UserCreateForm, UserUpdateForm
from .services import UserServices
from ..auth.schemas import AccessTokenResponse
from ..auth.services import get_user_id
from ..databases.aioredis import get_redis_cursor
from ..databases.sqlalchemy import get_db
from ..base_response import ResponseOK


users_router = APIRouter()


@users_router.post("/", response_model=AccessTokenResponse)
async def create_users(
        create_form: UserCreateForm,
        db: AsyncSession = Depends(get_db),
        redis_cursor: Redis = Depends(get_redis_cursor)
) -> AccessTokenResponse:
    """Создает пользователя"""

    return await UserServices.create_user(create_form, db, redis_cursor)


@users_router.get("/me", response_model=UserSchema)
async def get_user_self(
        user_id: int = Depends(get_user_id),
        db: AsyncSession = Depends(get_db)
) -> UserSchema:
    """Возвращает информацию о текущем пользователе"""

    return await UserServices.get_user_by_id(user_id, db)


@users_router.put("/me", response_model=ResponseOK)
async def update_user_self(
        user_id: int = Depends(get_user_id),
        update_form: UserUpdateForm = Body(),
        db: AsyncSession = Depends(get_db)
) -> ResponseOK:
    """Обновляет данные о текущем пользователе"""

    return await UserServices.update_user_data(user_id, update_form, db)
