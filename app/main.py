from fastapi import FastAPI, WebSocket, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import os
import hashlib
from pydantic import BaseModel
from typing import List
from . import audio_interface_helper as aih

app = FastAPI()
load_dotenv()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

PASSWORD = hashlib.md5((os.getenv("PASSWORD").encode()))

testing_classes = {
    "MultiOutsSineTest": None
}


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

# use this if on nvidia jetson to filter out unwanted devices
def filter_out_NVIDIA_devices(devices):
    # filter out every entry that starts with NVIDIA
    prefixes = ["NVIDIA", "hdmi", "pulse", "default"]
    return [device for device in devices if not any(device.startswith(prefix) for prefix in prefixes)]
    

settings = {
    "audio_settings": {
        "devices": filter_out_NVIDIA_devices(aih.get_devices_names(aih.get_out_devices())),
        "channel1": 1,
        "channel2": 2,
        "channel3": 3,
        "sine1_freq": 440,
        "sine2_freq": 220,
        "sine3_freq": 110,
        "sine1_volume": 0.1,
        "sine2_volume": 0.1,
        "sine3_volume": 0.1,
    }
}

@app.get("/settings")
async def get_settings():
    settings_json = { "settings": settings }
    return JSONResponse(content=settings_json)

class testSinePayload(BaseModel):
    device_name: str
    chanel: int
    freq: float
    volume_multiply: float

@app.get("/test_sine_out")
async def test_sine_out(payload: testSinePayload):
    try:
        device_index = aih.get_device_index(aih.get_out_devices(), payload.device_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    if testing_classes["MultiOutsSineTest"] is None:
        testing_classes["MultiOutsSineTest"] = aih.MultiOutsSineTest(device_index)
    elif testing_classes["MultiOutsSineTest"].device_index != device_index:
        testing_classes["MultiOutsSineTest"].shutdown()
        testing_classes["MultiOutsSineTest"] = aih.MultiOutsSineTest(device_index)
    try: 
        testing_classes["MultiOutsSineTest"].add_sine(payload.chanel, payload.freq, payload.volume_multiply)
        return JSONResponse(content={"success": True})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
class stopSinePayload(BaseModel):
    chanel: int
    
@app.get("/stop_sine_out")
async def stop_sine_out(payload: stopSinePayload):
    if testing_classes["MultiOutsSineTest"] is None:
        raise HTTPException(status_code=400, detail="No sine test running")
    try:
        testing_classes["MultiOutsSineTest"].remove_sine(payload.chanel)
        return JSONResponse(content={"success": True})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/shutdown_sine_test")
async def shutdown_sine_test():
    if testing_classes["MultiOutsSineTest"] is None:
        raise HTTPException(status_code=400, detail="No sine test running")
    try:
            del testing_classes["MultiOutsSineTest"]
            testing_classes["MultiOutsSineTest"] = None
            return JSONResponse(content={"success": True})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


