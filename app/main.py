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
import requests
from . import prompt_queue
from . import settings
from . import parallel_processor
import datetime

app = FastAPI()
load_dotenv()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
cache_lock = asyncio.Lock()

PASSWORD = hashlib.md5((os.getenv("PASSWORD").encode()))
API_KEY = os.getenv("LLM_API_KEY")
MODEL_PATH = Path("./data/models")
LOGGING_FOLDER = Path(os.getenv("LOGGING_FOLDER"))

# create logging folder if it does not exist
if not os.path.exists(LOGGING_FOLDER):
    os.makedirs(LOGGING_FOLDER)


settings_cache = settings.SettingsCache()
parallel_processor_instance = None
parallel_processor_status = None


testing_classes = {
    "MultiOutsSineTest": None
}

class ParallelProcessorWebsocketStatus(Enum):
    NOT_STARTED = "process not started"
    INITIALIZING = "initializing"
    SETTING_UP = "setting up"
    READY = "ready"

    EXTRACTING_PROMTPS = "extracting prompts"
    EXTRACTED_PROMPTS = "prompts extracted"

    PLAYING = "playing"
    BLOCKED = "blocked"
    UNBLOCKED = "unblocked"

    ERROR = "error"

start_endpoint = "/start"
login_endpoint = "/login"
settings_endpoint = "/settings"
settings_disk_endpoint = "/settings/disk"
questions_endpoint = "/questions"
parallel_processor_ws_endpoint = "/parallel_processor_ws"
test_sine_out_endpoint = "/test_sine_out"
stop_sine_out_endpoint = "/stop_sine_out"
shutdown_sine_test_endpoint = "/shutdown_sine_test"
generate_endpoint = "/generate"
queue_endpoint = "/queue"

def log_qa(qa: str):
    time_stemp = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    log_file_path = LOGGING_FOLDER / f"{time_stemp}_qa_log.txt"  # Use / to join paths
    with open(log_file_path, "a") as f:
        f.write(qa)


def serialize_enum(enum):
    return json.dumps({e.name: e.value for e in enum})

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
        "shutdown_sine_test": shutdown_sine_test_endpoint,
        "generate": generate_endpoint
    }
    endpoints_json = json.dumps(endpoints)
    return templates.TemplateResponse("index.html", {"request": request, "endpoints": endpoints_json, "status": serialize_enum(ParallelProcessorWebsocketStatus)})

@app.get(queue_endpoint)
async def queue():
    global parallel_processor_instance
    if parallel_processor_instance is None:
        raise HTTPException(status_code=400, detail="Parallel processor not started")
    queue = prompt_queue.prompt_queue_to_string(parallel_processor_instance.prompt_queue)
    return JSONResponse(content={"queue": queue})
        
def clear_db(URL):
    response = requests.post(f"{URL}/reset", json={})
    if response.status_code == 200:
        return True
    return False

def set_number_sound_events_DB(URL, number_sound_events):
    if number_sound_events is None:
        raise HTTPException(status_code=400, detail="Number sound events not provided")
    
    response = requests.post(f"{URL}/set_number_sound_events", json={"number_sound_events": int(number_sound_events)})
    if response.status_code == 200:
        return True
    return False

@app.post(start_endpoint)
async def start():
    global parallel_processor_instance
    settings_cache.load_from_disk()
    settings = settings_cache.get_settings()
    audio_model_settings = settings["audio_model_settings"]
    llm_settings = settings["llm_settings"]

    URL = "http://0.0.0.0:5432" 
    # clear db 
    if not clear_db(URL):
        raise HTTPException(status_code=400, detail="Could not clear db")
    
    if not set_number_sound_events_DB(URL, llm_settings["number_sound_events"]):
        raise HTTPException(status_code=400, detail="Could not set number_sound_events")
    




    parallel_processor_instance = parallel_processor.ParallelProcessor(MODEL_PATH, API_KEY, audio_model_settings, llm_settings)
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

@app.post(generate_endpoint)
async def generate(payload: generatePayload):
    global parallel_processor_status
    if parallel_processor_instance is None:
        raise HTTPException(status_code=400, detail="Parallel processor not started")
    if parallel_processor_status is not ParallelProcessorWebsocketStatus.READY:
        print(parallel_processor_status)
        raise HTTPException(status_code=400, detail="Parallel processor not ready")
    if payload.id is None:
        raise HTTPException(status_code=400, detail="ID not provided")
    if payload.answers is None:
        raise HTTPException(status_code=400, detail="Answers not provided")
    if len(payload.answers) != len(QUESTIONS):
        raise HTTPException(status_code=400, detail="Incorrect number of answers")
    answers = payload.answers
    memory_space_index = payload.id - 1 
    q_and_a = "\n".join([f"Q: {q}\n A:{a}" for q, a in zip(QUESTIONS, answers)])
    log_qa(q_and_a)
    print("Q AND A-------------------------------")
    print(q_and_a)
    print("Q AND A-------------------------------")
    try:
        communication_channel = parallel_processor_instance.get_parallel_process_parent_channel()
        communication_channel.send(parallel_processor.create_communicator(parallel_processor.PromptExtractionInputs.QA_INPUT, qa=q_and_a, memory_space_index=memory_space_index))
        return JSONResponse(content={"success": True})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@app.websocket(parallel_processor_ws_endpoint)
async def parallel_processor_ws(websocket: WebSocket):
    def get_websocket_communicator(status: ParallelProcessorWebsocketStatus, memory_space_index: int = -1):
        if memory_space_index != -1:
            return {"statusParallelProcessor": status.value, "memory_space_index": memory_space_index+1}
        return {"statusParallelProcessor": status.value}

    async def send(status: ParallelProcessorWebsocketStatus, memory_space_index: int = -1):
        global parallel_processor_status
        parallel_processor_status = status
        await websocket.send_json(get_websocket_communicator(status, memory_space_index))


    await websocket.accept()
    await send(ParallelProcessorWebsocketStatus.NOT_STARTED)
    while parallel_processor_instance is None:
        await asyncio.sleep(0.1)


    parallel_processor_communication_pipe = parallel_processor_instance.get_parallel_process_parent_channel()
    await websocket.send_json(get_websocket_communicator(ParallelProcessorWebsocketStatus.SETTING_UP))
    while True:        
        if parallel_processor_communication_pipe.poll():
            msg = parallel_processor_communication_pipe.recv()
            print("MAIN PROCESS:" + str(msg))
            if msg["status"]:
                if msg["status"] == parallel_processor.PromptExtractionStatus.INITIALIZING_LLM:
                    await send(ParallelProcessorWebsocketStatus.INITIALIZING)
                elif msg["status"] == parallel_processor.PromptExtractionStatus.WAITING:
                    await send(ParallelProcessorWebsocketStatus.READY)
                elif msg["status"] == parallel_processor.PromptExtractionStatus.EXTRACTING:
                    await send(ParallelProcessorWebsocketStatus.EXTRACTING_PROMTPS, msg["memory_space_index"])
                elif msg["status"] == parallel_processor.PromptExtractionStatus.PROMPTS_EXTRACTED:
                    await send(ParallelProcessorWebsocketStatus.EXTRACTED_PROMPTS, msg["memory_space_index"])
        
        else:
            await asyncio.sleep(0.1)
                
                

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



