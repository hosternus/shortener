from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from database.crud import get_url, create_url, get_url_by_source_url
from database.core import get_session, create_tables, close_db
from schemas import CreateUrl
from utils import generate_short_id
from config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield
    close_db()

app = FastAPI(lifespan=lifespan)

# cache
@app.get("/{url_id}")
def return_url(url_id: str, session: Session = Depends(get_session)):
    try:
        url = get_url(session=session, short_id=url_id)
        if url is None:
            raise HTTPException(status_code=404, detail="Not found")
        url.visits += 1
        session.commit()
        return RedirectResponse(url=url.source_url)
    except HTTPException as e:
        session.rollback()
        raise e
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/url")
def create_url_route(url_object: CreateUrl, session: Session = Depends(get_session)):
    try:
        url = get_url_by_source_url(session=session, source_url=str(url_object.source_url))
        if url is None:
            url = create_url(
                session=session, 
                source_url=str(url_object.source_url), 
                short_id=generate_short_id()
            )
        session.commit()
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    if settings.BASE_URL is None:
        raise HTTPException(status_code=500, detail="Base url not provided")
    return {"short_url": f"{settings.BASE_URL}/{url.short_id}"}
