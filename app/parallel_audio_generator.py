import time
import multiprocessing as mp
import numpy as np
import enum as Enum

"""
class GenerationStatus(Enum):
    EXTRACTING = "extracting sound events and prompts from q&a"
    GENERATING = "generating audio"
    PLAYING = "playing audio"
"""

class ParallelAudioGenerator:

    def __init__(self, audio_settings, audio_model_settings, llm_settings):
        self.manager = mp.Manager()

        self.generator_process = None
        self.playback_processes = []

        self.interface = audio_settings["device"]
        self.sr = 16000
        self.nchnls = 3
        self.channels = [audio_settings["channel1"], audio_settings["channel2"], audio_settings["channel3"]]

        self.model_path = audio_model_settings.pop("model")
        self.device = audio_model_settings.pop("device")
        self.parameters = audio_model_settings

        self.number_soundevents = llm_settings.get("number_soundevents", 0)
        self.number_prompts = llm_settings.get("number_prompts", 0)

        # maybe a validator for the settings would be nice

        self.cache = self._initialize_cache(self.nchnls)

    def _initialize_cache(self, number_of_memory_spaces):
        # Initialize the cache with specified number of memory spaces.
        cache = self.manager.dict()
        for i in range(number_of_memory_spaces):
            cache[i] = self.manager.dict()
        return cache
    
    def clear_memory_space(self, memory_space):
        #Clear the specified memory space in the cache.
        self.cache[memory_space] = self.manager.dict()
    
    def append_to_memory_space(self, memory_space, sound_event, data):
        #Append data to a specified memory space and sound event in the cache
        if sound_event not in self.cache[memory_space]:
            self.cache[memory_space][sound_event] = self.manager.list()
        self.cache[memory_space][sound_event].append(data.tolist())   # Might be point of failure
    
    def create_shared_audio_array(self, audio_array):
        #Create a shared array for audio data.
        audio_mp_array = mp.Array('f', audio_array.shape[0])
        audio_mp_array[:] = audio_array[:]
        return audio_mp_array
    
    def get_audio_from_cache(self, memory_space, sound_event, index):
        #Retrieve audio data from cache
        audios = self.cache[memory_space].get(sound_event, [])
        return audios[index] if index < len(audios) else None
    
    def get_len_sound_event(self, memory_space, sound_event):
        #Get the length of a sound event in a memory space.
        return len(self.cache[memory_space].get(sound_event, []))
    
    def print_cache(self):
        #Print the contents of the cache."""
        for memory_space, events in self.cache.items():
            print(f"memory_space: {memory_space}")
            if not events:
                print("--empty")
                continue
            for sound_event, audios in events.items():
                print(f"--sound_event: {sound_event}")
                if not audios:
                    print("----empty")
                    continue
                for audio in audios:
                    print(f"----audio: {audio}")


    
    def print_settings(self):
        print("interface: " + self.interface)
        print("sr: " + str(self.sr))
        print("nchnls: " + str(self.nchnls))
        print("channels: " + str(self.channels))
        print("model_path: " + self.model_path)
        print("device: " + self.device)
        print("parameters: " + str(self.parameters))
        print("number_soundevents: " + str(self.number_soundevents))
        print("number_prompts: " + str(self.number_prompts))

