import json
from pathlib import Path
import os
from . import audio_interface_helper as aih


DATA_PATH = Path("./data/")

def load_settings(setting_category):
    try:
        with open(DATA_PATH / f"{setting_category}.json", "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error loading {setting_category}.json: {e}")
        return {}  # Return an empty dictionary or handle as needed
    except FileNotFoundError:
        print(f"{setting_category}.json file not found.")
        return {} 

def save_settings(setting_category, settings):
    with open(DATA_PATH/ f"{setting_category}.json", "w") as f:
        json.dump(settings, f, indent=4)

# use this if on nvidia jetson to filter out unwanted devices
def filter_out_NVIDIA_devices(devices):
    # filter out every entry that starts with NVIDIA
    prefixes = ["NVIDIA", "hdmi", "pulse", "default"]
    return [device for device in devices if not any(device.startswith(prefix) for prefix in prefixes)]

class SettingsCache:

    def __init__(self):
        self.settings = {
            "audio_settings": load_settings("audio_settings"),
            "audio_model_settings": load_settings("audio_model_settings"),
            "llm_settings": load_settings("llm_settings"),
            "tracker_settings": load_settings("tracker_settings"),
            "headphone_sensors_settings": load_settings("headphone_sensors_settings")
        }

    def save_setting(self, changed_setting):
        for category, new_settings in changed_setting.items():
            if category in self.settings:
                self.settings[category] = new_settings
                save_settings(category, new_settings)

    def get_settings(self, category="all"):
        if category == "all":
            return self.settings
        return self.settings.get(category, None)
    
    def get_settings_with_drop_down(self):
        self.settings["audio_settings"]["device_options"] = filter_out_NVIDIA_devices(aih.get_devices_names(aih.get_out_devices()))
        models_path = DATA_PATH / "models"
        self.settings["audio_model_settings"]["model_options"] = [folder.name for folder in models_path.iterdir() if folder.is_dir()]
        self.settings["audio_model_settings"]["device_options"] = ["mps", "cuda", "cpu"]
        return self.settings
    

    

        

