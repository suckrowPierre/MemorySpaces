import time
import multiprocessing as mp
import numpy as np
import requests
from enum import Enum
import ctypes
import random
from . import audioldm2
from . import LLM_api_connector as LLMac
from . import prompt_queue as pq
mp.set_start_method('spawn', force=True)

class AudioGenerationStatus(Enum):
    INITIALIZING = "Initializing audio pipeline"
    INITIALIZED = "Audio pipeline initialized"
    GENERATING = "Generating audio"
    GENERATED = "Audio generated"
    TOBDB = "Sendt audio to DB"

    BLOCKED = "Blocked"
    UNBLOCKED = "Unblocked"

class PromptExtractionStatus(Enum):
    INITIALIZING_LLM = "Initializing LLM"
    INITIALIZED_LLM = "LLM initialized"
    WAITING = "Waiting for input"
    EXTRACTING = "Extracting prompts"
    PROMPTS_EXTRACTED = "Prompts extracted"
    PROMPTS_QUEUED = "Prompts queued"

    MEMORY_CLEARED = "Memory cleared"
    ERROR = "Error"

class PromptExtractionInputs(Enum):
    QA_INPUT = "QA input"

class PlaybackStatus(Enum):
    PLAYING = "Playing"
    STOPPED = "Stopped"

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

def extract_prompts(llm, qa):
    return llm.extract_prompts(qa)

def block_generator(generator_blocked_boolean):
    generator_blocked_boolean.value = True

def unblock_generator(generator_blocked_boolean):
    generator_blocked_boolean.value = False


def queue_prompts(prompt_queue, llm_settings, memory_space_index, prompts):
    pq.add_prompts_to_queue_bulk(prompt_queue, prompts, memory_space_index, llm_settings["number_sound_events"], llm_settings["number_prompts"])


def prompt_extraction_process(parallel_process_communication_pipe, audiogeneration_communication_pipe, generator_blocked_boolean, prompt_queue, llm_settings, api_key):
    parallel_process_communication_pipe.send(create_communicator(PromptExtractionStatus.INITIALIZING_LLM))

    llm = LLMac.LLMApiConnector(api_key, **llm_settings)
    parallel_process_communication_pipe.send(create_communicator(PromptExtractionStatus.INITIALIZED_LLM))
    
    wait_for_status(audiogeneration_communication_pipe, AudioGenerationStatus.INITIALIZED)


    while True:
        parallel_process_communication_pipe.send(create_communicator(PromptExtractionStatus.WAITING))
        msg = parallel_process_communication_pipe.recv()
        if msg["command"] == PromptExtractionInputs.QA_INPUT:
            memory_space_index, qa = msg["memory_space_index"], msg["qa"]
            try:
                parallel_process_communication_pipe.send(create_communicator(PromptExtractionStatus.EXTRACTING, memory_space_index=memory_space_index))
                # block and clear queue for memory space
                block_generator(generator_blocked_boolean)
                wait_for_status(audiogeneration_communication_pipe, AudioGenerationStatus.BLOCKED)
                print("blocked generator to clear memory space from prompt queue")
                clear_memory_space_from_queue(prompt_queue, memory_space_index)
                print("cleared memory")

                # clear memory space from db
                clear_memory_space_db(memory_space_index)

                # unblock generator and extract prompts
                unblock_generator(generator_blocked_boolean)
                wait_for_status(audiogeneration_communication_pipe, AudioGenerationStatus.UNBLOCKED)
                print("unblocked generator")
                prompts = extract_prompts(llm,qa)
                print(str(prompts))
                parallel_process_communication_pipe.send(create_communicator(PromptExtractionStatus.PROMPTS_EXTRACTED, memory_space_index=memory_space_index))
                
                # block and queue prompts
                block_generator(generator_blocked_boolean)
                wait_for_status(audiogeneration_communication_pipe, AudioGenerationStatus.BLOCKED)
                print("blocked generator to queue prompts")
                queue_prompts(prompt_queue, llm_settings, memory_space_index, prompts)
                parallel_process_communication_pipe.send(create_communicator(PromptExtractionStatus.PROMPTS_QUEUED, memory_space_index=memory_space_index))

                # unblock generator
                unblock_generator(generator_blocked_boolean)
                wait_for_status(audiogeneration_communication_pipe, AudioGenerationStatus.UNBLOCKED)
                print("unblocked generator")
            except Exception as e:
                print(e)
                parallel_process_communication_pipe.send(create_communicator(PromptExtractionStatus.ERROR))

def pop_prompt(prompt_queue):
    memory_space_index, sound_event_index, prompt_index, prompt = pq.pop_random_element(prompt_queue)
    return memory_space_index, sound_event_index, prompt_index, prompt

def generate(audio_pipe, parameters, prompt):
    model_parameters = {"prompt": prompt, **parameters}
    audio = audioldm2.text2audio(audio_pipe, model_parameters)
    return audio

def put_into_db(prompt, audio, memory_space_index, sound_event_index):
    audio = audio.tolist()
    BASE_URL = "http://0.0.0.0:5432" # makes this changeable from frontend
    response = requests.post(f"{BASE_URL}/audio/{memory_space_index}/{sound_event_index}", json={"audio": audio, "prompt": prompt})
    if response.status_code == 200:
        return True
    return False

def clear_memory_space_db(memory_space_index):
    BASE_URL = "http://0.0.0.0:5432" # makes this changeable from frontend
    response = requests.post(f"{BASE_URL}/del_memory_space/{memory_space_index}")
    if response.status_code == 200:
        return True
    return False


def audio_generation_process(audio_generation_communication_pipe, generator_blocked_boolean, model_path, device, parameters, prompt_queue):
    print(create_communicator(AudioGenerationStatus.INITIALIZING))
    audio_pipe = audioldm2.setup_pipeline(model_path, device)
    print("pipe loaded")
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
                    
                    put_into_db(prompt, audio, memory_space_index, sound_event_index)

                    print(create_communicator(AudioGenerationStatus.TOBDB, memory_space_index=memory_space_index, sound_event_index=sound_event_index, prompt_index=prompt_index))
                    print(len(prompt_queue))
                
            except Exception as e:
                print(e)
                time.sleep(1)
                       

class ParallelProcessor:

    def __init__(self, model_path, api_key, audio_model_settings, llm_settings):
        self.llm_settings = llm_settings
        self.api_key = api_key

        self.generator_blocked = mp.Value(ctypes.c_bool, False)

        self.number_sound_events = llm_settings["number_sound_events"]
        self.number_prompts = llm_settings["number_prompts"]

        self.manager = mp.Manager()
        
        self.prompt_queue = pq.initialize_prompt_queue(self.manager)
        self.audio_generation_parent_channel, self.audio_generation_child_channel = mp.Pipe(duplex=True)
        self.parallel_process_parent_channel, self.parallel_process_child_channel = mp.Pipe(duplex=True)

        self.prompt_extraction_process = None
        self.audio_generation_process = None

        self.model_path = str(model_path / audio_model_settings.pop("model"))
        self.device = audio_model_settings.pop("device")
        self.parameters = audio_model_settings

        self.init_audio_generation_process()
        self.init_prompt_extraction_process()

    def get_audio_generation_parent_channel(self):
        return self.audio_generation_parent_channel

    def get_parallel_process_parent_channel(self):
        return self.parallel_process_parent_channel

    def print_prompt_queue(self):
        print(self.prompt_queue)

    def init_audio_generation_process(self):
        self.audio_generation_process = mp.Process(target=audio_generation_process, args=(
            self.audio_generation_child_channel, self.generator_blocked , self.model_path, self.device, self.parameters, self.prompt_queue))
        self.audio_generation_process.start()

    def init_prompt_extraction_process(self):
        self.prompt_extraction_process = mp.Process(target=prompt_extraction_process, args=(
            self.parallel_process_child_channel, self.audio_generation_parent_channel, self.generator_blocked , self.prompt_queue, self.llm_settings, self.api_key))
        self.prompt_extraction_process.start()
    

