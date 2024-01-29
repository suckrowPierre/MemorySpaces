import time
import multiprocessing as mp
mp.set_start_method('spawn', force=True)
import numpy as np
from enum import Enum
import audioldm2
import cache

class GenerationStatus(Enum):
    EXTRACTING = "extracting sound events and prompts from q&a"
    INIZIALIZING = "inizializing audioldm2 pipe"
    INIZIALIZED = "audioldm2 pipe inizialized"
    WAITING_FOR_PROMPT = "waiting for prompt"
    PROMPT_RECEIVED = "prompt received"
    GENERATING = "generating audio"
    PLAYING = "playing audio"

def get_communicator(status, **kwargs):
    communicator = {
        "status": status,
    }
    communicator.update(kwargs)
    return communicator

def communicator_to_string(communicator):
    string = ""
    for key, value in communicator.items():
        # check if value is enum 
        if isinstance(value, Enum):
            value = value.value
        string += f"{key}: {value} "
    return string

def generator(c, model_path, device, parameters, cache):
    c.send(get_communicator(GenerationStatus.INIZIALIZING))
    pipe = audioldm2.setup_pipeline(model_path, device)
    c.send(get_communicator(GenerationStatus.INIZIALIZED))
    while True:
        c.send(get_communicator(GenerationStatus.WAITING_FOR_PROMPT))
        prompt = c.recv()
        c.send(get_communicator(GenerationStatus.PROMPT_RECEIVED, prompt=prompt))
        c.send(get_communicator(GenerationStatus.GENERATING, prompt=prompt))
        audio = pipe(prompt, **parameters)

    
class ParallelAudioGenerator:

    def __init__(self, model_path, audio_settings, audio_model_settings, llm_settings):
        self.manager = mp.Manager()

        self.extraction_process = None
        self.generator_process = None
        self.playback_processes = []

        self.interface = audio_settings["device"]
        self.sr = 16000
        self.nchnls = 3
        self.channels = [audio_settings["channel1"], audio_settings["channel2"], audio_settings["channel3"]]

        model = audio_model_settings.pop("model")
        self.model_path = str(model_path / model)
        self.device = audio_model_settings.pop("device")
        self.parameters = audio_model_settings

        self.number_soundevents = llm_settings.get("number_soundevents", 0)
        self.number_prompts = llm_settings.get("number_prompts", 0)

        # maybe a validator for the settings would be nice

        self.generator_parent_channel, self.generator_child_channel = mp.Pipe()

        self.cache = cache._initialize_cache(self.manager, self.nchnls, self.number_soundevents, self.number_prompts)
    
    def get_generator_channel(self):
        return self.generator_parent_channel
    
    def clear_memory_space(self, memory_space):
        cache.clear_memory_space(self.cache, self.manager, memory_space)
    
    def append_to_memory_space(self, memory_space, sound_event, audio_data):
        cache.append_to_memory_space(self.cache, self.manager, memory_space, sound_event, audio_data)
    
    def get_audio_from_cache(self, memory_space, sound_event, index):
        return cache.get_audio_from_cache(self.cache, memory_space, sound_event, index)
    
    def get_len_sound_event(self, memory_space, sound_event):
        return cache.get_len_sound_event(self.cache, memory_space, sound_event)
    
    def print_cache(self):
        print(cache.cache_to_string(self.cache))
            
    def _init_generation_process(self):
        self.generator_process = mp.Process(target=generator, args=(self.generator_child_channel, self.model_path, self.device, self.parameters, self.cache))
        self.generator_process.start()
    
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

