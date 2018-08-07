

import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as signal


Fsamp = 5000.
Npoints = 300000
drive_elec = 7
drive_voltage = 10

chirp_start = 1
chirp_length = 60
chirp_end = 1000

filname = r'C:\GitHub\opt_lev_controls\labview\DAQ_settings\chirp_elec7_1-1000Hz_60s.txt'


######################################


dt = 1. / Fsamp
t = np.linspace(0, (Npoints-1) * dt, Npoints)

Vchirp = drive_voltage * signal.chirp(t, chirp_start, chirp_length, \
                                      chirp_end, phi=-90)
Vsteady = drive_voltage * np.sin(2 * np.pi * chirp_end * (t-chirp_length))

drive_arr = (t <= chirp_length) * Vchirp #+ (t > 60) * Vsteady

plt.figure()
plt.plot(t, drive_arr)

plt.show()

out_arr = []
for ind in range(8):
    if ind == drive_elec:
        out_arr.append(drive_arr)
    else:
        out_arr.append(np.zeros(Npoints))

out_arr = np.array(out_arr)
#print out_arr.shape

#np.savetxt(r'C:\GitHub\opt_lev\labview\DAQ_settings\freq_comb_elec6_optphase2.txt', out_arr, fmt='%.5e', delimiter=",")

np.savetxt(filname, out_arr, fmt='%.5e', delimiter=",")
