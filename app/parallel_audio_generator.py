import time
import multiprocessing as mp
import numpy as np
from enum import Enum
import audioldm2
import cache
import llm

mp.set_start_method('spawn', force=True)


class GeneratorCommStatus(Enum):
    # extractor
   

    # generator
    INITIALIZING = "Initializing audio pipeline"
    INITIALIZED = "Audio pipeline initialized"
    WAITING = "Waiting for input"
    GENERATING = "Generating audio"
    CACHED = "Audio cached"
    MEMORY_CLEARED = "Memory cleared"

    # playback
    PLAYING = "Playing audio"


class GeneratorCommCommand(Enum):
    PROMPT_INPUT = "Prompt input"
    CLEAR_MEMORY = "flash memory space"

class ExtractorCommStatus(Enum):
    INITIALIZING = "Initializing LLM"
    INITIALIZED = "LLM initialized"
    WAITING = "Waiting for input"




def create_communicator(enum, **kwargs):
    communicator = {}
    if isinstance(enum, GeneratorCommStatus):
        communicator = {"status": enum}
        communicator.update(kwargs)
    elif isinstance(enum, GeneratorCommCommand):
        communicator = {"command": enum}
        communicator.update(kwargs)
    return communicator


def communicator_to_string(communicator):
    string = ""
    for key, value in communicator.items():
        if isinstance(value, Enum):
            value = value.value
        string += f"{key}: {value} "
    return string

def extractor(generator_communication_pipe):
    t = 1
    #TODO


def generator(communication_pipe, model_path, device, parameters, audio_cache, critical_mass=10):
    communication_pipe.send(create_communicator(GeneratorCommStatus.INITIALIZING))
    audio_pipe = audioldm2.setup_pipeline(model_path, device)
    communication_pipe.send(create_communicator(GeneratorCommStatus.INITIALIZED))

    while True:
        communication_pipe.send(create_communicator(GeneratorCommStatus.WAITING))
        msg = communication_pipe.recv()
        if msg["command"] == GeneratorCommCommand.PROMPT_INPUT:
            prompt, memory_space_index, sound_event_index, prompt_index = msg["prompt"], msg[
                "memory_space_index"], msg["sound_event_index"], msg["prompt_index"]
            model_parameters = {"prompt": prompt, **parameters}
            communication_pipe.send(create_communicator(GeneratorCommStatus.GENERATING))
            audio = audioldm2.text2audio(audio_pipe, model_parameters)
            cache.put_audio_array_into_cache(audio_cache, memory_space_index, sound_event_index, prompt_index, audio)
            communication_pipe.send(create_communicator(GeneratorCommStatus.CACHED))
            # check if critical mass is reached
            # ---- if yes send signal to playback process
        elif msg["command"] == GeneratorCommCommand.CLEAR_MEMORY:
            cache.clear_memory_space(audio_cache, msg["memory_space_index"])
            communication_pipe.send(create_communicator(GeneratorCommStatus.MEMORY_CLEARED))


class ParallelAudioGenerator:

    def __init__(self, model_path, audio_settings, audio_model_settings, llm_settings):
        self.sr = 16000
        self.channels = [audio_settings["channel1"], audio_settings["channel2"], audio_settings["channel3"]]
        self.interface = audio_settings["device"]

        self.number_sound_events = llm_settings["number_soundevents"]
        self.number_prompts = llm_settings["number_prompts"]

        self.manager = mp.Manager()
        self.audio_cache = cache.initialize_cache(self.manager, len(self.channels), llm_settings['number_soundevents'],
                                                  llm_settings['number_prompts'])
        self.generator_parent_channel, self.generator_child_channel = mp.Pipe(duplex=True)

        self.extraction_process = None
        self.generator_process = None
        self.playback_processes = []

        self.model_path = str(model_path / audio_model_settings.pop("model"))
        self.device = audio_model_settings.pop("device")
        self.parameters = audio_model_settings

    def get_generator_channel(self):
        return self.generator_parent_channel

    def clear_memory_space(self, memory_space):
        cache.clear_memory_space(self.audio_cache, memory_space)

    def put_audio_array_into_cache(self, memory_space_index, sound_event_index, prompt_index, audio_data):
        cache.put_audio_array_into_cache(self.audio_cache, memory_space_index, sound_event_index, prompt_index,
                                         audio_data)

    def get_audio_from_cache(self, memory_space_index, sound_event_index, prompt_index):
        return cache.get_audio_from_cache(self.audio_cache, memory_space_index, sound_event_index, prompt_index)

    def print_cache(self):
        print(cache.cache_to_string(self.audio_cache))

    def init_generation_process(self):
        self.generator_process = mp.Process(target=generator, args=(
            self.generator_child_channel, self.model_path, self.device, self.parameters, self.audio_cache))
        self.generator_process.start()

    def init_extraction_process(self):
        t = 1
        #TODO
