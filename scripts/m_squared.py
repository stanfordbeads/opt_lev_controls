import numpy as np
import bead_util as bu
import matplotlib.pyplot as plt
import os
import scipy.signal as sig
import scipy
import glob
from scipy.optimize import curve_fit



data_dir2 = r"C:\Data\20170525\beam_profiling\zsweep_1_0_turn_up_1_5_turn_left"

data_dir1 = r"C:\Data\20170525\beam_profiling\ysweep_1_0_turn_up_1_5_turn_left"

#data_dir2 = r"C:\Data\20160429\beam_profiles1"

multi_dir = True #False
height_to_plot = 30.

log_profs = True

ROI = [-80, 80] # um
#OFFSET = 2.*10**(-5)
OFFSET = 0

msq_fit = True
gauss_fit = True

#stage x = col 17, stage y = 18, stage z = 19
stage_column = 19
stage_column2 = 18
data_column = 3
data_column2 = 0
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
    if 'zsweep' in fname:
        stage_column = 19
    elif 'ysweep' in fname:
        stage_column = 18
    dat[:,stage_column]*=stage_cal
    h = attribs["stage_settings"][0]*cant_cal
    f.close()
    b, a = sig.butter(1, 1)
    if '2016' in fname:
        int_filt = sig.filtfilt(b, a, dat[:, data_column2])
    else:
        int_filt = sig.filtfilt(b, a, dat[:, data_column])
    #plt.plot(int_filt)
    #fft = np.fft.rfft(int_filt)
    #freqs = np.fft.rfftfreq(len(int_filt), d=1./5000)
    #plt.figure()
    #plt.loglog(freqs, fft * fft.conj())
    #plt.show()
    proft = np.gradient(int_filt)- OFFSET
    if 'zsweep' in fname:
        stage_filt = sig.filtfilt(b, a, dat[:, 19])
        #stage_column = 19
    elif 'ysweep' in fname:
        stage_filt = sig.filtfilt(b, a, dat[:, 18])
        #stage_column = 18
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
        self.date = "date not entered"
        
    def dist_mean(self):
        #Finds the cnetroid of intensity distribution. subtracts centroid from bins
        norm = np.sum(self.y*self.dxs)
        self.mean = np.sum(self.dxs*self.y*self.bins)/norm
        self.bins -= self.mean

    def sigsq(self):
        #finds second moment of intensity distribution.
        if type(self.mean) == str:
            self.dist_mean()
        derp1 = self.bins > ROI[0]
        derp2 = self.bins < ROI[1]
        ROIbool = np.array([a and b for a, b in zip(derp1, derp2)])
        norm = np.sum(self.y[ROIbool]*self.dxs[ROIbool])
        #norm = np.sum(self.y*self.dxs)
        self.sigmasq = np.sum(self.bins[ROIbool]**2*self.y[ROIbool])/norm
        #self.sigmasq = np.sum(self.bins**2*self.y)/norm
         

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
            f.date = dir[8:16]
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
        
    return file_profs, np.array(hs), np.array(sigmasqs)
 
def plot_profs(fp_arr):
    #plots average profile from different heights
    i = 1
    for fp in fp_arr:
        #plt.errorbar(fp.bins, fp.y, fp.errors, label = str(np.round(fp.cant_height)) + 'um')
        #lab = str(np.round(fp.cant_height)) + 'um'
        lab = 'dir' + str(i)
        i += 1
        if multi_dir:
            plt.plot(fp.bins, fp.y / np.amax(fp.y), 'o', label = lab)
            plt.ylim(10**(-5), 10)
        else:
            plt.plot(fp.bins, fp.y, 'o', label = lab)
    plt.xlabel("position [um]")
    plt.ylabel("margenalized irradiance ~[W/m]")
    if log_profs:
        plt.gca().set_yscale('log')
    else:
        plt.gca().set_yscale('linear')
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

if multi_dir:
    fp2, hs2, sigsq2 = proc_dir(data_dir2)
    ind = np.argmin(np.abs(hs - height_to_plot))
    ind2 = np.argmin(np.abs(hs2 - height_to_plot))
    plot_profs([file_profs[ind]] + [fp2[ind2]])

else:
    plot_profs(file_profs)

if msq_fit:

    p0 = [5., 10., 40.]

    bfit = hs < 140.

    popt, pcov = curve_fit(Szsq, hs[bfit], sigmasqs[bfit], p0=p0, maxfev=10000)

    hplt = np.arange(np.min(hs), np.max(hs), 0.1)
    plt.plot(hs, sigmasqs, 'o')
    plt.plot(hplt, Szsq(hplt, *popt), 'r',linewidth = 2,  label = "M^2=%0.3g"%popt[1]**2)
    plt.title("Trap Focus at h = %g um, Waist w0 = %0.2g um"%(popt[-1],popt[0]))
    plt.xlabel("Cantilever height [um]")
    plt.ylabel("second moment of intensity distribution [um^2]")
    plt.legend(loc=0)
    plt.show()


if gauss_fit:

    def gauss_wconst(x, A, x0, w0, C):
        return A * np.exp( -2 * (x-x0)**2 / (w0**2) ) + C
        
    def gauss(x, A, x0, w0):
        return A * np.exp( -2 * (x-x0)**2 / (w0**2) )
    
    if msq_fit:
        bestfit = np.argmin(np.abs(np.array(hs) - popt[-1]))
    else:
        bestfit = 0
    
    lab = hs[bestfit]
    bestprof = file_profs[bestfit]

    #p02 = [10**(-3), 0, 10, 10**(-7)]
    #popt2, pcov2 = curve_fit(gauss_wconst, bestprof.bins, bestprof.y, p0=p02)

    p02 = [10**(-3), 0, 10]    
    popt2, pcov2 = curve_fit(gauss, bestprof.bins, bestprof.y, p0=p02)

    fitpts = np.arange(np.min(bestprof.bins), np.max(bestprof.bins), 0.1)
    plt.plot(bestprof.bins, bestprof.y, 'o')
    
    #plt.plot(fitpts, gauss_wconst(fitpts, *popt2), 'r', linewidth = 2, label='h = %0.2g' % lab)
    plt.plot(fitpts, gauss(fitpts, *popt2), 'r', linewidth = 2, label='h = %0.2g' % lab)

    data_int = np.sum(bestprof.y) * (bestprof.bins[1] - bestprof.bins[0])
    gauss_int = np.sum(gauss(fitpts, *popt2)) * (fitpts[1] - fitpts[0])

    print 
    print "Non-Gaussian Part: ", (data_int - gauss_int) / data_int
    
    plt.title('Gaussian Fit Waist = %0.2g um' % (np.abs(popt2[2])) )
    plt.xlabel("Cantilever Position [um]")
    plt.ylabel("Intensity Profile [arbitrary]")
    plt.ylim(10**(-6), popt2[0] * 10)
    plt.gca().set_yscale('log')
    plt.legend(loc=0)
    plt.show()





