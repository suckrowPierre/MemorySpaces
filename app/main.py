from fastapi import FastAPI, WebSocket, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import os
import hashlib
from pydantic import BaseModel
from typing import List

app = FastAPI()
load_dotenv()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

PASSWORD = hashlib.md5((os.getenv("PASSWORD").encode()))

def load_questions():
    with open("data/questions.txt", "r") as f:
        lines = f.readlines()
        lines = [line for line in lines if line != "\n"]
        lines = [line.strip() for line in lines]
    return lines

QUESTIONS = load_questions()

@app.get("/")
async def get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/login")
async def login(password: dict):
    received_password_hash = password.get("password")
    if received_password_hash == PASSWORD.hexdigest():
        return JSONResponse(content={"success": True})
    else:
        raise HTTPException(status_code=401, detail="Incorrect password")
    
@app.get("/questions")
async def get_questions():
    return JSONResponse(content={"questions": QUESTIONS})   

class generatePayload(BaseModel):
    id: int
    answers: List[str]

@app.post("/generate")
async def generate(payload: generatePayload):
    print(id, payload.id)
    print(payload.answers)
    return JSONResponse(content={"success": True})




