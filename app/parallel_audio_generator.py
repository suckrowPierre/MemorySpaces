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

def initalize_chache(manager, number_of_memory_spaces):
    cache = manager.dict()
    for i in range(number_of_memory_spaces):
        cache[i] = manager.dict()
    return cache

def clear_memory_space(manager, cache, memory_space):
    cache[memory_space] = manager.dict()

def append_to_memory_space(manager, cache, memory_space, sound_event, data):
    cache[memory_space][sound_event] = manager.dict()
    cache[memory_space][sound_event].append(data)

def create_shared_audio_array(audio_array):
    audio_mp_array = mp.Array('f', audio_array.shape[0])
    audio_mp_array[:] = audio_array[:]
    return audio_mp_array

def get_audio_from_cache(cache, memory_space, sound_event):
    return cache[memory_space][sound_event]

def print_cache(cache):
    for memory_space in cache:
        print("memory_space: " + str(memory_space))
        if len(cache[memory_space]) == 0:
            print("--empty")
        else:
            for sound_event in cache[memory_space]:
                print("--sound_event: " + str(sound_event))
                if len(cache[memory_space][sound_event]) == 0:
                    print("----empty")
                else:
                    for audio in cache[memory_space][sound_event]:
                        print("----audio: " + str(audio))

class ParallelAudioGenerator:

    def __init__(self, audio_settings, audio_model_settings, llm_settings):
        self.manager = mp.Manager()

        self.generator_process = None
        self.playback_processes = []

        self.interface = audio_settings["device"]
        self.sr = 16000
        self.nchnls = 3
        self.channels = [audio_settings["channel1"], audio_settings["channel2"], audio_settings["channel3"]]

        # pop model path from audio_model_settings
        self.model_path = audio_model_settings.pop("model")
        self.device = audio_model_settings.pop("device")
        self.parameters = audio_model_settings

        self.number_soundevents = llm_settings["number_soundevents"]
        self.number_prompts = llm_settings["number_prompts"]

        self.cache = initalize_chache(self.manager, self.nchnls)
    
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

