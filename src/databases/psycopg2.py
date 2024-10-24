from decimal import Decimal
from typing import Optional, Callable, Generator

import psycopg2
from psycopg2.extras import DictCursor
from psycopg2._psycopg import connection as Connection

from config import PostgreSQLConfig


def _formats_data_types(row: dict) -> dict:
    """Форматирует типы данных"""
    # decimal to int

    for key, value in row.items():
        if isinstance(value, Decimal):
            row[key] = float(value)

    return row


def _fetch_one_wrapper(method) -> Callable:
    """Декоратор для fetchone возвращает данные в виде словаря если они есть"""

    def wrapper(*args, **kwargs) -> dict | None:
        row = method(*args, **kwargs)

        if row is not None:
            row = _formats_data_types(dict(row))

        return row

    return wrapper


def _fetch_all_wrapper(method) -> Callable:
    """Декоратор для fetchall возвращает данные в виде списка"""

    def wrapper(*args, **kwargs) -> list[Optional[dict]]:
        rows = method(*args, **kwargs)
        rows = [_formats_data_types(dict(row)) for row in rows]

        return rows

    return wrapper


def get_postgresql_connection() -> tuple[Connection, DictCursor]:
    """Подключение к postgresql"""

    connection = psycopg2.connect(
        user=PostgreSQLConfig.DB_USER,
        password=PostgreSQLConfig.DB_PASSWORD,
        host=PostgreSQLConfig.DB_HOST,
        port=PostgreSQLConfig.DB_PORT,
        database=PostgreSQLConfig.DB_NAME
    )
    connection.autocommit = True

    cursor = connection.cursor(cursor_factory=DictCursor)
    cursor.fetchone = _fetch_one_wrapper(cursor.fetchone)
    cursor.fetchall = _fetch_all_wrapper(cursor.fetchall)

    return connection, cursor


def get_psql_cursor() -> Generator[DictCursor, None, None]:
    """Генератор курсоров PostgreSQL"""

    psql_connect, psql_cursor = get_postgresql_connection()

    try:
        yield psql_cursor

    finally:
        psql_cursor.close()
        psql_connect.close()
