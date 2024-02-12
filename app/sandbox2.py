import audio_interface_helper
import time
import random
from pyo import *




def main():
    outdevices = audio_interface_helper.get_out_devices()
    device_index = audio_interface_helper.get_device_index(outdevices,"Quantum 2626")
    s = Server(sr=44100, nchnls=4, buffersize=512, duplex=0)
    s.setOutputDevice(device_index)
    s.boot()
    s.start()
    channel = 0


    #sine1 = Sine(freq=440, mul=0.001).out(chnl=channel)
    #sine2 = Sine(freq=220, mul=0.001).out(chnl=channel)
    sine3 = Sine(freq=180, mul=0.001).out(chnl=channel, dur=5)
    sine4 = Sine(freq=110, mul=0.001).out(chnl=channel, dur=10)
    # mix sines into one output
    #mix = Mix(sine1 + sine2 + sine3, voices=3).out(chnl=channel)

    time.sleep(10)





if __name__ == "__main__":
    main()
