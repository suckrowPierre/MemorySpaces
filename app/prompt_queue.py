import random


def initialize_prompt_queue(manger):
    queue = manger.list()
    return queue


def add_prompt_to_queue(queue, prompt, memory_space_index, sound_event_index, prompt_index):
    if queue is None:
        raise ValueError("queue is None")
    if prompt is None:
        raise ValueError("prompt is None")
    if memory_space_index is None:
        raise ValueError("memory_space_index is None")
    if sound_event_index is None:
        raise ValueError("sound_event_index is None")
    if prompt_index is None:
        raise ValueError("prompt_index is None")

    prefix = str(memory_space_index) + "_" + str(sound_event_index) + "_" + str(prompt_index) + "_"
    queue.append(prefix + prompt)


def pop_random_element(queue):
    if queue is None:
        raise ValueError("queue is None")
    if len(queue) == 0:
        raise ValueError("queue is empty")
    random_index = random.randrange(len(queue))
    queue[random_index], queue[-1] = queue[-1], queue[random_index]
    prompt_with_prefix = queue.pop()
    memory_space_index, sound_event_index, prompt_index, prompt = prompt_with_prefix.split("_")
    return memory_space_index, sound_event_index, prompt_index, prompt


def prompt_queue_to_string(queue):
    if queue is None:
        return "queue is None"
    if len(queue) == 0:
        return "queue is empty"
    string = ""
    for prompt in queue:
        string += prompt + "\n"
    return string
