from sqlalchemy import Column, BigInteger, String

from ..databases.sqlalchemy import Base


class UsersORM(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(30), nullable=False)
    email = Column(String(40), nullable=False, unique=True)
    password = Column(String(32), nullable=False)
