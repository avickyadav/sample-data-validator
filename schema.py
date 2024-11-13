from pydantic import BaseModel
from datetime import datetime


class FileUploadSchema(BaseModel):
    id: int
    crm_id: str
    owner: str
    upload_date: datetime
    status: str
    error: str | None

    class Config:
        orm_mode = True  # This enables Pydantic to work with SQLAlchemy models
