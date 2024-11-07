from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.orm import declarative_base
from database import engine

Base = declarative_base()


class FileUpload(Base):
    __tablename__ = "file_upload"
    id = Column(Integer, primary_key=True, index=True)
    crm_id = Column(String(255))
    owner = Column(String(100), nullable=False)
    upload_date = Column(DateTime, default=datetime.now(timezone.utc))
    status = Column(String(50), nullable=False)
    error = Column(String, nullable=True)


Base.metadata.create_all(bind=engine)
