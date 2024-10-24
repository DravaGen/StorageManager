from redis.asyncio import Redis

from fastapi import HTTPException

from sqlalchemy import insert, update, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import UsersORM
from .schemas import UserSchema, UserCreateForm, UserUpdateForm
from ..auth.schemas import AccessTokenResponse
from ..auth.services import hash_password, create_token
from ..base_response import ResponseOK


class UserServices:

    @staticmethod
    async def get_user_by_id(
            user_id: int,
            db: AsyncSession
    ) -> UserSchema | None:
        """"""

        user = await db.scalars(
            select(UsersORM)
            .where(UsersORM.id == user_id)
        )
        user = user.first()

        return UserSchema.model_validate(user) if user else None

    @classmethod
    async def create_user(
            cls,
            create_form: UserCreateForm,
            db: AsyncSession,
            redis_cursor: Redis
    ) -> AccessTokenResponse:
        """Создает нового пользователя и выдает доступ к функционалу"""

        exist_user = await db.execute(
            select(UsersORM)
            .where(UsersORM.email == create_form.email)
        )
        if exist_user.scalar():
            raise HTTPException(status_code=409, detail="Email already exists")

        user = await db.execute(
            insert(UsersORM)
            .values(**create_form.model_dump())
            .returning(UsersORM.id)
        )
        user_id = user.scalar()

        await cls.update_user_data(
            user_id,
            UserUpdateForm(password=create_form.password),
            db
        )

        return AccessTokenResponse(
            access_token=await create_token(user_id, redis_cursor)
        )

    @staticmethod
    async def update_user_data(
            user_id: int,
            update_form: UserUpdateForm,
            db: AsyncSession
    ) -> ResponseOK:
        """Обновляет данные пользователя"""

        if update_form.password:
            update_form.password = hash_password(
                user_id, update_form.password
            )

        await db.execute(
            update(UsersORM)
            .where(UsersORM.id == user_id)
            .values(**update_form.model_dump(exclude_unset=True))
        )

        return ResponseOK()
