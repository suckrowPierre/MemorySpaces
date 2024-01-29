from enum import Enum

class CacheStructure(Enum):
    DATA = "data"
    CONSTRAINTS = "constraints"
    NUMBER_OF_MEMORY_SPACES = "number_of_memory_spaces"
    NUMBER_SOUNDEVENTS = "number_soundevents"
    NUMBER_PROMPTS = "number_prompts"

def get_number_of_memory_spaces_constraint(cache):
    return cache[CacheStructure.CONSTRAINTS][CacheStructure.NUMBER_OF_MEMORY_SPACES]

def get_number_of_soundevents_constraint(cache):
    return cache[CacheStructure.CONSTRAINTS][CacheStructure.NUMBER_SOUNDEVENTS]

def get_number_of_prompts_constraint(cache):
    return cache[CacheStructure.CONSTRAINTS][CacheStructure.NUMBER_PROMPTS]

def is_cache_empty(cache):
    return cache[CacheStructure.DATA] is None

def is_sound_event_in_memory_space(cache, memory_space, sound_event):
    return sound_event in cache[CacheStructure.DATA][memory_space]

def get_len_sound_event(cache, memory_space, sound_event):
    validate_if_cache_not_empty(cache)
    #Get the length of a sound event in a memory space.
    return len(cache[CacheStructure.DATA][memory_space].get(sound_event, []))

def validate_if_cache_not_empty(cache):
    if is_cache_empty(cache):
        raise ValueError("cache is empty")

def validate_if_memory_space_exists(cache, memory_space):
    if memory_space not in cache[CacheStructure.DATA] or memory_space >= get_number_of_memory_spaces_constraint(cache):
        raise ValueError("memory space does not exist")
    
def validate_if_sound_event_exists(cache, memory_space, sound_event):
    if sound_event not in cache[CacheStructure.DATA][memory_space]:
        raise ValueError("sound event does not exist")
    
def validate_if_memory_space_full(cache, memory_space):
    if len(cache[CacheStructure.DATA][memory_space]) >= get_number_of_soundevents_constraint(cache):
        raise ValueError("memory space is full")

def validate_if_memory_has_not_sound_event_or_full(cache, memory_space, sound_event):
    if (not is_sound_event_in_memory_space(cache, memory_space, sound_event)) and len(cache[CacheStructure.DATA][memory_space]) >= get_number_of_soundevents_constraint(cache):
        raise ValueError("memory space is full")

def validate_if_sound_event_full(cache, memory_space, sound_event):
    if get_len_sound_event(cache, memory_space, sound_event) >= get_number_of_prompts_constraint(cache):
        raise ValueError("sound event is full")


def _initialize_cache(manager, number_of_memory_spaces, number_soundevents, number_prompts):
    # Initialize the cache with specified number of memory spaces.
    cache = manager.dict()
    cache[CacheStructure.CONSTRAINTS] = manager.dict()
    cache[CacheStructure.CONSTRAINTS][CacheStructure.NUMBER_OF_MEMORY_SPACES] = number_of_memory_spaces
    cache[CacheStructure.CONSTRAINTS][CacheStructure.NUMBER_SOUNDEVENTS] = number_soundevents
    cache[CacheStructure.CONSTRAINTS][CacheStructure.NUMBER_PROMPTS] = number_prompts
    cache[CacheStructure.DATA] = manager.dict()
    for i in range(number_of_memory_spaces):
        cache[CacheStructure.DATA][i] = manager.dict()
    return cache


def clear_memory_space(cache, manager, memory_space):
    #Clear the specified memory space in the cache.
    validate_if_cache_not_empty(cache)
    validate_if_memory_space_exists(cache, memory_space)
    del cache[CacheStructure.DATA][memory_space]
    cache[CacheStructure.DATA][memory_space] = manager.dict()

    
def append_to_memory_space(cache, manager, memory_space, sound_event, audio_data):
    #Append data to a specified memory space and sound event in the cache
    validate_if_cache_not_empty(cache)
    validate_if_memory_space_exists(cache, memory_space)
    validate_if_memory_has_not_sound_event_or_full(cache, memory_space, sound_event)
    validate_if_sound_event_full(cache, memory_space, sound_event)
    if sound_event not in cache[CacheStructure.DATA][memory_space]:
        cache[CacheStructure.DATA][memory_space][sound_event] = manager.list()
    cache[CacheStructure.DATA][memory_space][sound_event].append(audio_data.tolist())   # Might be point of failure

def get_audio_from_cache(cache, memory_space, sound_event, index):
    #Retrieve audio data from cache
    validate_if_cache_not_empty(cache)
    validate_if_memory_space_exists(cache, memory_space)
    validate_if_sound_event_exists(cache, memory_space, sound_event)
    audios = cache[CacheStructure.DATA][memory_space].get(sound_event, [])
    return audios[index] if index < len(audios) else None

def cache_to_string(cache):
    #Print the contents of the cache."""
    validate_if_cache_not_empty(cache)
    string = ""
    for memory_space, events in cache[CacheStructure.DATA].items():
        string += (f"memory_space: {memory_space}\n")
        if not events:
            string +=("--empty\n")
            continue
        for sound_event, audios in events.items():
            string +=(f"--sound_event: {sound_event}\n")
            if not audios:
                string += ("----empty\n")
                continue
            for audio in audios:
                string +=(f"----audio: {audio}\n")
    return string