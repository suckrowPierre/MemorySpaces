from enum import Enum

class CacheStructure(Enum):
    DATA = "data"

def validate_cache_entry(cache, memory_space_index, sound_event_index, prompt_index):
    if memory_space_index >= len(cache[CacheStructure.DATA]):
        raise ValueError("memory space index [" + str(memory_space_index) + "] out of range")
    if sound_event_index >= len(cache[CacheStructure.DATA][memory_space_index]):
        raise ValueError("sound event index [" + str(sound_event_index) + "] out of range")
    if prompt_index >= len(cache[CacheStructure.DATA][memory_space_index][sound_event_index]):
        raise ValueError("prompt index [" + str(prompt_index) + "] out of range")

def initialize_cache(manager, number_of_memory_spaces, number_soundevents, number_prompts):
    # Initialize the cache with specified number of memory spaces.
    cache = manager.dict()
    cache[CacheStructure.DATA] = manager.list(range(number_of_memory_spaces))
    for i in range(number_of_memory_spaces):
        cache[CacheStructure.DATA][i] = manager.list(range(number_soundevents))
        for j in range(number_soundevents):
            cache[CacheStructure.DATA][i][j] = manager.list(range(number_prompts))
            for k in range(number_prompts):
                cache[CacheStructure.DATA][i][j][k] = manager.list()
    return cache

def put_audio_array_into_cache(cache, memory_space_index, sound_event_index, prompt_index, audio_data):
    if (len(audio_data) == 0):
        raise ValueError("audio_data is empty")
    validate_cache_entry(cache, memory_space_index,sound_event_index, prompt_index)
    cache[CacheStructure.DATA][memory_space_index][sound_event_index][prompt_index].extend(
        audio_data.tolist())

def get_audio_from_cache(cache, memory_space_index, sound_event_index, prompt_index):
    validate_cache_entry(cache, memory_space_index,sound_event_index, prompt_index)
    audio = cache[CacheStructure.DATA][memory_space_index][sound_event_index][prompt_index]
    return audio

def clear_prompt(cache, memory_space_index, sound_event_index, prompt_index):
    if prompt_index >= len(cache[CacheStructure.DATA][memory_space_index][sound_event_index]):
        raise ValueError("prompt index [" + str(prompt_index) + "] out of range")
    cache[CacheStructure.DATA][memory_space_index][sound_event_index][prompt_index][:] = []


def clear_sound_event(cache, memory_space_index, sound_event_index):
    if sound_event_index >= len(cache[CacheStructure.DATA][memory_space_index]):
        raise ValueError("sound event index [" + str(sound_event_index) + "] out of range")
    for prompt in range(len(cache[CacheStructure.DATA][memory_space_index][sound_event_index])):
        clear_prompt(cache, memory_space_index, sound_event_index, prompt)

def clear_memory_space(cache, memory_space_index):
    if memory_space_index >= len(cache[CacheStructure.DATA]):
        raise ValueError("memory space index [" + str(memory_space_index) + "] out of range")
    for sound_event_index in range(len(cache[CacheStructure.DATA][memory_space_index])):
        clear_sound_event(cache, memory_space_index, sound_event_index)

def cache_to_string(cache):
    if len(cache[CacheStructure.DATA]) == 0:
        return "Cache is empty"
    string = ""
    for i in range(len(cache[CacheStructure.DATA])):
        string += f"Memory space {i}: \n"
        for j in range(len(cache[CacheStructure.DATA][i])):
            string += f"    Sound event {j}: \n"
            for k in range(len(cache[CacheStructure.DATA][i][j])):
                string += f"        Prompt {k}: {cache[CacheStructure.DATA][i][j][k]}\n"
    return string

def cache_status_to_string(cache):
    if len(cache[CacheStructure.DATA]) == 0:
        return "Cache is empty"
    string = ""
    for i in range(len(cache[CacheStructure.DATA])):
        string += f"Memory space {i}: \n"
        for j in range(len(cache[CacheStructure.DATA][i])):
            string += f"    Sound event {j}: \n"
            for k in range(len(cache[CacheStructure.DATA][i][j])):
                if len(cache[CacheStructure.DATA][i][j][k]) == 0:
                    string += f"        Prompt {k}: empty\n"
                else:
                    string += f"        Prompt {k}: AUDIO\n"
    return string

def cache_status_to_json(cache):
    if len(cache[CacheStructure.DATA]) == 0:
        return {"cache": "empty"}
    json_output = {}
    for i in range(len(cache[CacheStructure.DATA])):
        json_output[f"memory_space_{i}"] = {}
        for j in range(len(cache[CacheStructure.DATA][i])):
            json_output[f"memory_space_{i}"][f"sound_event_{j}"] = {}
            for k in range(len(cache[CacheStructure.DATA][i][j])):
                if len(cache[CacheStructure.DATA][i][j][k]) == 0:
                    json_output[f"memory_space_{i}"][f"sound_event_{j}"][f"prompt_{k}"] = "empty"
                else:
                    json_output[f"memory_space_{i}"][f"sound_event_{j}"][f"prompt_{k}"] = "AUDIO"
    return json_output