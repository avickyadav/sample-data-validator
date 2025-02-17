from datetime import datetime

from fastapi import FastAPI, UploadFile, HTTPException
from azure.storage.fileshare import ShareFileClient
import os
from dotenv import load_dotenv

from database import get_db, SessionLocal
from models import FileUpload

load_dotenv()


AZURE_STORAGE_CONNECTION_STRING = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
FILE_SHARE_NAME = "pythontrial"
DIRECTORY_NAME = "uploads"
OUTPUT_DIRECTORY_NAME = "outputs"
ERROR_DIRECTORY_NAME = "errors"
CONFIG_DIRECTORY_NAME = "configs"


def upload_to_azure(file_path: str, file_data: bytes):
    file_client = ShareFileClient.from_connection_string(
        conn_str=AZURE_STORAGE_CONNECTION_STRING,
        share_name=FILE_SHARE_NAME,
        file_path=file_path
    )
    file_client.upload_file(file_data)
    print("file uploaded azure")


def download_from_azure(file_path: str):
    file_client = ShareFileClient.from_connection_string(
        conn_str=AZURE_STORAGE_CONNECTION_STRING,
        share_name=FILE_SHARE_NAME,
        file_path=file_path
    )
    return file_client.download_file().readall()


def update_fields_db(new_upload, azure_file_path, status):
    db = next(get_db())
    print(f"code in update field db {new_upload.id}, {azure_file_path}, ")
    if status == "success":
        print("code in update field db success")
        db.query(FileUpload).filter(FileUpload.id == new_upload.id).update(
            {"output_file_link": azure_file_path,
             "status": "Completed"})
        db.commit()
    else:
        db.query(FileUpload).filter(FileUpload.id == new_upload.id).update(
            {"error": azure_file_path,
             "status": "Failed"})
        db.commit()
