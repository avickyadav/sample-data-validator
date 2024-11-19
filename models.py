from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.orm import declarative_base
from database import engine

Base = declarative_base()

#comment some
class FileUpload(Base):
    __tablename__ = "file_upload"
    id = Column(Integer, primary_key=True, index=True)
    crm_id = Column(String(255))
    owner = Column(String(100), nullable=False)
    upload_date = Column(DateTime)
    status = Column(String(50), nullable=False)
    error = Column(String, nullable=True)
    input_file_link = Column(String, nullable=True)  # New column
    output_file_link = Column(String, nullable=True)


Base.metadata.create_all(bind=engine)
