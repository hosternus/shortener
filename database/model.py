from datetime import datetime

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, func

class Base(DeclarativeBase):
    pass

class Url(Base):
    __tablename__ = "urls"

    id: Mapped[int] = mapped_column(primary_key=True, nullable=False)
    source_url: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    short_id: Mapped[str] = mapped_column(String(6), nullable=False, unique=True)
    visits: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now, server_default=func.now()) # pylint: disable=not-callable
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now, server_default=func.now(), onupdate=func.now(), server_onupdate=func.now()) # pylint: disable=not-callable
