import shutil
import aiofiles
import traceback

from typing import Optional
from pathlib import Path

from fastapi import UploadFile, HTTPException
from fastapi.responses import FileResponse

from psycopg2.extras import DictCursor

from config import Config

from .schemas import FileSchema, UpdateFileSchema, ResponseOK
from.database import get_postgresql_connection


class FileService:

    @classmethod
    def get_file_data(
            cls,
            file_id: int,
            psql_cursor: DictCursor
    ) -> FileSchema | None:
        """Возвращает файл из базы данных"""

        psql_cursor.execute("""
            SELECT * FROM files
            WHERE id = %(file_id)s
        """, {
            "file_id": file_id
        })
        psql_response = psql_cursor.fetchone()

        return FileSchema(**psql_response) if psql_response else None


    @classmethod
    def get_files_data(
            cls,
            psql_cursor: DictCursor
    ) -> list[Optional[FileSchema]]:
        """Возвращает все файлы которые есть в базе данных"""

        psql_cursor.execute("SELECT * FROM files")
        psql_response = psql_cursor.fetchall()

        return [FileSchema(**x) for x in psql_response]


    @staticmethod
    def _file_exist_on_storage(
            full_name: str,
            path: Path
    ) -> bool:
        """Возвращает есть ли файл в хранилище"""

        return Path(path, full_name).exists()


    @staticmethod
    def _file_exist_on_database(
            name: str,
            extension: str,
            path: Path,
            psql_cursor: DictCursor
    ) -> bool:
        """Возвращает есть ли данные о файле в базе данных"""

        psql_cursor.execute("""
            SELECT id FROM files
            WHERE name = %(name)s AND
                  extension = %(extension)s AND
                  path = %(path)s
        """, {
            "name": name,
            "extension": extension,
            "path": str(path)
        })
        psql_response = psql_cursor.fetchone()

        return bool(psql_response)


    @staticmethod
    def _add_file_data(
            file_data: FileSchema,
            psql_cursor: DictCursor
    ) -> int:
        """Добавляет данные о файле в базу данных и возвращает идентификатор файла """

        psql_cursor.execute("""
            INSERT INTO files (
                name, extension, size, path
            ) VALUES (
                %(name)s, %(extension)s, %(size)s, %(path)s
            )
            RETURNING id
        """, dict(file_data))
        psql_response = psql_cursor.fetchone()

        return psql_response["id"]


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
            file: UploadFile,
            psql_cursor: DictCursor
    ) -> ResponseOK:
        """Обрабатывает загрузку файлов"""

        full_name = file.filename
        name, extension = cls._split_file_name(full_name)

        if (
            cls._file_exist_on_storage(
                full_name, Config.BASE_DIRECTORY
            ) or
            cls._file_exist_on_database(
                name, extension, Config.BASE_DIRECTORY, psql_cursor
            )
        ):
            raise HTTPException(status_code=409, detail="file exists")

        file_data = FileSchema(
            id=0,
            name=name,
            extension=extension,
            size=file.size,
            path=str(Config.BASE_DIRECTORY)
        )
        file_id = cls._add_file_data(
            file_data=file_data,
            psql_cursor=psql_cursor
        )
        file_data.id = file_id

        try:
            async with aiofiles.open(file_data.full_path, "wb") as open_file:
                file_content = await file.read()
                await open_file.write(file_content)

        except:
            cls.delete_file(file_id, psql_cursor)
            raise HTTPException(status_code=501, detail="file not saved")


        return ResponseOK()


    @staticmethod
    def _drop_file_data(
            file_id: int,
            psql_cursor: DictCursor
    ) -> None:
        """Удаляет данные о файле в базе данных"""

        psql_cursor.execute("""
            DELETE FROM files
            WHERE id = %(file_id)s
        """, {
            "file_id": file_id
        })


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
    def delete_file(
            cls,
            file_id: int,
            psql_cursor: DictCursor
    ) -> ResponseOK:
        """Удаляет все данные о файле вместе с файлом"""

        file_data = cls.get_file_data(file_id, psql_cursor)

        if file_data is None:
            raise HTTPException(status_code=404, detail="file not found")

        full_path = file_data.full_path

        if cls._file_exist_on_storage(file_data.full_name, file_data.directory):
            full_path.unlink()

        cls._delete_directorys(full_path.parent, full_path.anchor)
        cls._drop_file_data(file_id, psql_cursor)

        return ResponseOK()


    @staticmethod
    def _move_file(
            old_path: Path,
            new_path: Path
    ) -> None:
        """Перемещает файл в другую директорию"""

        if not old_path.exists():
            raise FileNotFoundError("The file to be moved was not found")

        if new_path.exists():
            raise FileExistsError("The file space is occupied")

        new_directory = new_path.parent
        new_directory.mkdir(parents=True, exist_ok=True)

        shutil.copy2(old_path, new_path)
        old_path.unlink()


    @staticmethod
    def _rename_file(
            old_path: Path,
            new_path: Path
    ) -> None:
        """Переименовывает файл"""

        if not old_path.exists():
            raise FileNotFoundError("The file to be rename was not found")

        if new_path.exists():
            raise FileExistsError("The file space is occupied")

        old_path.rename(new_path)


    @classmethod
    def update_file_data(
            cls,
            file_id: int,
            data: UpdateFileSchema,
            psql_cursor: DictCursor
    ) -> ResponseOK:
        """Обновляет данные о файле и перемещает его если нужно"""

        file_data = cls.get_file_data(file_id, psql_cursor)

        if file_data is None:
            raise HTTPException(status_code=404, detail="file not found")

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
            psql_cursor.execute("""
                UPDATE files
                SET name = %(name)s,
                    path = %(path)s,
                    comment = %(comment)s,
                    updated_at = NOW()
                WHERE id = %(file_id)s
            """, {
                "name": new_name,
                "path": str(new_path),
                "comment": data.comment,
                "file_id": file_id
            })

        return ResponseOK()


    @classmethod
    def download_file(
            cls,
            file_id: int,
            psql_cursor: DictCursor
    ) -> FileResponse:
        """Возвращает файл для скачивания"""

        file_data = cls.get_file_data(file_id, psql_cursor)

        if file_data is None:
            raise HTTPException(status_code=404, detail="file not found")

        return FileResponse(
            path=file_data.full_path,
            filename=file_data.full_name
        )


    @classmethod
    def files_initialization(cls) -> None:
        """Инициализация файлов и дб"""

        psql_connect, psql_cursor = get_postgresql_connection()

        try:
            storage_files = list(Config.BASE_DIRECTORY.glob("*.*"))
            db_files = [
                {"file_id": x.id, "path": x.full_path}
                for x in cls.get_files_data(psql_cursor)
            ]
            db_files_path = [x["path"] for x in db_files]

            found_files = [x for x in storage_files if x not in db_files_path]
            # Файлы которые появились в хранилище

            for file_path in found_files:

                name, extension = cls._split_file_name(file_path)
                cls._add_file_data(
                    file_data=FileSchema(
                        id=0,
                        name=name,
                        extension=extension,
                        size=file_path.stat().st_size,
                        path=str(Config.BASE_DIRECTORY)
                    ),
                    psql_cursor=psql_cursor
                )

            files_not_found = [
                x["file_id"]
                for x in db_files
                if not x["path"].exists()
            ]
            # Файлы которые были удалены из хранилище

            for file_id in files_not_found:
                cls._drop_file_data(file_id, psql_cursor)

        finally:
            psql_cursor.close()
            psql_connect.close()
