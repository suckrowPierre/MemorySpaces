from fastapi import FastAPI, Depends
import sqlite3
from pathlib import Path
from pydantic import BaseModel
from typing import List
import array
import base64
import json
import numpy as np
import pickle
from io import BytesIO



app = FastAPI()

DB_PATH = Path("./db/audio.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Enables column access by name
    try:
        yield conn
    finally:
        conn.close()


def create_db(conn):
    cursor = conn.cursor()

    # Create memory spaces table
    cursor.execute("CREATE TABLE IF NOT EXISTS memory_space (id INTEGER PRIMARY KEY)")

    # Create sound event table
    cursor.execute("""CREATE TABLE IF NOT EXISTS sound_event (
        id INTEGER PRIMARY KEY, 
        memory_space_id INTEGER, 
        FOREIGN KEY(memory_space_id) REFERENCES memory_space(id))""")

    # Create audio table
    cursor.execute("""CREATE TABLE IF NOT EXISTS audio (
        id INTEGER PRIMARY KEY, 
        sound_event_id INTEGER, 
        audio_data TEXT NOT NULL, 
        FOREIGN KEY(sound_event_id) REFERENCES sound_event(id))""")

    cursor.close()

def fill_structure(conn, number_memory_spaces):
    cursor = conn.cursor()
    # Fill memory spaces
    for i in range(1, number_memory_spaces + 1):
        cursor.execute("INSERT INTO memory_space (id) VALUES (?)", (i,))
    cursor.close()


async def startup_event():
    # Ensure the directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    try:
        create_db(conn)
        # Check if it's the first time populating the database
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM memory_space")
        count = cursor.fetchone()[0]
        if count == 0:  # It's empty, fill the tables
            fill_structure(conn, 3)  # Example values, adjust as needed
        conn.commit()
    finally:
        conn.close()


@app.get("/")
async def helf():
    return {"message": "Hello World"}

@app.get("/memory_spaces")
async def memory_spaces(conn: sqlite3.Connection = Depends(get_db_connection)):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM memory_space")
    memory_spaces = cursor.fetchall()
    return [dict(memory_space) for memory_space in memory_spaces]

class audioPayload(BaseModel):
    # audio list of floats representing the audio data
    audio: List[float]

class InitSoundEventsRequest(BaseModel):
    number_sound_events: int

@app.post("/init_sound_events")
async def init_sound_events(request: InitSoundEventsRequest, conn: sqlite3.Connection = Depends(get_db_connection)):
    number_sound_events = request.number_sound_events
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM memory_space")
    memory_spaces = cursor.fetchall()
    for memory_space in memory_spaces:
        for i in range(number_sound_events):
            cursor.execute("INSERT INTO sound_event (memory_space_id) VALUES (?)", (memory_space["id"],))
    conn.commit()
    return {"success": True}

@app.post("/audio/{memory_space_id}/{sound_event_id}")
async def audio(memory_space_id: int, sound_event_id: int, payload: audioPayload, conn: sqlite3.Connection = Depends(get_db_connection)):
    audio_list = payload.audio
    audio_array = np.array(audio_list, dtype=np.float64)  # Use np.float64 for high precision
    # Serialize the NumPy array using pickle
    audio_pickle = pickle.dumps(audio_array)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO audio (sound_event_id, audio_data) VALUES (?, ?)", (sound_event_id, audio_pickle))
    conn.commit()
    return {"success": True}

@app.get("/audios/{memory_space_id}/{sound_event_id}")
async def audios(memory_space_id: int, sound_event_id: int, conn: sqlite3.Connection = Depends(get_db_connection)):
    cursor = conn.cursor()
    cursor.execute("SELECT audio_data FROM audio WHERE sound_event_id = ?", (sound_event_id,))
    audio_row = cursor.fetchone()
    if audio_row:
        audio_pickle = audio_row["audio_data"]
        # Deserialize the NumPy array from pickle
        audio_array = pickle.loads(audio_pickle)
        audio_list = audio_array.tolist()
        return {"audio": audio_list}
    return {"audio": None}

@app.post("/del_audio/{memory_space_id}}")
async def del_audio(memory_space_id: int, conn: sqlite3.Connection = Depends(get_db_connection)):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM audio WHERE sound_event_id IN (SELECT id FROM sound_event WHERE memory_space_id = ?)", (memory_space_id,))
    conn.commit()
    return {"success": True}

@app.get("/number_of_sound_events/{memory_space_id}")
async def number_of_sound_events(memory_space_id: int, conn: sqlite3.Connection = Depends(get_db_connection)):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sound_event WHERE memory_space_id = ?", (memory_space_id,))
    count = cursor.fetchone()[0]
    return {"number_of_sound_events": count}

@app.get("/random_audio/{memory_space_id}/{sound_event_id}")
async def random_audio(memory_space_id: int, sound_event_id: int, conn: sqlite3.Connection = Depends(get_db_connection)):
    cursor = conn.cursor()
    cursor.execute("SELECT audio_data FROM audio WHERE sound_event_id = ? ORDER BY RANDOM() LIMIT 1", (sound_event_id,))
    audio = cursor.fetchone()
    return {"audio": audio}







# start up 
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

with sqlite3.connect(DB_PATH) as conn:
    create_db(conn)
    # Check if it's the first time populating the database
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM memory_space")
    count = cursor.fetchone()[0]
    if count == 0:  # It's empty, fill the tables
        fill_structure(conn, 3)  # Example values, adjust as needed
    conn.commit()
