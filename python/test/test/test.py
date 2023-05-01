from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout, \
    QVBoxLayout, QLineEdit, QCheckBox, QFormLayout
import numpy as np
from nidaqmx.task import Task, AcquisitionType  
from nidaqmx.constants import TerminalConfiguration, LineGrouping
import warnings
from nidaqmx.errors import DaqWarning, DaqError
from scipy import signal
import matplotlib.pyplot as plt
import sys 
from vimba import *
#from pymba import Vimba

# config devices/inputs
TTL1 ="PXI1Slot4/ao2"
TTL2 = "PXI1Slot4/ao3"
# group channels and create dictionaries//ordering matters because they are added (.add_ai chan()) in this order 
aochannels={'camtrigger': TTL1, 'sweeptrigger': TTL2}

samplingrate=50000 # sampling rate in 1/s

def configTriggers(pulsewidth, totalT, delay):
    '''
    config two TTLs w/ delay 
    '''

    #pulsewidth = 0.001 # 1 ms pulse width
    #totalT=1 # total period =1s
    amp =5 # TTL amp=5V
    tpulse1 = np.linspace(0, pulsewidth, round(pulsewidth*samplingrate),endpoint=False) # time array for a single pulse--pulse width
    tzeros1 =  np.linspace(pulsewidth, totalT, round((totalT-pulsewidth)*samplingrate), endpoint=True)
    waveform1 = np.hstack((amp*signal.square(2 * np.pi /(pulsewidth*2) * tpulse1-np.pi/4)/2+amp/2, np.zeros(len(tzeros1) )))

    #delay=0.3 # delay between pulses [s]

    tzeros2a =  np.linspace(0, delay, round(delay*samplingrate),endpoint=False)
    tpulse2 = np.linspace(delay, delay+pulsewidth, round(pulsewidth*samplingrate), endpoint=True) # time array for a single pulse--pulse width
    tzeros2 =  np.linspace(delay+pulsewidth, totalT, round((totalT-pulsewidth-delay)*samplingrate), endpoint=False)
    waveform2 = np.hstack((np.zeros(len(tzeros2a)), amp*signal.square(2 * np.pi /(pulsewidth*2) * tpulse2-np.pi/4)/2+amp/2, \
                       np.zeros(len(tzeros2))))
    return waveform1, waveform2
## plot TTLs
#plt.plot(np.hstack((tpulse1,tzeros1)), waveform1)
#plt.plot(np.hstack((tzeros2a, tpulse2,tzeros2)), waveform2)
#plt.legend(['sweep', 'camera'])
#plt.xlabel('time [s]')
#plt.ylabel('trigger [V]')
#plt.ylim(-.1, 5.1)
#plt.show()

with Task() as task:
    # https://github.com/ni/nidaqmx-python/blob/master/examples/ao_voltage_hw_timed.py
    
    task.ao_channels.add_ao_voltage_chan(TTL1, max_val = 5, min_val =0)
    task.ao_channels.add_ao_voltage_chan(TTL2, max_val = 5, min_val =0)

    task.timing.cfg_samp_clk_timing(samplingrate)
    pulsewidth = 0.001 # 1 ms pulse width
    totalT=1 # total period =1s
    delay=0.3 # delay between pulses [s]

    #t=np.linspace(0, 1, samplingrate*100)
    #waveform1 = (signal.square(2*np.pi*300*t+2*np.pi/3, duty=0.5)+1)*5/2
    #waveform2 = (signal.square(2*np.pi*300*t, duty=0.5)+1)*5/2
    #waveform=[0,0,0,0, 5, 5, 5, 0, 0, 0, 0]

    waveform1, waveform2=configTriggers(pulsewidth, totalT, delay)
    t = np.linspace(0, totalT, round(totalT*samplingrate),endpoint=False)
     
    waveform2ch = np.vstack((waveform1, waveform2))
    print(np.shape(waveform2ch))

    print("2 Channel N Samples Write: ")
    print(task.write(waveform2ch, auto_start=True))

    task.wait_until_done()
    task.stop()

    plt.plot(t, waveform1)
    plt.plot(t, waveform2)

    plt.legend(['sweep', 'camera'])
    plt.xlabel('time [s]')
    plt.ylabel('trigger [V]')
    plt.ylim(-.1, 5.1)

    plt.show()


def print_camera(cam: Camera):
    print('/// Camera Name   : {}'.format(cam.get_name()))
    print('/// Model Name    : {}'.format(cam.get_model()))
    print('/// Camera ID     : {}'.format(cam.get_id()))
    print('/// Serial Number : {}'.format(cam.get_serial()))
    print('/// Interface ID  : {}\n'.format(cam.get_interface_id()))

    
def get_camera(camera_id):
    with Vimba.get_instance() as vimba:
        if camera_id:
            try:
                return vimba.get_camera_by_id(camera_id)

            except VimbaCameraError:
                sys.exit('Failed to access Camera \'{}\'. Abort.'.format(camera_id))

        else:
            cams = vimba.get_all_cameras()
            if not cams:
                sys.exit('No Cameras accessible. Abort.')

            return cams[0]

#with Vimba.get_instance() as vimba:
#    cams = vimba.get_all_cameras()

#    print('Cameras found: {}'.format(len(cams)))
  

#    for cam1 in cams:
#        print_camera(cam1)
       
#     #print(cams[0].get_id()) 
    
#    camera_id = cams[0].get_id()

#    with vimba.get_camera_by_id(camera_id) as cam:
#        # Acquire 10 frame with a custom timeout (default is 2000ms) per frame acquisition.
#        for frame in cam.get_frame_generator(limit=10, timeout_ms=3000):
#            print('Got {}'.format(frame), flush=True)
