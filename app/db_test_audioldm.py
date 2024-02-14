import requests
import json
import base64
import array
import numpy as np
import audioldm2
from pathlib import Path


# Make sure to replace `http://localhost:8000` with the actual URL where your FastAPI app is running
BASE_URL = "http://0.0.0.0:5432"

def main():
    
    path = "../data/models/audioldm2"

    pipe = audioldm2.setup_pipeline(path, audioldm2.Devices.CUDA.value)
    print("success pipeline")
    audio = audioldm2.text2audio(pipe, audioldm2.generate_params("a string orchestra"))
    print("success audio")

    print("audio type: ", type(audio))
    audio = audio.tolist()
    
    # Post audio to memory_space 1 and sound_event 1
    response = requests.post(f"{BASE_URL}/audio/0/0", json={"audio": audio, "prompt": "Hello World"})
    assert response.status_code == 200
    print("success audio")
    

if __name__ == "__main__":
    main()

