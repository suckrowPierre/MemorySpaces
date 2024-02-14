import requests
import json
import base64
import array
import numpy as np

# Make sure to replace `http://localhost:8000` with the actual URL where your FastAPI app is running
BASE_URL = "http://0.0.0.0:5432"

def run_audio_flow():
    # Initialize and fill the database correctly
    response = requests.post(f"{BASE_URL}/init_sound_events", json={"number_sound_events": 4})
    assert response.status_code == 200
    assert response.json() == {"success": True}
    print("success init_sound_events")
    
    # Define a sample audio payload
    sample_audio = [0.1, 0.2, 0.3, 0.4]  # Example audio data
    
    # Post audio to memory_space 1 and sound_event 1
    response = requests.post(f"{BASE_URL}/audio/1/1", json={"audio": sample_audio})
    assert response.status_code == 200
    assert response.json() == {"success": True}
    print("success audio")
    
    # Fetch audios for memory_space 1 and sound_event 1
    response = requests.get(f"{BASE_URL}/audios/1/1")
    assert response.status_code == 200
    # Handle the response validation according to your application's logic
    print(response.json())
    print("success audios")

    response_data = response.json()
    print(response_data)

if __name__ == "__main__":
    run_audio_flow()

