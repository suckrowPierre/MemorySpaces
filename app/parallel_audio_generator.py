import time
import multiprocessing as mp
import numpy as np
from enum import Enum
import audioldm2
import cache
import LLM_api_connector as LLMac
import prompt_queue as pq
import ctypes

mp.set_start_method('spawn', force=True)


class GeneratorStatus(Enum):
    INITIALIZING = "Initializing audio pipeline"
    INITIALIZED = "Audio pipeline initialized"
    GENERATING = "Generating audio"
    GENERATED = "Audio generated"
    CACHED = "Audio cached"

    BLOCKED = "Blocked"
    UNBLOCKED = "Unblocked"

class ExtractoStatus(Enum):
    INITIALIZING = "Initializing LLM"
    INITIALIZED = "LLM initialized"
    WAITING = "Waiting for input"
    EXTRACTING = "Extracting prompts"
    PROMPTS_EXTRACTED = "Prompts extracted"
    PROMPTS_QUEUED = "Prompts queued"

    MEMORY_CLEARED = "Memory cleared"
    ERROR = "Error"

class ExtractorCommCommand(Enum):
    QA_INPUT = "QA input"


def create_communicator(enum, **kwargs):
    communicator = {}
    if isinstance(enum, GeneratorStatus) or isinstance(enum, ExtractoStatus):
        communicator = {"status": enum}  # Note the use of enum.value to get the string representation
        communicator.update(kwargs)
    elif isinstance(enum, ExtractorCommCommand):
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

def clear_memory_space_from_cache(extractor_communication_pipe, audio_cache, memory_space_index):
    cache.clear_memory_space(audio_cache, memory_space_index)
    extractor_communication_pipe.send(create_communicator(ExtractoStatus.MEMORY_CLEARED))

def extract_prompts(extractor_communication_pipe, llm, qa):
    extractor_communication_pipe.send(create_communicator(ExtractoStatus.EXTRACTING))
    prompt_list = llm.extract_prompts(qa)
    extractor_communication_pipe.send(create_communicator(ExtractoStatus.PROMPTS_EXTRACTED))
    return prompt_list

def block_generator(generator_blocked_boolean):
    generator_blocked_boolean.value = True

def unblock_generator(generator_blocked_boolean):
    generator_blocked_boolean.value = False


def queue_prompts(extractor_communication_pipe, prompt_queue, llm_settings, memory_space_index, prompts):
    pq.add_prompts_to_queue_bulk(prompt_queue, prompts, memory_space_index, llm_settings["number_sound_events"], llm_settings["number_prompts"])
    extractor_communication_pipe.send(create_communicator(ExtractoStatus.PROMPTS_QUEUED))

def extractor(extractor_communication_pipe, generator__communication_pipe, generator_blocked_boolean, audio_cache, prompt_queue, llm_settings, api_key):
    extractor_communication_pipe.send(create_communicator(ExtractoStatus.INITIALIZING))

    llm = LLMac.LLMApiConnector(api_key, **llm_settings)
    print(create_communicator(ExtractoStatus.INITIALIZED))
    wait_for_status(generator__communication_pipe, GeneratorStatus.INITIALIZED)

    while True:
        extractor_communication_pipe.send(create_communicator(ExtractoStatus.WAITING))
        msg = extractor_communication_pipe.recv()
        if msg["command"] == ExtractorCommCommand.QA_INPUT:
            memory_space_index, qa = msg["memory_space_index"], msg["qa"]
            try:
                block_generator(generator_blocked_boolean)
                wait_for_status(generator__communication_pipe, GeneratorStatus.BLOCKED)
                print("blocked generator")
                clear_memory_space_from_queue(prompt_queue, memory_space_index)
                print("cleared memory")
                unblock_generator(generator_blocked_boolean)
                wait_for_status(generator__communication_pipe, GeneratorStatus.UNBLOCKED)
                print("unblocked generator")
                prompts = extract_prompts(extractor_communication_pipe,llm,qa)
                block_generator(generator_blocked_boolean)
                wait_for_status(generator__communication_pipe, GeneratorStatus.BLOCKED)
                print("blocked generator")
                queue_prompts(extractor_communication_pipe, prompt_queue, llm_settings, memory_space_index, prompts)
                # stop playback
                clear_memory_space_from_cache(extractor_communication_pipe, audio_cache, memory_space_index)
                unblock_generator(generator_blocked_boolean)
                wait_for_status(generator__communication_pipe, GeneratorStatus.UNBLOCKED)
                print("unblocked generator")
            except Exception as e:
                print(e)
                extractor_communication_pipe.send(create_communicator(ExtractoStatus.ERROR))

def pop_prompt(prompt_queue):
    memory_space_index, sound_event_index, prompt_index, prompt = pq.pop_random_element(prompt_queue)
    return memory_space_index, sound_event_index, prompt_index, prompt

def generate(audio_pipe, parameters, prompt):
    model_parameters = {"prompt": prompt, **parameters}
    audio = audioldm2.text2audio(audio_pipe, model_parameters)
    return audio

def cache_audio(audio_cache, memory_space_index, sound_event_index, prompt_index, audio):
    cache.put_audio_array_into_cache(audio_cache, memory_space_index, sound_event_index, prompt_index, audio)

def generator(communication_pipe, generator_blocked_boolean, model_path, device, parameters, audio_cache, prompt_queue, critical_mass=10):
    print(create_communicator(GeneratorStatus.INITIALIZING))
    audio_pipe = audioldm2.setup_pipeline(model_path, device)
    communication_pipe.send(create_communicator(GeneratorStatus.INITIALIZED))

    while True:
        if generator_blocked_boolean.value:
            communication_pipe.send(create_communicator(GeneratorStatus.BLOCKED))
            time.sleep(1)
            #continue
        else: 
            communication_pipe.send(create_communicator(GeneratorStatus.UNBLOCKED))
            try: 
                try:
                    memory_space_index, sound_event_index, prompt_index, prompt = pop_prompt(prompt_queue)
                except ValueError:
                    time.sleep(1)
                    continue
                if prompt:
                    print(create_communicator(GeneratorStatus.GENERATING, memory_space_index=memory_space_index, sound_event_index=sound_event_index, prompt_index=prompt_index, prompt=prompt))
                    audio = generate(audio_pipe, parameters, prompt)
                    cache_audio(audio_cache, memory_space_index, sound_event_index, prompt_index, audio)
                    print(create_communicator(GeneratorStatus.CACHED, memory_space_index=memory_space_index, sound_event_index=sound_event_index, prompt_index=prompt_index))
                    print(len(prompt_queue))
                
            except Exception as e:
                print(e)
                time.sleep(1)


class ParallelAudioGenerator:

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
        self.generator_parent_channel, self.generator_child_channel = mp.Pipe(duplex=True)
        self.extractor_parent_channel, self.extractor_child_channel = mp.Pipe(duplex=True)

        self.extraction_process = None
        self.generator_process = None
        self.playback_processes = []

        self.model_path = str(model_path / audio_model_settings.pop("model"))
        self.device = audio_model_settings.pop("device")
        self.parameters = audio_model_settings

    def get_generator_channel(self):
        return self.generator_parent_channel

    def get_extractor_channel(self):
        return self.extractor_parent_channel

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

    def init_generation_process(self):
        self.generator_process = mp.Process(target=generator, args=(
            self.generator_child_channel, self.generator_blocked , self.model_path, self.device, self.parameters, self.audio_cache, self.prompt_queue))
        self.generator_process.start()

    def init_extraction_process(self):
        self.extraction_process = mp.Process(target=extractor, args=(
            self.extractor_child_channel, self.generator_parent_channel, self.generator_blocked ,self.audio_cache, self.prompt_queue, self.llm_settings, self.api_key))
        self.extraction_process.start()
