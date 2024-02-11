from pyo import *
import time
import multiprocessing as mp
import numpy as np
from enum import Enum
import ctypes
import random
#import audioldm2
#import cache
#import LLM_api_connector as LLMac
#import prompt_queue as pq
from . import audioldm2
from . import cache
from . import LLM_api_connector as LLMac
from . import prompt_queue as pq
mp.set_start_method('spawn', force=True)

def get_out_devices():
    try:
        outs = pa_get_output_devices()
        if outs == []:
            raise Exception("No output devices found")
    except:
        raise Exception("oa_get_output_devices() failed")
    return outs


def get_device_index(devices, name):
    try:
        index = devices[1][devices[0].index(name)]
    except:
        raise Exception("Device not found")
    return index 

def get_devices_names(devices):
    return devices[0]

class AudioGenerationStatus(Enum):
    INITIALIZING = "Initializing audio pipeline"
    INITIALIZED = "Audio pipeline initialized"
    GENERATING = "Generating audio"
    GENERATED = "Audio generated"
    CACHED = "Audio cached"

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


def prompt_extraction_process(parallel_process_communication_pipe, audiogeneration_communication_pipe, generator_blocked_boolean, audio_cache, prompt_queue, llm_settings, api_key):
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
                
                # stop playback
                # TODO

                # clear audio cache and unblock generator
                clear_memory_space_from_cache(audio_cache, memory_space_index)
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

def cache_audio(audio_cache, memory_space_index, sound_event_index, prompt_index, audio):
    cache.put_audio_array_into_cache(audio_cache, memory_space_index, sound_event_index, prompt_index, audio)

def audio_generation_process(audio_generation_communication_pipe, generator_blocked_boolean, model_path, device, parameters, audio_cache, prompt_queue):
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
                    cache_audio(audio_cache, memory_space_index, sound_event_index, prompt_index, audio)
                    print(create_communicator(AudioGenerationStatus.CACHED, memory_space_index=memory_space_index, sound_event_index=sound_event_index, prompt_index=prompt_index))
                    print(len(prompt_queue))
                
            except Exception as e:
                print(e)
                time.sleep(1)


def sound_events_under_min_number_of_audio(available_audio, min_number_audio):
    for sound_event in available_audio:
        if len(sound_event) < min_number_audio:
            return True
    return False

def audio_playback_process(commonication_pipe, audio_cache, plackback_blocked, number_sound_events, memory_space_index, channel, amplitude, lower_bound_intervall_limit, upper_bound_intervall_limit, sr, device_index, critical_mass=2 ):
    
    s = Server(sr=44100, nchnls=1, buffersize=512, duplex=0)
    s.set_output_device(device_index)
    s.boot()
    s.start()
    mixer = Mixer(outs=1, chnls=number_sound_events)


    # play_head_information structure (playing, duration_in_sec, start_time, reader)
    play_heads = []
    for i in range(number_sound_events):
        mixer.setAmp(i, channel, amplitude)
        play_heads.append([False, 0, 0, None])

    
    while True:
        if plackback_blocked.value:
            commonication_pipe.send(create_communicator(PlaybackStatus.STOPPED, memory_space_index=memory_space_index))
            time.sleep(1)
            continue
        else:
            available_audio = cache.get_available_audio(audio_cache, memory_space_index)
            if sound_events_under_min_number_of_audio(available_audio, critical_mass):
                commonication_pipe.send(create_communicator(PlaybackStatus.STOPPED, memory_space_index=memory_space_index))
                time.sleep(1)
                continue
            else:
                commonication_pipe.send(create_communicator(PlaybackStatus.PLAYING, memory_space_index=memory_space_index))
                for i in range(number_sound_events):
                    if not play_heads[i][0]:
                        audio = cache.get_random_audio_from_available_audio(available_audio, i).tolist()
                        random_interval = random.randint(lower_bound_intervall_limit, upper_bound_intervall_limit)
                        duration = len(audio) / sr + random_interval
                        table = DataTable(size=len(audio), chnls=1)
                        table.replace(audio)
                        table_read_freq = sr / float(len(audio))
                        reader = TableRead(table, freq=table_read_freq, loop=False)
                        mixer.addInput(i, reader)
                        play_heads[i] = [True, duration, time.time(), reader]
                    else:
                        time.sleep(1)
                        if time.time() - play_heads[i][2] > play_heads[i][1]:
                            play_heads[i][3].stop()
                            mixer.delInput(i)
                            play_heads[i] = [False, 0, 0, None]




                        
            


            
            



   

class ParallelProcessor:

    def __init__(self, model_path, api_key, audio_settings, audio_model_settings, llm_settings):
        self.llm_settings = llm_settings
        self.api_key = api_key

        self.generator_blocked = mp.Value(ctypes.c_bool, False)
        self.playback_memory_space1_blocked = mp.Value(ctypes.c_bool, False)
        self.playback_memory_space2_blocked = mp.Value(ctypes.c_bool, False)
        self.playback_memory_space3_blocked = mp.Value(ctypes.c_bool, False)

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

        for i in range(len(self.channels)):
            self.init_playback_process(i, self.channels[i], 1, 5, 10, get_device_index(get_out_devices(), self.interface))

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

    def init_playback_process(self, memory_space_index, channel, amplitude, lower_bound_intervall_limit, upper_bound_intervall_limit, device_index):
        playback_process = mp.Process(target=audio_playback_process, args=(self.parallel_process_child_channel, self.audio_cache, self.playback_memory_space1_blocked, self.number_sound_events, memory_space_index, channel, amplitude, lower_bound_intervall_limit, upper_bound_intervall_limit, self.sr, device_index))
        playback_process.start()
        self.playback_processes.append(playback_process)
