from pydantic import BaseModel, HttpUrl

class CreateUrl(BaseModel):
    source_url: HttpUrl | str
