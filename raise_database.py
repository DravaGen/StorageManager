from config import Config
from src.database import get_postgresql_connection


def raise_db() -> None:
    """Поднимает базу данных"""

    psql_connect, psql_cursor = get_postgresql_connection()

    psql_cursor.execute("""
        DROP TABLE IF EXISTS files
    """)

    psql_cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id BIGSERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            extension VARCHAR(10) NOT NULL,
            size INT NOT NULL,
            path VARCHAR(255) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NULL,
            comment TEXT DEFAULT NULL
        )
    """)

    psql_cursor.close()
    psql_connect.close()


if __name__ == "__main__":
    if Config.DEBUG:
        raise_db()
