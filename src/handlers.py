from typing import Optional

from fastapi import APIRouter, UploadFile, Depends, Query, Body
from fastapi.responses import FileResponse

from psycopg2.extras import DictCursor

from .schemas import FileSchema, UpdateFileSchema, ResponseOK
from .services import FileService
from .database import get_psql_cursor


api_router = APIRouter()


@api_router.get("/files", response_model=list[Optional[FileSchema]])
async def get_files(
        psql_cursor: DictCursor = Depends(get_psql_cursor)
) -> list[Optional[FileSchema]]:
    """Возвращает файлы"""

    return FileService.get_files_data(psql_cursor)


@api_router.get("/files/{file_id}", response_model=Optional[FileSchema])
async def get_file(
        file_id: int,
        psql_cursor: DictCursor = Depends(get_psql_cursor)
) -> Optional[FileSchema]:
    """Возвращает файл"""

    return FileService.get_file_data(file_id, psql_cursor)


@api_router.put("/files/{file_id}", response_model=ResponseOK)
async def update_file_data(
        file_id: int,
        file: UpdateFileSchema = Body(),
        psql_cursor: DictCursor = Depends(get_psql_cursor)
) -> ResponseOK:
    """Обновляет данные о файле"""

    return FileService.update_file_data(file_id, file, psql_cursor)


@api_router.delete("/files/{file_id}", response_model=ResponseOK)
async def delete_file(
        file_id: int,
        psql_cursor: DictCursor = Depends(get_psql_cursor)
) -> ResponseOK:
    """Удаляет файл"""

    return FileService.delete_file(file_id, psql_cursor)


@api_router.post("/upload/file", response_model=ResponseOK)
async def upload_file(
        file: UploadFile,
        psql_cursor: DictCursor = Depends(get_psql_cursor)
) -> ResponseOK:
    """Загружает файл"""

    return await FileService.upload_file(file, psql_cursor)


@api_router.get("/download/file", response_class=FileResponse)
async def download_file(
        file_id: int = Query(),
        psql_cursor: DictCursor = Depends(get_psql_cursor)
) -> FileResponse:
    """Возвращает файл для скачивания"""

    return FileService.download_file(file_id, psql_cursor)
