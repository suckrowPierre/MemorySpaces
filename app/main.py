from fastapi import FastAPI, WebSocket, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import os
import hashlib
from pydantic import BaseModel
from typing import List
from pathlib import Path
import json
from enum import Enum
import asyncio
from . import audio_interface_helper as aih
from . import settings
from . import parallel_processor

app = FastAPI()
load_dotenv()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

PASSWORD = hashlib.md5((os.getenv("PASSWORD").encode()))
API_KEY = os.getenv("LLM_API_KEY")
MODEL_PATH = Path("./data/models")


settings_cache = settings.SettingsCache()
parallel_processor_instance = None


testing_classes = {
    "MultiOutsSineTest": None
}

class ParallelProcessorWebsocketStatus(Enum):
    NOT_STARTED = "Not started"
    INITIALIZING_LLM = "Initializing LLM"
    READY = "Ready for input"

    EXTRACTING_PROMTPS = "Extracting prompts"
    EXTRACTED_PROMPTS = "Prompts extracted"

    PLAYING = "Playing"
    BLOCKED = "Blocked"
    UNBLOCKED = "Unblocked"

    ERROR = "Error"

class ParallelProcessorWebsocketInputs(Enum):
    ANSWERS = "answers"

start_endpoint = "/start"
login_endpoint = "/login"
settings_endpoint = "/settings"
settings_disk_endpoint = "/settings/disk"
questions_endpoint = "/questions"
parallel_processor_ws_endpoint = "/parallel_processor_ws"
test_sine_out_endpoint = "/test_sine_out"
stop_sine_out_endpoint = "/stop_sine_out"
shutdown_sine_test_endpoint = "/shutdown_sine_test"

def serialize_enum(enum):
    return {e.name: e.value for e in enum}

enums = {
    "input": serialize_enum(ParallelProcessorWebsocketStatus),
    "status": serialize_enum(ParallelProcessorWebsocketInputs),
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
    endpoints = {
        "start": start_endpoint,
        "login": login_endpoint,
        "settings": settings_endpoint,
        "settings_disk": settings_disk_endpoint,
        "questions": questions_endpoint,
        "parallel_processor_ws": parallel_processor_ws_endpoint,
        "test_sine_out": test_sine_out_endpoint,
        "stop_sine_out": stop_sine_out_endpoint,
        "shutdown_sine_test": shutdown_sine_test_endpoint
    }
    endpoints_json = json.dumps(endpoints)
    print(endpoints_json)
    return templates.TemplateResponse("index.html", {"request": request, "endpoints": endpoints_json, "enums": enums})

@app.post(start_endpoint)
async def start():
    global parallel_processor_instance
    settings = get_settings_json(load_from_disk=True)
    audio_settings = settings["settings"]["audio_settings"]
    audio_model_settings = settings["settings"]["audio_model_settings"]
    llm_settings = settings["settings"]["llm_settings"]
    parallel_processor_instance = parallel_processor.ParallelProcessor(MODEL_PATH, API_KEY,  audio_settings, audio_model_settings,
                                                    llm_settings)
    return JSONResponse(content={"success": True})

@app.post(login_endpoint)
async def login(password: dict):
    received_password_hash = password.get("password")
    if received_password_hash == PASSWORD.hexdigest():
        return JSONResponse(content={"success": True})
    else:
        raise HTTPException(status_code=401, detail="Incorrect password")
    
@app.get(questions_endpoint)
async def get_questions():
    return JSONResponse(content={"questions": QUESTIONS})   

class generatePayload(BaseModel):
    id: int
    answers: List[str]

def get_websocket_communicator(status: ParallelProcessorWebsocketStatus, memory_space_index: int = -1):
    if memory_space_index != -1:
        return {"statusParallelProcessor": status.value, "memory_space_index": memory_space_index}
    return {"statusParallelProcessor": status.value}
    


@app.websocket(parallel_processor_ws_endpoint)
async def parallel_processor_ws(websocket: WebSocket):
    await websocket.accept()
    while parallel_processor_instance is None:
        await websocket.send_json(get_websocket_communicator(ParallelProcessorWebsocketStatus.NOT_STARTED))
        await asyncio.sleep(1)

    parallel_processor_communication_pipe = parallel_processor_instance.get_parallel_process_parent_channel()
    while True:
        msg = parallel_processor_communication_pipe.recv()
        print("MAIN PROCESS:" + str(msg))
        if msg["status"] == parallel_processor.PromptExtractionStatus.INITIALIZING:
            await websocket.send_json(get_websocket_communicator(ParallelProcessorWebsocketStatus.INITIALIZING_LLM))
        elif msg["status"] == parallel_processor.PromptExtractionStatus.WAITING:
            await websocket.send_json(get_websocket_communicator(ParallelProcessorWebsocketStatus.READY))
            recieved = await websocket.receive_json()
            if recieved["input"] == ParallelProcessorWebsocketInputs.ANSWERS.value:
                answers = recieved["data"]
                q_and_a = "\n".join([f"{q}\n{a}" for q, a in zip(QUESTIONS, answers)])
                print("Q AND A-------------------------------")
                print(q_and_a)
                print("Q AND A-------------------------------")
        elif msg["status"] == parallel_processor.PromptExtractionStatus.EXTRACTING:
            await websocket.send_json(get_websocket_communicator(ParallelProcessorWebsocketStatus.EXTRACTING_PROMTPS, msg["memory_space_index"]))
        elif msg["status"] == parallel_processor.PromptExtractionStatus.PROMPTS_EXTRACTED:
            await websocket.send_json(get_websocket_communicator(ParallelProcessorWebsocketStatus.EXTRACTED_PROMPTS, msg["memory_space_index"]))



def get_settings_json(load_from_disk: bool = False):
    if load_from_disk:
        settings_cache.load_from_disk()
    return {"settings": settings_cache.get_settings_with_drop_down()}

@app.get(settings_endpoint)
async def settings():
    settings_json = get_settings_json()
    return JSONResponse(content=settings_json)

@app.get(settings_disk_endpoint)
async def settings_disk():
    settings_json = get_settings_json(load_from_disk=True)
    return JSONResponse(content=settings_json)

@app.post(settings_endpoint)
async def save_settings(settings: dict):
    settings_cache.save_setting(settings)
    return JSONResponse(content={"success": True})

class testSinePayload(BaseModel):
    device_name: str
    channel: int
    freq: float
    volume_multiply: float

@app.get(test_sine_out_endpoint)
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
        testing_classes["MultiOutsSineTest"].add_sine(payload.channel, payload.freq, payload.volume_multiply)
        return JSONResponse(content={"success": True})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
class stopSinePayload(BaseModel):
    channel: int
    
@app.get(stop_sine_out_endpoint)
async def stop_sine_out(payload: stopSinePayload):
    if testing_classes["MultiOutsSineTest"] is None:
        raise HTTPException(status_code=400, detail="No sine test running")
    try:
        testing_classes["MultiOutsSineTest"].remove_sine(payload.channel)
        return JSONResponse(content={"success": True})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get(shutdown_sine_test_endpoint)
async def shutdown_sine_test():
    if testing_classes["MultiOutsSineTest"] is None:
        raise HTTPException(status_code=400, detail="No sine test running")
    try:
            del testing_classes["MultiOutsSineTest"]
            testing_classes["MultiOutsSineTest"] = None
            return JSONResponse(content={"success": True})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


