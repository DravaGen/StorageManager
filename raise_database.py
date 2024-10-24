from sqlalchemy import create_engine

from config import Config, PostgreSQLConfig
from src.databases.sqlalchemy import Base


if __name__ == "__main__":
    if Config.DEBUG:
        URL = PostgreSQLConfig.SQLALCHEMY_URL.replace("asyncpg", "psycopg2")

        engine = create_engine(URL)
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
