import numpy as np
import bead_util as bu
import matplotlib.pyplot as plt
import os
import scipy.signal as sig
import scipy
import glob
from scipy.optimize import curve_fit



data_dir1 = r"C:\Data\20180524\profiling\xsweep_2"
data_dir2 = r"C:\Data\20180524\profiling\xsweep_2"

#dirlabs = ['80um Above', '80um Below']
#dirlabs = ['x', 'y']
dirlabs = ['dir1', 'dir2']

#out_dir = r"C:\Data\20170704\profiling\output"
#data_dir2 = r"C:\Data\20160429\beam_profiles1"

multi_dir = True
height_to_plot_1 = 0.
height_to_plot_2 = 0.
bestind_offset = 0

INVERT = False
log_profs = True

ROI = [-2, 2] # um
#OFFSET = 2.*10**(-5)
OFFSET = 0

msq_fit = True #False
gauss_fit = True

#stage x = col 17, stage y = 18, stage z = 19
stage_column = 17
stage_column2 = 17

data_column = 3
data_column2 = 3  # 0 For data circa 2016

cant_cal = 8. #um/volt

pow_radius = 10    # um
compute_tail_pow = True

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
    
        
def gauss(x, A, mu, sig):
    '''gaussian fitting function'''
    return A*np.exp(-1.*(x-mu)**2/(2.*sig**2))

def profile(fname, ends = 100, stage_cal = 8., stage_column = 17.):
    dat, attribs, f = bu.getdata(fname)
    dat = dat[ends:-ends, :]
    if 'xsweep' in fname:
        stage_column = 17
        sign = 1.0
    elif 'ysweep' in fname:
        stage_column = 18
        if 'left' in fname:
            sign = 1.0
        elif 'right' in fname:
            sign = -1.0
        else:
            sign = 1.0
    #elif 'zsweep' in fname:
        #stage_column = 19
    dat[:,stage_column]*=stage_cal
    h = attribs["stage_settings"][2]*cant_cal
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
    stage_filt = sig.filtfilt(b, a, dat[:, stage_column])
    dir_sign = np.sign(np.gradient(stage_filt)) * sign
    xvec = dat[:,stage_column]
    yvec = (proft - proft * dir_sign) * 0.5 - (proft + proft * dir_sign) * 0.5
    #plt.plot(xvec, yvec)
    #plt.show()
    b, y, e = spatial_bin(xvec, yvec)
    #plt.errorbar(b, y, e)
    #plt.show()
    if INVERT:
        y = -1.*y
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

    def sigsq2(self, p0 = [1., 0., 3.], make_plot = False, plt_region = [-10, 10]):
        '''finds second moment by fitting to gaussian'''
        if type(self.mean) == str:
            self.dist_mean()
        popt, pcov = curve_fit(gauss, self.bins, self.y, p0 = p0)
        if make_plot:
            pb = (self.bins<plt_region[1])*(self.bins>plt_region[0])
            plt.semilogy(self.bins[pb], self.y[pb], 'o')
            plt.semilogy(self.bins[pb], gauss(self.bins[pb], *popt), 'r')
            plt.show()
        self.sigmasq = popt[-1]**2
        
        
         

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
        f.sigsq2()
        sigmasqs.append(f.sigmasq)
        hs.append(f.cant_height)
        
    return file_profs, np.array(hs), np.array(sigmasqs)
 
def plot_profs(fp_arr):
    #plots average profile from different heights
    i = 1
    for fp in fp_arr:
        #plt.errorbar(fp.bins, fp.y, fp.errors, label = str(np.round(fp.cant_height)) + 'um')
        if multi_dir:
            lab = dirlabs[i-1]
        else:
            lab = str(np.round(fp.cant_height)) + 'um'
        i += 1
        if multi_dir:
            plt.plot(fp.bins, fp.y / np.max(fp.y), 'o', label = lab)
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
    ind = np.argmin(np.abs(hs - height_to_plot_1))
    ind2 = np.argmin(np.abs(hs2 - height_to_plot_2))
    plot_profs([file_profs[ind]] + [fp2[ind2]])

else:
    plot_profs(file_profs)

if msq_fit:

    p0 = [5., 10., 40.]

    bfit = hs < 140.

    popt, pcov = curve_fit(Szsq, hs[bfit], sigmasqs[bfit], p0=p0, maxfev=10000)
    hplt = np.arange(np.min(hs), np.max(hs), 0.1)
    
    if multi_dir:
        bfit2 = hs2 < 140.
        popt2, pcov2 = curve_fit(Szsq, hs2[bfit2], sigsq2[bfit2], p0=p0, maxfev=10000)
        hplt2 = np.arange(np.min(hs2), np.max(hs2), 0.1)
        
        fig, axarr = plt.subplots(2, sharex=True, sharey=True)
        ax1 = axarr[0]
        ax2 = axarr[1]

    else:
        fig, axarr = plt.subplots(1, sharex=True)
        ax1 = axarr

        
    if multi_dir:    
        maxsig = np.max([np.max(sigmasqs), np.max(sigsq2)])
    else:
        maxsig = np.max(sigmasqs)
    
    ax1.plot(hs, sigmasqs, 'o')
    ax1.plot(hplt, Szsq(hplt, *popt), 'r',linewidth = 2,  label = "M^2=%0.3g"%popt[1]**2)
    ax1.set_title("Trap Focus at h = %g um, Waist w0 = %0.2g um"%(popt[-1],popt[0]*2.0))
    ax1.set_ylabel("second moment [um^2]")
    ax1.set_ylim(0, maxsig*1.2)
    ax1.legend(loc=0)

    if multi_dir:
        ax2.plot(hs2, sigsq2, 'o')
        ax2.plot(hplt2, Szsq(hplt2, *popt2), 'r',linewidth = 2,  label = "M^2=%0.3g"%popt2[1]**2)
        ax2.set_title("Trap Focus at h = %g um, Waist w0 = %0.2g um"%(popt2[-1],popt2[0]*2.0))
        ax2.set_ylabel("Second moment [um^2]")
        ax2.set_xlabel("Cantilever height [um]")
        ax2.set_ylim(0, maxsig*1.2)
        ax2.legend(loc=0)
    plt.show()


if gauss_fit:

    if multi_dir:
        f2, axarr2 = plt.subplots(2, sharex=True, sharey=True)
        ax1 = axarr2[0]
        ax2 = axarr2[1]
    else:
        f2, axarr2 = plt.subplots(1, sharex=True)
        ax1 = axarr2

    def gauss_wconst(x, A, x0, w0, C):
        return A * np.exp( -2 * (x-x0)**2 / (w0**2) ) + C
        
    def gauss(x, A, x0, w0):
        return A * np.exp( -2 * (x-x0)**2 / (w0**2) )
    
    if msq_fit:
        bestfit = np.argmin(np.abs(np.array(hs) - popt[-1])) - \
                                                       bestind_offset
        if multi_dir:
            bestfit2 = np.argmin(np.abs(np.array(hs2) - popt2[-1])) - \
                                                              bestind_offset
    else:
        bestfit = 0
        if multi_dir:
            bestfit2 = 0
    
    lab = hs[bestfit]
    if multi_dir:
        lab2 = hs2[bestfit2]
                        
    bestprof = file_profs[bestfit]
    if multi_dir:
        bestprof2 = fp2[bestfit2]

    #p02 = [10**(-3), 0, 10, 10**(-7)]
    #popt2, pcov2 = curve_fit(gauss_wconst, bestprof.bins, bestprof.y, p0=p02)

    p02 = [10**(-3), 0, 10]
    b_fit_1 = (bestprof.bins>ROI[0])*(bestprof.bins<ROI[1]) #get lower index for fit
    popt3, pcov3 = curve_fit(gauss, bestprof.bins[b_fit_1], bestprof.y[b_fit_1], p0=p02)
    fitpts = np.arange(np.min(bestprof.bins), np.max(bestprof.bins), 0.1)
    
    if multi_dir:
        b_fit_2 = (bestprof2.bins>ROI[0])*(bestprof2.bins<ROI[1])
        popt4, pcov4 = curve_fit(gauss, bestprof2.bins[b_fit_2], bestprof2.y[b_fit_2], p0=p02)
        fitpts2 = np.arange(np.min(bestprof2.bins), np.max(bestprof2.bins), 0.1)

        
    ax1.plot(bestprof.bins, bestprof.y, 'o')
    ax1.plot(fitpts, gauss(fitpts, *popt3), 'r', linewidth = 2, label='h = %0.2g' % lab)

    print
    
    if compute_tail_pow:
        r = np.abs(bestprof.bins)
        dr = bestprof.bins[1] - bestprof.bins[0]
        intpts = r > pow_radius
        area_facs = np.pi * r**2 * dr  
        tails = bestprof.y[intpts]
        tail_pow = np.sum(tails * area_facs[intpts])
        total_pow = np.sum(bestprof.y * area_facs)
        percent_pow = tail_pow / total_pow

        print "Percent power outside of %0.1g um: %0.3g (1)" % (pow_radius, percent_pow)
    
    data_int = np.sum(bestprof.y) * (bestprof.bins[1] - bestprof.bins[0])
    gauss_int = np.sum(gauss(fitpts, *popt3)) * (fitpts[1] - fitpts[0])

    print "Non-Gaussian Part (1): ", (data_int - gauss_int) / data_int

    ax1.set_title('Gaussian Fit Waist = %0.2g um' % (np.abs(popt3[2])) )
    ax1.set_ylabel("Intensity Profile [arbitrary]")
    ax1.set_ylim(10**(-6), popt3[0] * 10)
    ax1.set_yscale('log')
    ax1.legend(loc=0)
    
    if multi_dir:
        ax2.plot(bestprof2.bins, bestprof2.y, 'o')
        ax2.plot(fitpts2, gauss(fitpts2, *popt4), 'r', linewidth = 2, label='h = %0.2g' % lab2)
        if compute_tail_pow:
            r2 = np.abs(bestprof2.bins)
            dr2 = bestprof2.bins[1] - bestprof2.bins[0]
            intpts2 = r2 > pow_radius
            area_facs2 = np.pi * r2**2 * dr2
            tails2 = bestprof2.y[intpts2]
            tail_pow2 = np.sum(tails2 * area_facs2[intpts2])
            total_pow2 = np.sum(bestprof2.y * area_facs2)
            percent_pow2 = tail_pow2 / total_pow2

            print "Percent power outside of %0.1g um: %0.3g (2)" % (pow_radius, percent_pow2)

        
        data_int2 = np.sum(bestprof2.y) * (bestprof2.bins[1] - bestprof2.bins[0])
        gauss_int2 = np.sum(gauss(fitpts2, *popt4)) * (fitpts2[1] - fitpts2[0])
        print "Non-Gaussian Part (2): ", (data_int2 - gauss_int2) / data_int2

        ax2.set_title('Gaussian Fit Waist = %0.2g um' % (np.abs(popt4[2])) )
        ax2.set_xlabel("Cantilever Position [um]")
        ax2.set_ylabel("Intensity Profile [arbitrary]")
        ax2.set_ylim(10**(-6), popt4[0] * 10)
        ax2.set_yscale('log')
        ax2.legend(loc=0)
    
    plt.show()





