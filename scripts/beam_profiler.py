import numpy as np
import bead_util as bu
import matplotlib.pyplot as plt
import os
import scipy.signal as sig
import scipy
import glob


data_dir1 = r"C:\Data\20170302_profiling\test_no_amp_down"
data_dir2 = r"C:\Data\20170302_profiling\test_no_amp_down3"



#stage x = col 17, stage y = 18, stage z = 19
stage_column = 19
data_column = 0


def spatial_bin(xvec, yvec, bin_size = .13):
    fac = 1./bin_size
    bins_vals = np.around(fac*xvec)
    bins_vals/=fac
    bins = np.unique(bins_vals)
    y_binned = np.zeros_like(bins)
    y_errors = np.zeros_like(bins)
    for i, b in enumerate(bins):
        idx = bins_vals == b
        y_binned[i] =  np.mean(yvec[idx])
        y_errors[i] = scipy.stats.sem(yvec[idx])
    return bins, y_binned, y_errors
    
        
    

def profile(fname, ends = 100, stage_cal = 8.):
    dat, attribs, f = bu.getdata(fname)
    dat = dat[ends:-ends, :]
    #plt.plot(dat[:, data_column])
    #plt.show()
    dat[:, stage_column]*=stage_cal
    f.close()
    b, a = sig.butter(1, 1)
    int_filt = sig.filtfilt(b, a, dat[:, data_column])    
    proft = np.gradient(int_filt)
    stage_filt = sig.filtfilt(b, a, dat[:, stage_column])
    dir_sign = np.sign(np.gradient(stage_filt))
    b, y, e = spatial_bin(dat[dir_sign<0, stage_column], proft[dir_sign<0])
    return b, y, e


def proc_dir(dir):
    files = glob.glob(dir + '\*.h5')
    #print files
    bs = np.array([])
    ys = np.array([])
    for f in files:
        b, y, e = profile(f)
        bs = np.append(bs, b)
        ys = np.append(ys, y)
    return spatial_bin(bs, ys)
        
b1, y1, e1 = proc_dir(data_dir1)
b2, y2, e2 = proc_dir(data_dir2)



binx1 = np.argmax(y1)
binx2 = np.argmax(y2)
cent1 = b1[binx1]
cent2 = b2[binx2]

plt.errorbar(b1-cent1, y1/np.max(y1), e1, fmt = '.', label = "1")
#plt.errorbar(b1-cent1, y1, e1, fmt = '.', label = "1")
plt.errorbar(b2-cent2, y2/np.max(y2), e2, fmt = '.', label = "2")
#plt.errorbar(b2-cent2, y2, e2, fmt = '.', label = "2")
#plt.gca().set_yscale('log')
plt.xlabel('Position [um]')
plt.ylabel('Intensity [arbitrary units]')
plt.legend()
plt.show()

