from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    BigInteger,
    Enum as SAEnum,
    ForeignKey,
    func
)
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped, 
    declared_attr, 
    mapped_column,
    relationship
)

from .pydantic import TaskStatesEnum


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all database models with async support."""
    __abstract__ = True

    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name with '_t' suffix."""
        return f"{cls.__name__.lower()}_t"


class User(Base):
    __tablename__ = "user_t"

    telegram_user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    telegram_username: Mapped[str] = mapped_column(String(64))
    
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(default=func.now(), onupdate=func.now(), nullable=True)

    tasks: Mapped[list["Task"]] = relationship(back_populates="user")


class Task(Base):
    __tablename__ = "task_t"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user_t.telegram_user_id", ondelete="CASCADE"))

    title: Mapped[str] = mapped_column(String(512))
    status: Mapped[TaskStatesEnum] = mapped_column(SAEnum(TaskStatesEnum), default=TaskStatesEnum.open)

    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(default=func.now(), onupdate=func.now(), nullable=True)

    user: Mapped["User"] = relationship(back_populates="tasks")
