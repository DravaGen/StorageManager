from fastapi import APIRouter, Depends

from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import AccessTokenResponse
from .services import get_user_by_email, hash_password, create_token, \
    delete_token, check_auth, oauth2_schema
from ..databases.aioredis import get_redis_cursor
from ..databases.sqlalchemy import get_db
from ..base_response import ResponseOK


auth_router = APIRouter()


@auth_router.post("/login", response_model=AccessTokenResponse)
async def login(
        login_form: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db),
        redis_cursor: AsyncSession = Depends(get_redis_cursor)
) -> AccessTokenResponse:
    """Авторизует пользователя по email через форму"""

    user = await get_user_by_email(login_form.username, db)

    if (
        user is None or
        user.password != hash_password(
            user.id, login_form.password
        )
    ):
        raise HTTPException(status_code=403, detail="Incorrect auth data")

    return AccessTokenResponse(
        access_token=await create_token(user.id, redis_cursor)
    )


@auth_router.delete(
    "/logout",
    response_model=ResponseOK,
    dependencies=[Depends(check_auth)]
)
async def logout(
        access_token: str = Depends(oauth2_schema),
        redis_cursor: Redis = Depends(get_redis_cursor)
) -> ResponseOK:
    """Выходит и удаляет даные о токене"""

    await delete_token(access_token, redis_cursor)

    return ResponseOK
