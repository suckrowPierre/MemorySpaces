def _initialize_cache(manager, number_of_memory_spaces, number_soundevents, number_prompts):
    # Initialize the cache with specified number of memory spaces.
    cache = manager.dict()
    cache["constraints"] = manager.dict()
    cache["constraints"]["number_of_memory_spaces"] = number_of_memory_spaces
    cache["constraints"]["number_soundevents"] = number_soundevents
    cache["constraints"]["number_prompts"] = number_prompts
    cache["data"] = manager.dict()
    for i in range(number_of_memory_spaces):
        cache["data"][i] = manager.dict()
    return cache


def clear_memory_space(cache, manager, memory_space):
    #Clear the specified memory space in the cache.
    if cache["data"] is None:
        raise ValueError("cache is empty")
    if (memory_space >= cache["constraints"]["number_of_memory_spaces"]):
        raise ValueError("memory space does not exist")
    if memory_space in cache["data"]:
        del cache["data"][memory_space]
        cache["data"][memory_space] = manager.dict()
    else:
        raise ValueError("memory space does not exist")
    
def append_to_memory_space(cache, manager, memory_space, sound_event, audio_data):
    #Append data to a specified memory space and sound event in the cache
    if cache["data"] is None:
        raise ValueError("cache is empty")
    if (memory_space >= cache["constraints"]["number_of_memory_spaces"]):
        raise ValueError("memory space does not exist")
    if (cache["data"][memory_space] is None):
        raise ValueError("memory space does not exist")
    if len(cache["data"][memory_space]) >= cache["constraints"]["number_soundevents"]:
        raise ValueError("memory space is full")
    if get_len_sound_event(cache, memory_space, sound_event) >= cache["constraints"]["number_prompts"]:
        raise ValueError("sound event is full")
    if sound_event not in cache["data"][memory_space]:
        cache["data"][memory_space][sound_event] = manager.list()
    cache["data"][memory_space][sound_event].append(audio_data.tolist())   # Might be point of failure

def get_audio_from_cache(cache, memory_space, sound_event, index):
    #Retrieve audio data from cache
    if cache["data"] is None:
        raise ValueError("cache is empty")
    if memory_space not in cache["data"]:
        raise ValueError("memory space does not exist")
    if sound_event not in cache["data"][memory_space]:
        raise ValueError("sound event does not exist")
    audios = cache["data"][memory_space].get(sound_event, [])
    return audios[index] if index < len(audios) else None

def get_len_sound_event(cache, memory_space, sound_event):
    if cache["data"] is None:
        raise ValueError("cache is empty")
    #Get the length of a sound event in a memory space.
    return len(cache["data"][memory_space].get(sound_event, []))

