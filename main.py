import io
import math
from datetime import datetime, timezone
from urllib.parse import unquote 
import pytz

from fastapi.responses import HTMLResponse
from datetime import timedelta
from fastapi import FastAPI, Depends, HTTPException, status, Request, Cookie, UploadFile, File, Query
from fastapi.responses import RedirectResponse, JSONResponse, Response
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
import httpx
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import jwt
from jwt import PyJWTError
import requests
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, aliased
import pandas as pd

from typing import List, Dict

from constants.rialto_table_constants import rialto_table_necessary_columns
from controllers.netsuite_controller import process_action
from database import get_db
from helper_file import DIRECTORY_NAME, upload_to_azure, download_from_azure
from models import FileUpload
from schema import FileUploadSchema
from controllers import netsuite_controller

load_dotenv()

app = FastAPI()

# Configuration
client_id = os.getenv("AZURE_CLIENT_ID")
client_secret = os.getenv("AZURE_CLIENT_SECRET")
tenant_id = os.getenv("AZURE_TENANT_ID")
redirect_uri = os.getenv("REDIRECT_URI")
scopes = ["openid", "profile", "email"]
issuer = f"https://login.microsoftonline.com/{tenant_id}/v2.0"

print(f'THIS IS REDIRECT {redirect_uri}')

# Mount static files (optional)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")


# @app.get("/", response_class=HTMLResponse)
# async def read_upload_home(request: Request):
#     return templates.TemplateResponse("upload_home.html", {"request": request, "uploads": uploads})


async def validate_token(token: str):
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = {}

    if 'kid' not in unverified_header:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid header")

    async with httpx.AsyncClient() as client:
        keys_url = f"https://login.microsoftonline.com/common/discovery/v2.0/keys"
        keys_response = await client.get(keys_url)
        keys = keys_response.json().get('keys')

    for key in keys:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                "kty": key['kty'],
                "n": key['n'],
                "e": key['e']
            }
    print(f'Yahaaa tk aake gya {rsa_key}')
    if rsa_key:
        # payload = jwt.decode(
        #     token,
        #     options=
        # )
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    # decoded_token = jwt.decode(token, algorithms=['RS256'], verify=False)
    # print(f"ye kara samaaan {decoded_token}")


async def get_current_user(request: Request):
    print(f'this is headers {request.headers}')
    # Extract token from Authorization header
    authorization: str = request.headers.get("Authorization")
    if not authorization:
        return None

    token = authorization.split(" ")[1] if " " in authorization else authorization
    user = await validate_token(token)
    return user


# @app.get("/")
# async def read_root(current_user: dict = Depends(get_current_user)):
#     if current_user is None:
#         return RedirectResponse(url="/login")  # Redirect if not authenticated
#     return {"message": f"Welcome, {current_user.get('name', 'User')}!"}


@app.get("/login")
async def login():
    return RedirectResponse(
        url=f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&response_mode=query&scope={' '.join(scopes)}")


@app.get("/auth/callback")
async def auth_callback(code: str, responses: RedirectResponse, request: Request):
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        })

        if response.status_code != 200:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed")

        tokens = response.json()
        toke = await validate_token(tokens["access_token"])
        if toke:
            responses = RedirectResponse(url='/')
            responses.set_cookie(key="user_token", value=tokens["access_token"])
            return responses

        print(f'this is token {toke}')
        return {"access_token": tokens["access_token"], "id_token": tokens["id_token"]}


# @app.get("/upload_history/{crm_id}", response_class=List[FileUploadSchema])
# async def get_upload_history(crm_id: str, db: Session = Depends(get_db)):
#     # Filter uploads by CRM ID
#     history = list(db.query(FileUpload).filter(FileUpload.crm_id == crm_id).all())
#     return history
@app.get("/upload_history/{crm_id}", response_model=List[FileUploadSchema])  # Correctly specify the return type
async def get_upload_by_crm_id(crm_id: str, db: Session = Depends(get_db)):
    print(f'This is crm {crm_id}')
    history = db.query(FileUpload).filter(FileUpload.crm_id == crm_id).all()
    if not history:
        raise HTTPException(status_code=404, detail="Records not found")
    return history  # This will return a list of FileUploadSchema instances


@app.get("/", response_class=HTMLResponse)
async def protected_route(request: Request, user_token: str = Cookie(None), message: str = None,
                          db: Session = Depends(get_db), page: int = Query(1, ge=1), limit: int = Query(5, ge=1),
                          sort: str = Query('desc')
                          ):
    print(f'this is user token {user_token}')
    if user_token is None:
        return RedirectResponse(url="/login")  # Redirect if not authenticated
    uploads_records_data, total_pages = await get_all_upload_records_from_db(db, limit, page, sort=sort)
    print(f"This is page data {page} and {total_pages}")
    return templates.TemplateResponse("upload_home.html",
                                      {"request": request, "uploads": uploads_records_data,
                                       "message": message,
                                       "page": page,
                                       "total_pages": total_pages})


async def get_all_upload_records_from_db(db, limit=5, page=1, sort='desc'):
    total_records = db.query(FileUpload.crm_id).distinct().count()
    total_pages = math.ceil(total_records / limit)  # Calculate total pages
    # Fetch records for the current page
    # upload_records = db.query(FileUpload).order_by(FileUpload.upload_date.desc()).offset((page - 1) * limit).limit(limit).all()
    latest_uploads_subquery = (
        db.query(
            FileUpload.crm_id,
            func.max(FileUpload.upload_date).label('latest_upload_date')
        )
        .group_by(FileUpload.crm_id)
        .subquery()
    )
    FileUploadAlias = aliased(FileUpload)

    upload_records = (
        db.query(FileUpload)
        .join(
            latest_uploads_subquery,
            (FileUpload.crm_id == latest_uploads_subquery.c.crm_id) &
            (FileUpload.upload_date == latest_uploads_subquery.c.latest_upload_date)
        )
    )
    if sort.lower() == 'desc':
        upload_records = upload_records.order_by(FileUpload.upload_date.desc()).offset((page - 1) * limit).limit(
            limit).all()
    else:
        upload_records = upload_records.order_by(FileUpload.upload_date.asc()).offset((page - 1) * limit).limit(
            limit).all()

    return upload_records, total_pages


@app.post("/upload/", response_class=HTMLResponse)
async def upload_file(request: Request, file: UploadFile = File(...),
                      db: Session = Depends(get_db),
                      user_token: str = Cookie(None)):
    # Check the file content type to ensure it's an .xlsx file
    file_data = await file.read()
    if file.content_type != "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        records, total_pages = await get_all_upload_records_from_db(db)
        error_message = "Only .xlsx files are allowed."
        return templates.TemplateResponse("upload_home.html", {
            "request": request,
            "uploads": records,
            "error": error_message,
            "page": 1,
            "total_pages": total_pages
        })
    #checking file format
    excel_file = io.BytesIO(file_data)
    df = pd.read_excel(excel_file, header=1)
    missing_columns = [col for col in rialto_table_necessary_columns if
                       col.strip() not in [df_col.strip() for df_col in df.columns]]
    if missing_columns:
        records, total_pages = await get_all_upload_records_from_db(db)
        error_message = f"Columns that are missing in Input file:  {missing_columns}"
        print(f"Here are the columns that are missing {missing_columns}")
        return templates.TemplateResponse("upload_home.html", {
            "request": request,
            "uploads": records,
            "error": error_message,
            "page": 1,
            "total_pages": total_pages
        })
    print("past the missing columns")

    base_name, ext = os.path.splitext(os.path.basename(file.filename))

    # Ensure the file has the .xlsx extension
    if ext.lower() != '.xlsx':
        raise ValueError("The file must have an .xlsx extension.")

    timestamp = datetime.now(timezone.utc)
    est_timezone = pytz.timezone('America/New_York')
    timestamp_est = timestamp.astimezone(est_timezone)
    formatted_time = timestamp_est.strftime('%Y-%m-%d_%H-%M-%S')
    new_file_name = f"{base_name}_{formatted_time}{ext}"
    file_path = f"{DIRECTORY_NAME}/{new_file_name}"
    user_info = jwt.decode(user_token, options={"verify_signature": False})

    new_upload = FileUpload(
        crm_id=file.filename,  # or generate a unique ID
        owner=user_info['name'],
        status='In-Progress',
        error=None,
        input_file_link=file_path,
        upload_date=timestamp_est
    )

    db.add(new_upload)
    db.commit()
    try:
        upload_to_azure(file_path, file_data)
        await process_action(file_path, file_data, new_upload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return RedirectResponse(url="/?message=File uploaded successfully", status_code=303)


@app.get("/download_input_file/uploads/{filename}", name="download_input_file")
async def download_file(filename: str):
    decoded_file_name = unquote(filename)

    try:
        file_data = download_from_azure(f'uploads/{decoded_file_name}')
        file_data_stream = io.BytesIO(file_data)
    except Exception as e:
        raise HTTPException(status_code=404, detail="File not found")

    return StreamingResponse(file_data_stream, media_type="application/octet-stream")


@app.get("/download_output_file/outputs/{filename}")
async def download_file_output(filename: str):
    decoded_file_name = unquote(filename)
    print("code is in the outputs")
    try:
        file_data = download_from_azure(f'outputs/{decoded_file_name}')
        file_data_stream = io.BytesIO(file_data)
    except Exception as e:
        raise HTTPException(status_code=404, detail="File not found")

    return StreamingResponse(file_data_stream, media_type="application/octet-stream")


@app.get("/download_failed_file/errors/{filename}")
async def download_file_output(filename: str):
    decoded_file_name = unquote(filename)
    print("code is in the outputs")
    try:
        file_data = download_from_azure(f'errors/{decoded_file_name}')
        file_data_stream = io.BytesIO(file_data)
    except Exception as e:
        raise HTTPException(status_code=404, detail="File not found")

    return StreamingResponse(file_data_stream, media_type="application/octet-stream")


@app.post("/upload-configs/", response_class=HTMLResponse)
async def upload_file(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db),
                      user_token: str = Cookie(None)):
    # Check the file content type to ensure it's an .xlsx file
    file_data = await file.read()
    if file.content_type != "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        records, total_pages = await get_all_upload_records_from_db(db)
        error_message = "Only .xlsx files are allowed."
        return templates.TemplateResponse("upload_home.html", {
            "request": request,
            "uploads": records,
            "error": error_message,
            "page": 1,
            "total_pages": total_pages
        })
    file_path = f"configs/{file.filename}"
    user_info = jwt.decode(user_token, options={"verify_signature": False})

    try:
        upload_to_azure(file_path, file_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return RedirectResponse(url="/?message=File uploaded successfully", status_code=303)
