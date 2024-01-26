from pyo import *
from multiprocessing import Process, Manager

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

def play_sine(out, freq, volume_multiply, out_put_device_index, **interface_settings):
    print("Playing sine on device: " + str(out) + " with freq: " + str(freq))
    sr, nchnls, buffersize, duplex = interface_settings.values()
    s = Server(sr=sr, nchnls=nchnls, buffersize=buffersize, duplex=duplex)
    s.setOutputDevice(out_put_device_index)
    s.boot()
    a = Sine(freq=freq, mul=volume_multiply).out(chnl=out)
    s.start()



class MultiOutsSineTest:

    def __init__(self, device_index, sr=44100, nchnls=8, buffersize=512, duplex=0):
        self.outs = []
        self.device_index = device_index
        self.sr = sr
        self.nchnls = nchnls
        self.buffersize = buffersize
        self.duplex = duplex
        self.manager = Manager()
        self.processes = []


    def add_sine(self, out, freq, volume_multiply):
        if out in self.outs:
            raise Exception("Out already in use")
        if out >= self.nchnls:
            raise Exception("Out out of range")
        if len(self.outs) >= self.nchnls:
            raise Exception("No more outs available")
        self.outs.append(out)
        self.processes.append(Process(target=play_sine, args=(out, freq, volume_multiply, self.device_index), kwargs={"sr": self.sr, "nchnls": self.nchnls, "buffersize": self.buffersize, "duplex": self.duplex}))
        self.processes[-1].start()

    def remove_sine(self, out):
        if out not in self.outs:
            raise Exception("Out not in use")
        self.processes[out].terminate()
        del self.processes[out]
        self.outs.remove(out)

    def shutdown(self):
        for process in self.processes:
            process.terminate()
        self.processes = []
        self.outs = []

    def __del__(self):
        self.shutdown()
        self.manager.shutdown()
        print("MultiOutsSineTest deleted")

    