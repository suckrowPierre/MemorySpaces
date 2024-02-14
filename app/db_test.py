import requests
import json
import base64
import array
import numpy as np

# Make sure to replace `http://localhost:8000` with the actual URL where your FastAPI app is running
BASE_URL = "http://0.0.0.0:5432"

def run_audio_flow():
    # Initialize and fill the database correctly
    
    # Define a sample audio payload
    sample_audio = [5, 5, 5, 5]  # Example audio data
    
    # Post audio to memory_space 1 and sound_event 1
    response = requests.post(f"{BASE_URL}/audio/1/0", json={"audio": sample_audio, "prompt": "Hello World"})
    assert response.status_code == 200
    print("success audio")
    
    # Fetch audios for memory_space 1 and sound_event 1
    response = requests.get(f"{BASE_URL}/audios/0/0")
    assert response.status_code == 200
    # Handle the response validation according to your application's logic
    print(response.json())
    print("success audios")

    response_data = response.json()
    print(response_data)

if __name__ == "__main__":
    run_audio_flow()

