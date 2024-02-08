import random


def initialize_prompt_queue(manger):
    queue = manger.list()
    return queue

def clear_memory_space_from_queue(queue, memory_space_index):
    if queue is None:
        raise ValueError("queue is None")
    if memory_space_index is None:
        raise ValueError("memory_space_index is None")
    # Use a list comprehension to filter out the items to remove
    queue[:] = [prompt for prompt in queue if not prompt.startswith(str(memory_space_index))]

def add_prompts_to_queue_bulk(queue, prompts, memory_space_index, number_sound_events, number_prompts):
    if queue is None:
        raise ValueError("queue is None")
    if prompts is None:
        raise ValueError("prompts is None")
    if memory_space_index is None:
        raise ValueError("memory_space_index is None")
    if number_sound_events is None:
        raise ValueError("number_sound_events is None")
    if number_prompts is None:
        raise ValueError("number_prompts is None")

    if len(prompts) < number_sound_events:
        print("generated sound events are less then specified")
    if len(prompts) > number_sound_events:
        prompts = prompts[:number_sound_events]
    for sound_event_index in range(len(prompts)):
        if len(prompts[sound_event_index]) < number_prompts:
            print("generated prompts are less then specified")
        if len(prompts[sound_event_index]) > number_prompts:
            prompts[sound_event_index] = prompts[sound_event_index][:number_prompts]
        for prompt_index in range(len(prompts[sound_event_index])):
            add_prompt_to_queue(queue, prompts[sound_event_index][prompt_index], memory_space_index, sound_event_index, prompt_index)



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
    return int(memory_space_index), int(sound_event_index), int(prompt_index), prompt


def prompt_queue_to_string(queue):
    if queue is None:
        return "queue is None"
    if len(queue) == 0:
        return "queue is empty"
    string = ""
    for prompt in queue:
        string += prompt + "\n"
    return string
