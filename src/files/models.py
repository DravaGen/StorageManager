from sqlalchemy import Column, BigInteger, Integer, String, Text, TIMESTAMP, \
    ForeignKey
from sqlalchemy.sql import func

from ..databases.sqlalchemy import Base


class FilesORM(Base):
    __tablename__ = "files"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    owner_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    extension = Column(String(10), nullable=False)
    size = Column(Integer, nullable=False)
    path = Column(String, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
        onupdate=func.now()
    )
    comment = Column(String, nullable=True)
