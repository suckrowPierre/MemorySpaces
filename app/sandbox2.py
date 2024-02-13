import multiprocessing
import time
import random
from pyo import *

def process1():
    s = Server(sr=44100, nchnls=4, buffersize=512, duplex=0)
    s.deactivateMidi()
    s.setOutputDevice(0)
    s.boot().start()
    time.sleep(1)
    sine1 = Noise(mul=0.1).out(chnl=0)
    sine2 = Sine(freq=180, mul=0.1).out(chnl=0)

    time.sleep(25)

def process2():
    time.sleep(500)
    print("process2")

def process3():
    time.sleep(500)
    print("process3")

def process4():
    time.sleep(500)
    print("process4")




def main():
    p2 = multiprocessing.Process(target=process2)
    p2.start()
    p3 = multiprocessing.Process(target=process3)
    p3.start()
    p4 = multiprocessing.Process(target=process4)
    p4.start()
    p1 = multiprocessing.Process(target=process1)
    p1.start()
    time.sleep(50)
    




if __name__ == "__main__":
    main()
