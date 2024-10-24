import random
import hashlib
from string import ascii_lowercase, digits

from redis.asyncio import Redis

from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..users.models import UsersORM
from ..databases.aioredis import get_redis_cursor


oauth2_schema = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_user_by_email(
        email: str,
        db: AsyncSession
) -> UsersORM | None:
    """Возвращает данные пользователя по имени"""

    user = await db.scalars(
        select(UsersORM)
        .where(UsersORM.email == email)
    )
    user = user.first()

    return user


def hash_password(
        user_id: int,
        password: int
) -> str:
    """
        Возвращает пароль в хэшированном виде,
            как он хранится в базе данных
    """

    return hashlib.md5(f"{user_id}|{password}".encode()).hexdigest()


def generate_access_token() -> str:
    """Генерирует токен доступа"""

    return ''.join(random.choices(ascii_lowercase + digits, k=32))


async def get_user_id_by_token(
        access_token: str,
        redis_cursor: Redis
) -> int | None:
    """Возвращает идентификатор пользователя с помощью токена"""

    user_id = await redis_cursor.get(f"user_token:{access_token}")
    return int(user_id) if user_id else None


async def create_token(
        user_id: int,
        redis_cursor: Redis
) -> str:
    """Создает и возвращает токен доступа который принадлежит пользователю"""

    access_tokens = generate_access_token()

    await redis_cursor.set(
        f"user_token:{access_tokens}",
        user_id
    )

    return access_tokens


async def delete_token(
        access_token: str,
        redis_cursor: Redis
) -> None:
    """Удаляет токен доступа"""

    await redis_cursor.delete(f'user_token:{access_token}')


async def get_user_id(
        access_token: str = Depends(oauth2_schema),
        redis_cursor: Redis = Depends(get_redis_cursor)
) -> int:
    """
        Возвращает идентификатор пользователя по 'Authorization' header

        Если access_token передан, но недействителен,
            возникает сообщение 401 UNAUTHORIZED
    """

    user_id = await get_user_id_by_token(access_token, redis_cursor)

    if user_id is None:
        raise HTTPException(status_code=401)

    return user_id


async def check_auth(
        user_id: int = Depends(get_user_id)
) -> None:
    """Проверяет аутентификацию"""
    pass
