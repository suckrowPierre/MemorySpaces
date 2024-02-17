import os
from dotenv import load_dotenv
import requests
from pyo import *
import time
import random
import multiprocessing as mp

load_dotenv()
DB_IP = os.getenv("DB_IP")
DB_PORT = os.getenv("DB_PORT")
URL = f"http://{DB_IP}:{DB_PORT}"


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


def get_len_memory_spaces():
    response = requests.get(f"{URL}/len_memory_spaces")
    if response.status_code == 200:
        return int(response.json()["len_memory_spaces"])
    return None


def get_random_audio(memory_space_id, sound_event_index):
    try:
        response = requests.get(f"{URL}/random_audio/{memory_space_id}/{sound_event_index}")
        if response.status_code == 200:
            audio = response.json()["audio_data"]
            prompt = response.json()["prompt"]
            return audio, prompt
    except Exception as e:
        print(e)
    return None, None


def get_number_sound_events():
    response = requests.get(f"{URL}/number_sound_events")
    if response.status_code == 200:
        return int(response.json()["number_sound_events"])
    return None


def playback_process(channel, device_index, memory_space_index, sound_event_index, lower_bound_interval_limit,
                     upper_bound_interval_limit, critical_mass):
    s = Server(sr=44100, nchnls=4, buffersize=512, duplex=0)
    s.deactivateMidi()
    s.setOutputDevice(device_index)
    s.boot().start()
    time.sleep(1)

    def play_audio(audio, channel, delay, sr=16000, amplitude=0.7):
        audio_list = list(audio)
        duration = len(audio_list) / sr
        table = DataTable(size=len(audio_list), chnls=1)
        table.replace(audio_list)
        table_read_freq = sr / float(len(audio_list))
        reader = TableRead(table, freq=table_read_freq, loop=False, mul=amplitude)
        reader.out(chnl=channel)
        delay = delay + duration
        time.sleep(delay)

    while True:
        audio_db, prompt = get_random_audio(memory_space_index, sound_event_index)
        if audio_db is None:
            time.sleep(1)
        else:
            print(f"Playing audio: {prompt}")
            delay_interval = random.randint(lower_bound_interval_limit, upper_bound_interval_limit)
            play_audio(audio_db, channel, delay_interval)
            time.sleep(0.1)


def sine_test_process(channel, device_index, freq, volume_multiply):
    s = Server(sr=48000, nchnls=3, buffersize=512, duplex=0)
    s.deactivateMidi()
    s.setOutputDevice(device_index)
    s.boot().start()
    time.sleep(1)
    sine = Sine(freq=freq, mul=volume_multiply).out(chnl=channel)
    while True:
        time.sleep(1)

def noise_test_process(channel, device_index, volume_multiply):
    s = Server(sr=48000, nchnls=3, buffersize=512, duplex=0)
    s.deactivateMidi()
    s.setOutputDevice(device_index)
    s.boot().start()
    time.sleep(1)
    noise = Noise(mul=volume_multiply).out(chnl=channel)
    while True:
        time.sleep(1)

def test():
    device = "Quantum 2626"
    device_list = get_out_devices()
    print(device_list)
    device_index = get_device_index(get_out_devices(), device)
    processes = []
    processes.append(mp.Process(target=sine_test_process, args=(0, device_index, 440, 0.1)))
    processes.append(mp.Process(target=noise_test_process, args=(1, device_index, 0.1)))
    processes.append(mp.Process(target=sine_test_process, args=(2, device_index, 880, 0.5)))
    for p in processes:
        p.start()
    for p in processes:
        p.join()
    print("Done")


def main():
    print(get_out_devices())
    device = "Quantum 2626"
    device_index = get_device_index(get_out_devices(), device)

    number_sound_events = get_number_sound_events()

    number_memory_spaces = get_len_memory_spaces()

    if number_memory_spaces is None:
        raise Exception("Could not get number of memory spaces")
    if number_sound_events is None:
        raise Exception("Could not get number of sound events")

    processes = []
    for i in range(number_memory_spaces):
        for j in range(number_sound_events):
            p = mp.Process(target=playback_process, args=(i, device_index, i, j, 1, 3, 2))
            p.start()
            processes.append(p)

    for p in processes:
        p.join()

    print("Done")




if __name__ == "__main__":
    #test()
    main()
