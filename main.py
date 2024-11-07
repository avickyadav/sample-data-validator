import math
from datetime import datetime
from fastapi.responses import HTMLResponse
from datetime import timedelta
from fastapi import FastAPI, Depends, HTTPException, status, Request, Cookie, UploadFile, File, Query
from fastapi.responses import RedirectResponse, JSONResponse, Response
import httpx
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import jwt
from jwt import PyJWTError
import requests
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from typing import List, Dict

from database import get_db
from models import FileUpload
from schema import FileUploadSchema

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

uploads = [
    {
        "crm_id": "CRM001",
        "owner": "Alice",
        "upload_date": datetime(2024, 10, 20),
        "status": "Completed",
        "error": None,
    },
    {
        "crm_id": "CRM001",
        "owner": "Alice",
        "upload_date": datetime(2024, 10, 21),
        "status": "Failed",
        "error": "File format not supported",
    },
    {
        "crm_id": "CRM002",
        "owner": "Bob",
        "upload_date": datetime(2024, 10, 22),
        "status": "In Progress",
        "error": None,
    },
    {
        "crm_id": "CRM002",
        "owner": "Bob",
        "upload_date": datetime(2024, 10, 23),
        "status": "Completed",
        "error": None,
    },
    {
        "crm_id": "CRM003",
        "owner": "Charlie",
        "upload_date": datetime(2024, 10, 24),
        "status": "Failed",
        "error": "File too large",
    },
    {
        "crm_id": "CRM003",
        "owner": "Charlie",
        "upload_date": datetime(2024, 10, 25),
        "status": "Completed",
        "error": None,
    },
    {
        "crm_id": "CRM001",
        "owner": "Alice",
        "upload_date": datetime(2024, 10, 26),
        "status": "In Progress",
        "error": None,
    },
    {
        "crm_id": "CRM004",
        "owner": "David",
        "upload_date": datetime(2024, 10, 27),
        "status": "Completed",
        "error": None,
    },
    {
        "crm_id": "CRM005",
        "owner": "Eve",
        "upload_date": datetime(2024, 10, 28),
        "status": "Failed",
        "error": "Unauthorized access",
    },
    {
        "crm_id": "CRM005",
        "owner": "Eve",
        "upload_date": datetime(2024, 10, 29),
        "status": "Completed",
        "error": None,
    },
]


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
    print(list(history))
    if not history:
        raise HTTPException(status_code=404, detail="Records not found")
    return history  # This will return a list of FileUploadSchema instances


@app.get("/", response_class=HTMLResponse)
async def protected_route(request: Request, user_token: str = Cookie(None), message: str = None,
                          db: Session = Depends(get_db), page: int = Query(1, ge=1), limit: int = Query(5, ge=1)):
    print(f'this is user token {user_token}')
    if user_token is None:
        return RedirectResponse(url="/login")  # Redirect if not authenticated
    uploads_records_data, total_pages = await get_all_upload_records_from_db(db, limit, page)
    print(f"This is page data {page} and {total_pages}")
    return templates.TemplateResponse("upload_home.html",
                                      {"request": request, "uploads": uploads_records_data, "message": message, "page": page, "total_pages": total_pages})


async def get_all_upload_records_from_db(db, limit=5, page=1):
    total_records = db.query(FileUpload).count()  # Count total records
    total_pages = math.ceil(total_records / limit)  # Calculate total pages
    # Fetch records for the current page
    upload_records = db.query(FileUpload).order_by(FileUpload.upload_date.desc()).offset((page - 1) * limit).limit(limit).all()
    return upload_records, total_pages





@app.post("/upload/", response_class=HTMLResponse)
async def upload_file(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db), user_token: str= Cookie(None)):
    # Check the file content type to ensure it's an .xlsx file
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
    user_info = jwt.decode(user_token, options={"verify_signature": False})
    new_upload = FileUpload(
        crm_id=file.filename,  # or generate a unique ID
        owner=user_info['name'],
        status='Completed',
        error=None,
    )

    db.add(new_upload)
    db.commit()

    return RedirectResponse(url="/?message=File uploaded successfully", status_code=303)
