from typing import Optional

from fastapi import APIRouter, UploadFile, Depends, Query, Body, \
    Path, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import FileSchema, FileUpdateForm
from .services import FileService
from ..auth.services import get_user_id
from ..databases.sqlalchemy import get_db
from ..base_response import ResponseOK


files_router = APIRouter()


@files_router.get("/my", response_model=list[Optional[FileSchema]])
async def get_my_files(
        user_id: int = Depends(get_user_id),
        db: AsyncSession = Depends(get_db)
) -> list[Optional[FileSchema]]:
    """Возвращает файлы текущего пользователя"""

    return await FileService.get_my_files(user_id, db)


@files_router.get("/download", response_class=FileResponse)
async def download_file(
        user_id: int = Depends(get_user_id),
        file_id: int = Query(...),
        db: AsyncSession = Depends(get_db)
) -> FileResponse:
    """Возвращает файл для скачивания"""

    return await FileService.download_file(user_id, file_id, db)


@files_router.get("/{file_id}", response_model=Optional[FileSchema])
async def get_file(
        user_id: int = Depends(get_user_id),
        file_id: int = Path(...),
        db: AsyncSession = Depends(get_db)
) -> FileSchema:
    """Возвращает файл"""

    return await FileService.get_file_data(user_id, file_id, db)


@files_router.put("/{file_id}", response_model=ResponseOK)
async def update_file_data(
        user_id: int = Depends(get_user_id),
        file_id: int = Path(...),
        file: FileUpdateForm = Body(...),
        db: AsyncSession = Depends(get_db)
) -> ResponseOK:
    """Обновляет данные о файле"""

    return await FileService.update_file_data(user_id, file_id, file, db)


@files_router.delete("/{file_id}", response_model=ResponseOK)
async def delete_file(
        user_id: int = Depends(get_user_id),
        file_id: int = Path(...),
        db: AsyncSession = Depends(get_db)
) -> ResponseOK:
    """Удаляет файл"""

    return await FileService.delete_file(user_id, file_id, db)


@files_router.post("/upload", response_model=ResponseOK)
async def upload_file(
        user_id: int = Depends(get_user_id),
        file: UploadFile = File(...),
        db: AsyncSession = Depends(get_db)
) -> ResponseOK:
    """Загружает файл"""

    return await FileService.upload_file(user_id, file, db)
