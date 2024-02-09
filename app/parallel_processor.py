import time
import multiprocessing as mp
import numpy as np
from enum import Enum
import ctypes
#import audioldm2
#import cache
#import LLM_api_connector as LLMac
#import prompt_queue as pq
from . import audioldm2
from . import cache
from . import LLM_api_connector as LLMac
from . import prompt_queue as pq
mp.set_start_method('spawn', force=True)


class AudioGenerationStatus(Enum):
    INITIALIZING = "Initializing audio pipeline"
    INITIALIZED = "Audio pipeline initialized"
    GENERATING = "Generating audio"
    GENERATED = "Audio generated"
    CACHED = "Audio cached"

    BLOCKED = "Blocked"
    UNBLOCKED = "Unblocked"

class PromptExtractionStatus(Enum):
    INITIALIZING = "Initializing LLM"
    INITIALIZED = "LLM initialized"
    WAITING = "Waiting for input"
    EXTRACTING = "Extracting prompts"
    PROMPTS_EXTRACTED = "Prompts extracted"
    PROMPTS_QUEUED = "Prompts queued"

    MEMORY_CLEARED = "Memory cleared"
    ERROR = "Error"

class PromptExtractionInputs(Enum):
    QA_INPUT = "QA input"


def create_communicator(enum, **kwargs):
    communicator = {}
    if isinstance(enum, AudioGenerationStatus) or isinstance(enum, PromptExtractionStatus):
        communicator = {"status": enum}  # Note the use of enum.value to get the string representation
        communicator.update(kwargs)
    elif isinstance(enum, PromptExtractionInputs):
        communicator = {"command": enum}  # Same here for commands
        communicator.update(kwargs)
    return communicator


def communicator_to_string(communicator):
    string = ""
    for key, value in communicator.items():
        if isinstance(value, Enum):
            value = value.value
        string += f"{key}: {value} "
    return string

def wait_for_status(communication_pipe, status):
    msg = communication_pipe.recv()
    while msg["status"] != status:
        msg = communication_pipe.recv()

def clear_memory_space_from_queue(prompt_queue, memory_space_index):
    pq.clear_memory_space_from_queue(prompt_queue, memory_space_index)

def clear_memory_space_from_cache(audio_cache, memory_space_index):
    cache.clear_memory_space(audio_cache, memory_space_index)

def extract_prompts(llm, qa):
    return llm.extract_prompts(qa)

def block_generator(generator_blocked_boolean):
    generator_blocked_boolean.value = True

def unblock_generator(generator_blocked_boolean):
    generator_blocked_boolean.value = False


def queue_prompts(prompt_queue, llm_settings, memory_space_index, prompts):
    pq.add_prompts_to_queue_bulk(prompt_queue, prompts, memory_space_index, llm_settings["number_sound_events"], llm_settings["number_prompts"])


def prompt_extraction_process(audio_generation_communication_pipe, audiogeneration_communication_pipe, generator_blocked_boolean, audio_cache, prompt_queue, llm_settings, api_key):
    audio_generation_communication_pipe.send(create_communicator(PromptExtractionStatus.INITIALIZING))

    llm = LLMac.LLMApiConnector(api_key, **llm_settings)
    print(create_communicator(PromptExtractionStatus.INITIALIZED))
    wait_for_status(audiogeneration_communication_pipe, AudioGenerationStatus.INITIALIZED)

    while True:
        audio_generation_communication_pipe.send(create_communicator(PromptExtractionStatus.WAITING))
        msg = audio_generation_communication_pipe.recv()
        if msg["command"] == PromptExtractionInputs.QA_INPUT:
            memory_space_index, qa = msg["memory_space_index"], msg["qa"]
            try:
                # block and clear queue for memory space
                block_generator(generator_blocked_boolean)
                wait_for_status(audiogeneration_communication_pipe, AudioGenerationStatus.BLOCKED)
                print("blocked generator to clear memory space from prompt queue")
                clear_memory_space_from_queue(prompt_queue, memory_space_index)
                print("cleared memory")

                # unblock generator and extract prompts
                unblock_generator(generator_blocked_boolean)
                wait_for_status(audiogeneration_communication_pipe, AudioGenerationStatus.UNBLOCKED)
                print("unblocked generator")
                prompts = extract_prompts(llm,qa)
                
                # block and queue prompts
                block_generator(generator_blocked_boolean)
                wait_for_status(audiogeneration_communication_pipe, AudioGenerationStatus.BLOCKED)
                print("blocked generator to queue prompts")
                queue_prompts(prompt_queue, llm_settings, memory_space_index, prompts)
                
                # stop playback
                # TODO

                # clear audio cache and unblock generator
                clear_memory_space_from_cache(audio_cache, memory_space_index)
                unblock_generator(generator_blocked_boolean)
                wait_for_status(audiogeneration_communication_pipe, AudioGenerationStatus.UNBLOCKED)
                print("unblocked generator")
            except Exception as e:
                print(e)
                audio_generation_communication_pipe.send(create_communicator(PromptExtractionStatus.ERROR))

def pop_prompt(prompt_queue):
    memory_space_index, sound_event_index, prompt_index, prompt = pq.pop_random_element(prompt_queue)
    return memory_space_index, sound_event_index, prompt_index, prompt

def generate(audio_pipe, parameters, prompt):
    model_parameters = {"prompt": prompt, **parameters}
    audio = audioldm2.text2audio(audio_pipe, model_parameters)
    return audio

def cache_audio(audio_cache, memory_space_index, sound_event_index, prompt_index, audio):
    cache.put_audio_array_into_cache(audio_cache, memory_space_index, sound_event_index, prompt_index, audio)

def audio_generation_process(audio_generation_communication_pipe, generator_blocked_boolean, model_path, device, parameters, audio_cache, prompt_queue, critical_mass=10):
    print(create_communicator(AudioGenerationStatus.INITIALIZING))
    audio_pipe = audioldm2.setup_pipeline(model_path, device)
    audio_generation_communication_pipe.send(create_communicator(AudioGenerationStatus.INITIALIZED))

    while True:
        if generator_blocked_boolean.value:
            audio_generation_communication_pipe.send(create_communicator(AudioGenerationStatus.BLOCKED))
            time.sleep(1)
            #continue
        else: 
            audio_generation_communication_pipe.send(create_communicator(AudioGenerationStatus.UNBLOCKED))
            try: 
                try:
                    memory_space_index, sound_event_index, prompt_index, prompt = pop_prompt(prompt_queue)
                except ValueError:
                    time.sleep(1)
                    continue
                if prompt:
                    print(create_communicator(AudioGenerationStatus.GENERATING, memory_space_index=memory_space_index, sound_event_index=sound_event_index, prompt_index=prompt_index, prompt=prompt))
                    audio = generate(audio_pipe, parameters, prompt)
                    cache_audio(audio_cache, memory_space_index, sound_event_index, prompt_index, audio)
                    print(create_communicator(AudioGenerationStatus.CACHED, memory_space_index=memory_space_index, sound_event_index=sound_event_index, prompt_index=prompt_index))
                    print(len(prompt_queue))
                
            except Exception as e:
                print(e)
                time.sleep(1)


class ParallelProcessor:

    def __init__(self, model_path, api_key, audio_settings, audio_model_settings, llm_settings):
        self.llm_settings = llm_settings
        self.api_key = api_key

        self.generator_blocked = mp.Value(ctypes.c_bool, False)
        self.sr = 16000
        self.channels = [audio_settings["channel1"], audio_settings["channel2"], audio_settings["channel3"]]
        self.interface = audio_settings["device"]

        self.number_sound_events = llm_settings["number_sound_events"]
        self.number_prompts = llm_settings["number_prompts"]

        self.manager = mp.Manager()
        self.audio_cache = cache.initialize_cache(self.manager, len(self.channels), llm_settings['number_sound_events'],
                                                  llm_settings['number_prompts'])

        self.prompt_queue = pq.initialize_prompt_queue(self.manager)
        self.audio_generation_parent_channel, self.audio_generation_child_channel = mp.Pipe(duplex=True)
        self.parallel_process_parent_channel, self.parallel_process_child_channel = mp.Pipe(duplex=True)

        self.prompt_extraction_process = None
        self.audio_generation_process = None
        self.playback_processes = []

        self.model_path = str(model_path / audio_model_settings.pop("model"))
        self.device = audio_model_settings.pop("device")
        self.parameters = audio_model_settings#

        self.init_audio_generation_process()
        self.init_prompt_extraction_process()

    def get_audio_generation_parent_channel(self):
        return self.audio_generation_parent_channel

    def get_parallel_process_parent_channel(self):
        return self.parallel_process_parent_channel

    def clear_memory_space(self, memory_space):
        cache.clear_memory_space(self.audio_cache, memory_space)

    def put_audio_array_into_cache(self, memory_space_index, sound_event_index, prompt_index, audio_data):
        cache.put_audio_array_into_cache(self.audio_cache, memory_space_index, sound_event_index, prompt_index,
                                         audio_data)

    def get_audio_from_cache(self, memory_space_index, sound_event_index, prompt_index):
        return cache.get_audio_from_cache(self.audio_cache, memory_space_index, sound_event_index, prompt_index)

    def print_cache(self):
        print(cache.cache_to_string(self.audio_cache))

    def print_prompt_queue(self):
        print(self.prompt_queue)
        # print(pq.prompt_queue_to_string(self.prompt_queue))

    def init_audio_generation_process(self):
        self.audio_generation_process = mp.Process(target=audio_generation_process, args=(
            self.audio_generation_child_channel, self.generator_blocked , self.model_path, self.device, self.parameters, self.audio_cache, self.prompt_queue))
        self.audio_generation_process.start()

    def init_prompt_extraction_process(self):
        self.prompt_extraction_process = mp.Process(target=prompt_extraction_process, args=(
            self.parallel_process_child_channel, self.audio_generation_parent_channel, self.generator_blocked ,self.audio_cache, self.prompt_queue, self.llm_settings, self.api_key))
        self.prompt_extraction_process.start()
