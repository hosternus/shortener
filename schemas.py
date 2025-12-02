from datetime import datetime
from pydantic import BaseModel, HttpUrl, ConfigDict

class ShortedURL(BaseModel):
    source_url: HttpUrl | str

class ShortedURLRequest(ShortedURL): pass

class ShortedURLResponse(ShortedURL):
    short_id: str
    full_url: HttpUrl | None = None
    visits: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, extra='ignore')
