from datetime import datetime
from typing import Optional, Literal

from sqlalchemy import (
    BigInteger,
    Integer,
    String,
    ForeignKey,
    DateTime,
)
from sqlalchemy import func as f
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped, 
    declared_attr, 
    mapped_column,
    relationship
)



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
    telegram_username: Mapped[str] = mapped_column(String(100))
    
    created_at: Mapped[datetime] = mapped_column(default=f.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(default=f.now(), onupdate=f.now(), nullable=True)

    tasks: Mapped[list["Task"]] = relationship(back_populates="user")


class Task(Base):
    __tablename__ = "task_t"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user_t.telegram_user_id", ondelete="CASCADE"))

    title: Mapped[str] = mapped_column(String(512))
    status: Mapped[Literal["opened", "closed"]] = mapped_column(String())

    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=f.now())
    updated_at: Mapped[datetime] = mapped_column(default=f.now(), onupdate=f.now(), nullable=True)

    user: Mapped["User"] = relationship(back_populates="tasks")
