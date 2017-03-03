import numpy as np
import bead_util as bu
import matplotlib.pyplot as plt
import os
import scipy.signal as sig
import scipy
import glob
from scipy.optimize import curve_fit

data_dir1 = r"C:\Data\20170302_profiling\hsteps_4turns_out"



#stage x = col 17, stage y = 18, stage z = 19
stage_column = 19
data_column = 0
cant_cal = 8. #um/volt


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
    h = attribs["stage_settings"][0]*cant_cal
    f.close()
    b, a = sig.butter(1, 1)
    int_filt = sig.filtfilt(b, a, dat[:, data_column])    
    proft = np.gradient(int_filt)
    stage_filt = sig.filtfilt(b, a, dat[:, stage_column])
    dir_sign = np.sign(np.gradient(stage_filt))
    b, y, e = spatial_bin(dat[dir_sign<0, stage_column], proft[dir_sign<0])
    return b, y, e, h

class File_prof:
    "Class storing information from a single file"
    
    def __init__(self, b, y, e, h):
        self.bins = b
        self.dxs = np.append(np.diff(b), 0)#0 pad left trapizoid rule
        self.y = y
        self.errors = e
        self.cant_height = h
        self.mean = "mean not computed"
        self.sigmasq = "std dev not computed"
        
    def dist_mean(self):
        #Finds the cnetroid of intensity distribution. subtracts centroid from bins
        norm = np.sum(self.y*self.dxs)
        self.mean = np.sum(self.dxs*self.y*self.bins)/norm
        self.bins -= self.mean

    def sigsq(self):
        #finds second moment of intensity distribution.
        if type(self.mean) == str:
            self.dist_mean()
        norm = np.sum(self.y*self.dxs)
        self.sigmasq = np.sum(self.bins**2*self.y)/norm
         

def proc_dir(dir):
    files = glob.glob(dir + '\*.h5')
    #print files
    file_profs = []
    hs = []
    for fi in files:
        b, y, e, h = profile(fi)
        if h not in hs:
            #if new height then create new profile object
            hs.append(h)
            f = File_prof(b, y, e, h)
            file_profs.append(f)
        else:
            #if height repeated then append data to object for that height
            for fi in file_profs:
                if fi.cant_height == h:
                    fi.bins = np.append(fi.bins, b)
                    fi.y = np.append(fi.y, y)
                    fi.errors = np.append(fi.errors, e)
            
    #now rebin all profiles
    for fp in file_profs:
        b, y, e = spatial_bin(fp.bins, fp.y)
        fp.bins = b
        fp.y = y
        fp.errors = e
        fp.dxs = np.append(np.diff(fp.bins), 0)#0 pad left trapizoid rule

    sigmasqs = []
    hs = []

    for f in file_profs:
        f.sigsq()
        sigmasqs.append(f.sigmasq)
        hs.append(f.cant_height)
        
    return file_profs, hs, sigmasqs
 
def plot_profs(fp_arr):
    #plots average profile from different heigths
    for fp in fp_arr:
        plt.errorbar(fp.bins, fp.y, fp.errors, label = str(np.round(fp.cant_height)) + 'um')
    plt.xlabel("position [um]")
    plt.ylabel("margenalized irradiance ~[W/m]")
    plt.legend()
    plt.show()


def Szsq(z, s0, M, z0, lam = 1.064):
    #function giving propigation of W=2sig parameter. See Seegman
    W0 = 2.*s0
    Wzsq = W0**2 + M**4*(lam/(np.pi*W0))**2*(z-z0)**2
    return Wzsq/4.
    

#def compute_msquared(hs, sigmasqs):
    #fits beam profile data to extract M^2 value 


file_profs, hs, sigmasqs = proc_dir(data_dir1)

p0 = [5., 10., 0.]

popt, pcov = curve_fit(Szsq, hs, sigmasqs, p0=p0)

hplt = np.arange(np.min(hs), np.max(hs), 0.1)
plt.plot(hs, sigmasqs, 'o')
plt.plot(hplt, Szsq(hplt, *popt), 'r',linewidth = 2,  label = "M^2=" + str(int(popt[1]**2)))
plt.xlabel("Cantilever height [um]")
plt.ylabel("second moment of intensity distribution [um^2]")
plt.legend()
plt.show()




