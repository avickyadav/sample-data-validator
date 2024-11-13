from datetime import datetime

from fastapi import FastAPI, UploadFile, HTTPException
from azure.storage.fileshare import ShareFileClient
import os
from dotenv import load_dotenv

load_dotenv()

AZURE_STORAGE_CONNECTION_STRING = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
FILE_SHARE_NAME = "pythontrial"
DIRECTORY_NAME = "uploads"


def upload_to_azure(file_path: str, file_data: bytes):
    file_client = ShareFileClient.from_connection_string(
        conn_str=AZURE_STORAGE_CONNECTION_STRING,
        share_name=FILE_SHARE_NAME,
        file_path=file_path
    )
    file_client.upload_file(file_data)


def download_from_azure(file_path: str):
    file_client = ShareFileClient.from_connection_string(
        conn_str=AZURE_STORAGE_CONNECTION_STRING,
        share_name=FILE_SHARE_NAME,
        file_path=file_path
    )
    return file_client.download_file().readall()
