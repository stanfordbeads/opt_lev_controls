from telnetlib import Telnet
import sys
import os
import parseRGA

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
directory = 'C:\Users\\beads\Documents\MKS Save'#sys.argv[10]


#Read until the \r\r is reached, indicating end-of-response. RGA Manual specifies the end-of-response byte string as being \r\r for most if not all responses. 
def read():
    return tn.read_until(b'\r\r')

def save_file(scan_num):
    f.write(line + '\n')

def file_exists(fullpath,j):
    #Changes j so that file is not overwritten.  
    while os.path.exists(fullpath) == True:
    	j += 1
    	fullpath = os.path.join(directory,MeasName+ r'_{}'.format(j))
    return fullpath

def scan(f):
    tn.write(b'ScanStart ' + NumScans.encode('ascii') + b'\r\n') 
    print(read())    
    
    try:
    	while True:
    	    #Read until the end of each response line. Timeout is in seconds. If timeout is reached, line returns b''.
    	    line = tn.read_until(b'\n',timeout = 2)
    	    print(line)
    	    #if save == True:
    	    f.write(line.decode('ascii') +'\n') #Print to file
    	     
    	    #Stop at the given end mass. If this not specified, the program still runs but it scans past EM and stalls.
    	    if b'MassReading ' + EM.encode('ascii') in line:
    	        tn.write(b'ScanStop\r\n')
    	        tn.write(b'FilamentControl Off\r\n')
    	        #tn.write(b'Release\r\n')
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
#tn.write(b'FilamentControl On\r\n')
#print(read())

#Define counter for files with same MeasName base name
j = 0
fullpath = os.path.join(directory,MeasName+ r'_{}'.format(j))

for i in range(int(NumScans)):
    fullpath = file_exists(fullpath, j)
    
    masses = []
    part_press = []
    
    with open(fullpath,'w') as f:
    	tn.write(b'ScanAdd ' + MeasName.encode('ascii')+b'\r\n')
    	print(read())	
    
    	scan(f)

tn.write(b'Release\r\n')

tn.close()
