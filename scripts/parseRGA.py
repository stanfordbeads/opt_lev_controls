import re
import numpy as np
import matplotlib.pyplot as plt

#Regex for checking if line contains mass. 'Mass' indicates that a line is a data point.
m = re.compile('Mass')

#Regex for extracting mass number and part. press.
mass = re.compile(r'\d+\.?\d+')
press = re.compile(r'\d+\.\d+\w[+-]\d+')

masses = []
part_press = []

def plot(x,y):
    plt.plot(x,y)
    plt.ylabel('Pressure [Torr]')
    plt.xlabel('Mass [amu]')
    plt.yscale('log')
    #plt.pause(0.001)
    #plt.draw()
    plt.show()

def getData(input_file):
    with open(input_file,'r') as f:
        for line in f:
            if m.search(line):
                found_mass = mass.search(line)
                found_press = press.search(line)
                masses.append(float(found_mass.group(0)))
                part_press.append(float(found_press.group(0)))
                 
    return masses, part_press

#masses, part_press = getData('test_2019_05_13')


