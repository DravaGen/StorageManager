import shutil
import aiofiles
import traceback

from typing import Optional
from pathlib import Path

from fastapi import UploadFile, HTTPException
from fastapi.responses import FileResponse

from pydantic import ValidationError

from sqlalchemy import insert, update, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import Config

from .models import FilesORM
from .schemas import FileSchema, FileCreateSchema, FileUpdateForm, \
    FailFilesInitialization
from ..databases.sqlalchemy import session_factory
from ..base_response import ResponseOK


class FileService:

    @staticmethod
    async def get_my_files(
            user_id: int,
            db: AsyncSession
    ) -> list[Optional[FileSchema]]:
        """Возвращает все файлы которые есть в базе данных"""

        files = await db.scalars(
            select(FilesORM)
            .where(FilesORM.owner_id == user_id)
        )
        files = files.all()

        return [FileSchema.model_validate(x) for x in files]

    @staticmethod
    async def get_file_data(
            user_id: int,
            file_id: int,
            db: AsyncSession
    ) -> FileSchema:
        """Возвращает файл из базы данных"""

        file = await db.scalars(
            select(FilesORM)
            .where(FilesORM.id == file_id)
        )
        file = file.first()

        if file is None:
            raise HTTPException(
                status_code=404,
                detail="file not found"
            )

        if file.owner_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="file does not belong to the user"
            )

        return FileSchema.model_validate(file)

    @staticmethod
    def _file_exist_on_storage(
            full_name: str,
            path: Path
    ) -> bool:
        """Возвращает есть ли файл в хранилище"""

        return Path(path, full_name).exists()

    @staticmethod
    async def _file_exist_on_database(
            name: str,
            extension: str,
            path: Path,
            db: AsyncSession
    ) -> bool:
        """Возвращает есть ли данные о файле в базе данных"""

        search_file = await db.scalars(
            select(FilesORM)
            .where(
                (FilesORM.name == name)
                & (FilesORM.extension == extension)
                & (FilesORM.path == str(path))
            )
        )

        return bool(search_file.first())

    @staticmethod
    def _validate_new_file(
            *,
            name: str,
            extension: str,
            size: int,
            path: str
    ) -> FileCreateSchema:
        """Возвращает FileCreateSchema для создания и валидирует данные"""

        try:
            return FileCreateSchema(
                name=name, extension=extension,
                size=size, path=path
            )

        except ValidationError as ex:
            raise HTTPException(status_code=422, detail=ex.errors())

    @staticmethod
    async def _add_file_data(
            owner_id: int,
            file_data: FileCreateSchema,
            db: AsyncSession
    ) -> int:
        """
            Добавляет данные о файле в базу данных
                и возвращает идентификатор файла
        """

        new_file = await db.execute(
            insert(FilesORM)
            .values(
                owner_id=owner_id,
                **file_data.model_dump()
            )
            .returning(FilesORM.id)
        )

        return new_file.scalar()

    @staticmethod
    def _split_file_name(
            file_name: Path | str
    ) -> tuple[str, str]:
        """Возвращает имя и расширение файла"""

        path = Path(file_name)

        return path.name.split(".")[0], "".join(path.suffixes)[1:]

    @classmethod
    async def upload_file(
            cls,
            user_id: int,
            file: UploadFile,
            db: AsyncSession
    ) -> ResponseOK:
        """Обрабатывает загрузку файлов"""

        full_name = file.filename
        name, extension = cls._split_file_name(full_name)

        if (
            cls._file_exist_on_storage(
                full_name, Config.BASE_DIRECTORY
            ) or
            await cls._file_exist_on_database(
                name, extension, Config.BASE_DIRECTORY, db
            )
        ):
            raise HTTPException(status_code=409, detail="file exists")

        file_id = await cls._add_file_data(
            owner_id=user_id,
            file_data=cls._validate_new_file(
                name=name,
                extension=extension,
                size=file.size,
                path=str(Config.BASE_DIRECTORY)
            ),
            db=db
        )
        file_data = await cls.get_file_data(user_id, file_id, db)

        try:
            async with aiofiles.open(file_data.full_path, "wb") as open_file:
                file_content = await file.read()
                await open_file.write(file_content)

        except:
            await cls.delete_file(user_id, file_id, db)
            raise HTTPException(status_code=501, detail="file not saved")

        return ResponseOK()

    @staticmethod
    async def _drop_file_data(
            file_id: int,
            db: AsyncSession
    ) -> None:
        """Удаляет данные о файле в базе данных"""

        await db.execute(
            delete(FilesORM)
            .where(FilesORM.id == file_id)
        )

    @classmethod
    def _delete_directorys(
            cls,
            path: Path,
            anchor: str,
    ) -> None:
        """Удаляет папки до корня если они пустые"""

        if (
            str(path) != anchor and
            path != Config.BASE_DIRECTORY and
            path.exists() and
            not any(path.iterdir())
        ):
            path.rmdir()
            cls._delete_directorys(path.parent, anchor)

    @classmethod
    async def delete_file(
            cls,
            user_id: int,
            file_id: int,
            db: AsyncSession
    ) -> ResponseOK:
        """Удаляет все данные о файле вместе с файлом"""

        file_data = await cls.get_file_data(user_id, file_id, db)
        full_path = file_data.full_path

        if cls._file_exist_on_storage(file_data.full_name, file_data.directory):
            full_path.unlink()

        cls._delete_directorys(full_path.parent, full_path.anchor)
        await cls._drop_file_data(file_id, db)

        return ResponseOK()

    @staticmethod
    def _validate_old_and_new_path(
            old_path: Path,
            new_path: Path
    ) -> None:
        """Проверьте, существует ли старый и новый пути"""

        if not old_path.exists():
            raise HTTPException(
                status_code=409,
                detail="The file to be moved was not found"
            )

        if new_path.exists():
            raise HTTPException(
                status_code=409,
                detail="The file space is occupied"
            )

    @classmethod
    def _move_file(
            cls,
            old_path: Path,
            new_path: Path
    ) -> None:
        """Перемещает файл в другую директорию"""

        cls._validate_old_and_new_path(old_path, new_path)

        new_directory = new_path.parent
        new_directory.mkdir(parents=True, exist_ok=True)

        shutil.copy2(old_path, new_path)
        old_path.unlink()

    @classmethod
    def _rename_file(
            cls,
            old_path: Path,
            new_path: Path
    ) -> None:
        """Переименовывает файл"""

        cls._validate_old_and_new_path(old_path, new_path)
        old_path.rename(new_path)

    @classmethod
    async def update_file_data(
            cls,
            user_id: int,
            file_id: int,
            data: FileUpdateForm,
            db: AsyncSession
    ) -> ResponseOK:
        """Обновляет данные о файле и перемещает его если нужно"""

        file_data = await cls.get_file_data(user_id, file_id, db)
        full_path = file_data.full_path

        new_name = data.name or file_data.name
        new_path = Path(data.path) if data.path else file_data.path
        new_full_path = FileSchema.get_full_path(
            directory=new_path,
            full_name=FileSchema.get_full_name(new_name, file_data.extension)
        )

        try:
            flag_name = file_data.name != new_name
            flag_directory = full_path.parent != new_full_path.parent

            if flag_directory:
                cls._move_file(full_path, new_full_path)

            if flag_name and not flag_directory:
                cls._rename_file(full_path, new_full_path)

        except (FileNotFoundError, FileExistsError) as ex:
            raise HTTPException(status_code=501, detail=str(ex))

        except (OSError, PermissionError):
            raise HTTPException(status_code=501, detail="Couldn't move the file")

        except Exception:
            traceback.print_exc()
            raise HTTPException(status_code=500, detail="Something went wrong")

        else:
            await db.execute(
                update(FilesORM)
                .where(FilesORM.id == file_id)
                .values(**data.model_dump(exclude_unset=True))
            )

        return ResponseOK()

    @classmethod
    async def download_file(
            cls,
            user_id: int,
            file_id: int,
            db: AsyncSession
    ) -> FileResponse:
        """Возвращает файл для скачивания"""

        file_data = await cls.get_file_data(user_id, file_id, db)

        return FileResponse(
            path=file_data.full_path,
            filename=file_data.full_name
        )

    @classmethod
    async def files_initialization(cls) -> None:
        """Инициализация файлов и дб"""

        db = session_factory()

        try:
            storage_files = list(Config.BASE_DIRECTORY.glob("*.*"))
            db_files = [
                {"file_id": x.id, "path": x.full_path}
                for x in await cls.get_files_data(db)
            ]
            db_files_path = [x["path"] for x in db_files]

            found_files = [x for x in storage_files if x not in db_files_path]
            # Файлы которые появились в хранилище

            for file_path in found_files:

                name, extension = cls._split_file_name(file_path)
                await cls._add_file_data(
                    file_data=cls._validate_new_file(
                        name=name,
                        extension=extension,
                        size=file_path.stat().st_size,
                        path=str(Config.BASE_DIRECTORY)
                    ),
                    db=db
                )

            files_not_found = [
                x["file_id"]
                for x in db_files
                if not x["path"].exists()
            ]
            # Файлы которые были удалены из хранилище

            for file_id in files_not_found:
                await cls._drop_file_data(file_id, db)

            await db.commit()

        except:
            await db.rollback()
            raise FailFilesInitialization()

        finally:
            await db.close()
