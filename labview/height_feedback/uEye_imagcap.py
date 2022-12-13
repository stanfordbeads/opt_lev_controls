from pypyueye import Camera, FrameThread, SaveThread, RecordThread, \
    PyuEyeQtApp, PyuEyeQtView, UselessThread, CircleDetector
from pyueye import ueye
import matplotlib.pyplot as plt
import time
import numpy as np
import os
from skimage.registration import phase_cross_correlation as pcc
from skimage.io import imread as imread

import imageio as iio
from skimage import filters
from skimage.color import rgb2gray  # only needed for incorrectly saved images
from skimage.measure import regionprops
#path=C:\Linux\Gravity\py3\heightfb_rd"

def take_img(filename):
    with Camera(device_id=0, buffer_count=10) as cam:

        #======================================================================
        # Camera settings
        #======================================================================
        cam.set_colormode(ueye.IS_CM_MONO8)
        cam.set_aoi(0, 0, 800, 400)
        #print(f'Pixelclock: {cam.get_pixelclock()}')
        cam.set_exposure_auto(0)
        cam.set_fps(1)
        cam.set_exposure(0.00005)
        cam.set_pixelclock(25)

        # #======================================================================
        # # Save an image
        # #======================================================================
        # # Create a thread to save just one image
        if (cam.get_exposure() < 1):
            #print(cam.get_exposure())
            #print(cam.get_pixelclock())
            thread = SaveThread(cam, path=filename)
            thread.start()
            # Wait for the thread to end
            thread.join()
            #thread.stop()
            #data = cam.capture_image()
            #np.save(r"C:\Users\afieguth\Desktop\testimg\test%d.npy" %run ,data)
        else:
            print(f"Sir or Madam, I am not happy with the exposure of {str(cam.get_exposure)}" )
    return

def get_height_pcc(path, run):
    shift = [0,0]
    folder = "run" 
    dest = os.path.join(path,folder)
    if ((run == 0) and (os.path.isdir(dest) == False)):
        os.mkdir(dest)
        suffix = f"image_test_{run}.bmp"
        filename = os.path.join(dest, suffix)
        take_img(filename)
    else:    
        suffix = f"image_test_{run}.bmp"
        zeroth_image = imread(os.path.join(dest, "image_test_0.bmp"), as_gray=True)
        filename = os.path.join(dest, suffix)
        take_img(filename)
        image = imread(filename, as_gray=True)
        shift, _, _ = pcc(zeroth_image,image, upsample_factor=200)

    return shift[0]#+height  74-center_of_mass[0]  return height


def get_height_pcc_no_save(path,run):
    shift=[0,0]
    folder="run" 
    dest = os.path.join(path,folder)
    if((run==0) and (os.path.isdir(dest)==False)):
        os.mkdir(dest)
        suffix = "image_test_%d.bmp" %run
        filename=os.path.join(dest,suffix)
        take_img(filename)
    else:    
        suffix = "image_test_1.bmp"
        zeroth_image=imread(os.path.join(dest,"image_test_0.bmp"), as_gray=True)
        filename=os.path.join(dest,suffix)
        take_img(filename)
        image=imread(filename,as_gray=True)

        ## pcc algorithm
        shift,_,_ = pcc(zeroth_image,image,upsample_factor=200)

    return shift[0]#+height    return height

def get_saved_height(zeroth_dest, dest):#path,run):
    #folder="run"
    #suffix = "image_test_%d.bmp" %run
    #dest = os.path.join(path,folder) 
    
    zeroth_image=imread(zeroth_dest)#os.path.join(dest,"image_test_0.bmp"), as_gray=True)
    filename=dest#os.path.join(dest,suffix)
    image=imread(filename,as_gray=True)
    shift,_,_ = pcc(zeroth_image,image,upsample_factor=100)    
    
    return shift[0]
'''
    time_info=[]

        for i in range(3600):
            time_info.append(time.time())
            suffix = "image_test_%d.bmp" %i
            filename=os.path.join(dest,suffix)
            print(filename)
            take_img(filename=filename)
            time.sleep(10)
            #print(time_info)
            timefile_dest = os.path.join(dest,"timeinfo_run%d.npy" %j)
            np.save(timefile_dest,time_info)
    else: continue
'''
