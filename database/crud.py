from sqlalchemy.orm import Session
from sqlalchemy import select

from database.model import Url

def get_url(session: Session, short_id: str) -> Url | None:
    query = select(Url).where(Url.short_id == short_id)
    res = session.execute(query)
    return res.scalar_one_or_none()

def create_url(session: Session, source_url: str, short_id: str) -> Url:
    url = Url(source_url=source_url, short_id=short_id)
    session.add(url)
    session.flush()
    return url

def get_url_by_source_url(session: Session, source_url: str) -> Url | None:
    query = select(Url).where(Url.source_url == source_url)
    res = session.execute(query)
    return res.scalar_one_or_none()
