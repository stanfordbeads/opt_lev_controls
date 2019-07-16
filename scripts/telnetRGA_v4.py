from telnetlib import Telnet
import sys
import os
#from parseRGA import *
import matplotlib.pyplot as plt
import re
import numpy as np
import csv

RGA_IP = '171.64.56.202'

MeasName = sys.argv[1]  #Measurement name will be used as base of the save file
SM = sys.argv[2]        #start mass
EM = sys.argv[3]        #end mass
PPP = sys.argv[4]       #points per peak
Acc = sys.argv[5]       #accuracy
EGI = sys.argv[6]       #EGain Index
SI = sys.argv[7]        #Source Index
DI = sys.argv[8]        #Detector Index
NumScans = sys.argv[9]  
directory = sys.argv[10]#'C:\Users\Stanford1Beads\Documents\MKS_Save'
save_csv = True #sys.argv[11]
save_npy = False
plot = False #sys.argv[12]
filament_on = True

mass_regex = re.compile(r'\d+\.?\d+')
press_regex = re.compile(r'\d+\.\d+\w[+-]\d+')

def read():
    '''Read until the \r\r is reached, indicating end-of-response. RGA Manual specifies the end-of-response byte string as being \r\r for most if not all responses.'''
    return tn.read_until(b'\r\r')

def file_exists(path, j):
    '''Changes j so that file is not overwritten.'''
    while os.path.exists(path) == True:
    	j += 1
    	path = os.path.join(directory,MeasName + r'_scan' + r'_{}'.format(j))
    return path

def scan(f):
    '''Runs one scan as specified in ScanStart input. The scan is stop once the line output does not contain MassReading'''
    tn.write(b'ScanStart 1' + b'\r\n') 
    
    #Read first five lines that are returned after Scan Start command
    print(read())
    print(read())
    print(read())
    print(read())
    print(read())
 
    try:
        while True:
    	    #Read until the end of each response line. Timeout is in seconds. If timeout is reached, line returns b''.
    	    line = tn.read_until(b'\n',timeout = 2)
            #print(line)
            #As long as the RGA returns mass readings, keep appending readings to mass and pressure lists.
            if line.decode('ascii').find('MassReading') != -1:	
                mass.append(float(mass_regex.search(line).group(0)))
                pressure.append((1/133.322368)*float(press_regex.search(line).group(0))) #Convert Pa to Torr
                
            if plot:
                ax.clear()
                ax.set_ylabel('Pressure [Torr]')
                ax.set_xlabel('Mass [amu]')
                ax.set_yscale('log')
                ax.set_xlim(0,float(EM.decode('ascii')))
                ax.set_ylim(1E-9,1E-4)
                ax.plot(mass,pressure) 
                plt.pause(0.001)
                plt.draw()
            #if save_npy:

            if line.decode('ascii').find('MassReading') == -1:
                tn.write(b'ScanStop\r\n')
                print(read())
                break 
    	    
    #If the response stream stalls, just press CTRL+C and this except properly stops scan, turns off the filament, and releases control.
    except KeyboardInterrupt:
        tn.write(b'ScanStop\r\n') 
        tn.write(b'FilamentControl Off\r\n')
        tn.write(b'Release\r\n')
        pass


#Connect to RGA. Telnet(IP,Port)
tn = Telnet(RGA_IP,10014)#,timeout=1)
#tn.set_debuglevel(2): This prints out the raw byte strings that come out of the RGA. Good for check \r and \n.
print(read())

#Gain control of the RGA
tn.write(b'Control "Process Eye" "MKS Spectra"\r\n')
print(read())

#Add an analog scan. AddAnalog MeasurementName StartMass EndMass PointsPerPeak Accuracy EGainIndex SourceIndex DetectorIndex
tn.write(b'AddAnalog ' + MeasName.encode('ascii')+b' '+SM.encode('ascii')+b' '+EM.encode('ascii')\
            +b' '+PPP.encode('ascii')+b' '+Acc.encode('ascii')+b' '+EGI.encode('ascii')+b' '+SI.encode('ascii')\
            +b' '+DI.encode('ascii')+b'\r\n')
print(read())

#Turn on the filament
if filament_on:
    tn.write(b'FilamentControl On\r\n')
    print(read())
    print(read())

#Define counter for files with same MeasName base name
j = 0
fullpath = os.path.join(r'{}'.format(directory),r'{}'.format(MeasName) + r'_scan' + r'_{}'.format(j))
fullpath_csv = os.path.join(r'{}'.format(directory),r'{}'.format(MeasName) + r'_scan' + r'_{}'.format(j)) 
print(fullpath,directory)

#Perform as many scans as specified by NumScans. Will save and plot if both corresponding variables are True.
mass = []
pressure = []

if plot:
    plt.ion()
    fig, ax = plt.subplots(1,1)
    line1, = ax.plot([],[])
    ax.set_ylabel('Pressure [Torr]')
    ax.set_xlabel('Mass [amu]')
    
for i in range(int(NumScans)): 
    mass = []
    pressure = []

    if plot:
        plt.cla()
 
    if save_npy: 
        fullpath = file_exists(fullpath, i)

        with open(fullpath,'w') as f:
            tn.write(b'ScanAdd ' + MeasName.encode('ascii') + b'\r\n')
            print(read())	
             
            scan(f)
    else:
        tn.write(b'ScanAdd ' + MeasName.encode('ascii') + b'\r\n')
        print(read())

        scan('')
    if i == 0:
        mass_arr = np.empty_like([mass])
        mass_arr = np.delete(mass_arr,0,0)
        pressure_arr = np.empty_like([pressure])
        pressure_arr = np.delete(pressure_arr,0,0)
    
    mass_arr = np.append(mass_arr, [mass], axis=0)
    pressure_arr = np.append(pressure_arr, [pressure], axis=0)

    if save_csv:
        fullpath_csv = file_exists(fullpath_csv,j)
        current_file_path = os.path.join(r'{}'.format(directory),'current_filename.txt')
        #Write each scan to a csv file. Mass is first row and pressure is the second row.
        with open(fullpath_csv,'wb') as cfile:
            writer = csv.writer(cfile,delimiter=' ')
            writer.writerow(mass_arr[0])
            writer.writerow(pressure_arr[0])
        #Write the scans' file path to a txt file so that Labview can look for the last scan correctly
        with open(current_file_path,'w') as cfile1:
            cfile1.write(fullpath_csv) 
if save_npy:
    np.save(fullpath + '_masses.npy', mass_arr)
    np.save(fullpath + '_pressures.npy',pressure_arr)

tn.write(b'Release\r\n')
tn.write(b'FilamentControl Off')
print(read())
tn.close()
