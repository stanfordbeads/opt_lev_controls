
## load all files in a directory and plot the correlation of the resonse
## with the drive signal versus time

import numpy as np
import matplotlib, calendar
import matplotlib.pyplot as plt
import os, re, glob
import bead_util as bu
import scipy.signal as sp
import scipy.optimize as opt
import cPickle as pickle

path = "/data/20140623/Bead1/freq_sweep_chirp"
## path to directory containing charge steps, used to calibrate phase and 
## scaling.  leave empty to use data path
cal_path = "/data/20140623/Bead1/one_charge_chirp"

## path to save plots and processed files (make it if it doesn't exist)
outpath = "/home/dcmoore/analysis" + path[5:]
if( not os.path.isdir( outpath ) ):
    os.makedirs(outpath)

reprocessfile = True
plot_angle = False
plot_phase = False
remove_laser_noise = False
remove_outliers = True
plot_flashes = False
ref_file = 0 ## index of file to calculate angle and phase for

file_start = 0

scale_fac = 1./0.00156
scale_file = 1.

amp_gain = 1. ## gain to use for files in path
amp_gain_cal = 1.  ## gain to use for files in cal_path

fsamp = 5000.
fdrive = 41.
fref = 1027
NFFT = 2**14
phaselen = int(fsamp/fdrive) #number of samples used to find phase
plot_scale = 1. ## scaling of corr coeff to units of electrons
plot_offset = 1.
data_columns = [0, 1] ## column to calculate the correlation against
drive_column = -1
laser_column = 3


b, a = sp.butter(3, [2.*(fdrive-1)/fsamp, 2.*(fdrive+1)/fsamp ], btype = 'bandpass')
boff, aoff = sp.butter(3, 2.*(fdrive-10)/fsamp, btype = 'lowpass')

def rotate_data(x, y, ang):
    c, s = np.cos(ang), np.sin(ang)
    return c*x - s*y, s*x + c*y

def getangle(fname):
        print "Getting angle from: ", fname 
        num_angs = 100
        dat, attribs, cf = bu.getdata(os.path.join(path, fname))
        pow_arr = np.zeros((num_angs,2))
        ang_list = np.linspace(-np.pi/2.0, np.pi/2.0, num_angs)
        for i,ang in enumerate(ang_list):
            rot_x, rot_y = rotate_data(dat[:,data_columns[0]], dat[:,data_columns[1]], ang)
            pow_arr[i, :] = [np.std(rot_x), np.std(rot_y)]
        
        best_ang = ang_list[ np.argmax(pow_arr[:,0]) ]
        print "Best angle [deg]: %f" % (best_ang*180/np.pi)

        cf.close()

        if(plot_angle):
            plt.figure()
            plt.plot(ang_list, pow_arr[:,0], label='x')
            plt.plot(ang_list, pow_arr[:,1], label='y')
            plt.xlabel("Rotation angle")
            plt.ylabel("RMS at drive freq.")
            plt.legend()
            
            ## also plot rotated time stream
            rot_x, rot_y = rotate_data(dat[:,data_columns[0]], dat[:,data_columns[1]], best_ang)
            plt.figure()
            plt.plot(rot_x)
            plt.plot(rot_y)
            plt.plot(dat[:, drive_column] * np.max(rot_x)/np.max(dat[:,drive_column]))
            plt.show()
        
        

        return best_ang

def getphase(fname, ang):
        print "Getting phase from: ", fname 
        dat, attribs, cf = bu.getdata(os.path.join(path, fname))
        xdat, ydat = rotate_data(dat[:,data_columns[0]], dat[:,data_columns[1]], ang)
        #xdat = sp.filtfilt(b, a, xdat)
        xdat = np.append(xdat, np.zeros( fsamp/fdrive ))
        corr2 = np.correlate(xdat,dat[:,drive_column])
        maxv = np.argmax(corr2) 

        cf.close()

        if(plot_phase):
            plt.figure()
            plt.plot( corr2 )
            plt.figure()
            xdat_filt = sp.filtfilt(b,a,xdat)
            drive_filt = sp.filtfilt(b,a,dat[:,drive_column])
            plt.plot( xdat_filt/np.max( xdat_filt ), label='x')
            plt.plot( drive_filt/np.max( drive_filt ), label='drive' )
            plt.legend()
            plt.show()

        print maxv
        return maxv


def getdata(fname, maxv, ang, gain):

	print "Processing ", fname
        dat, attribs, cf = bu.getdata(os.path.join(path, fname))

        ## make sure file opened correctly
        if( len(dat) == 0 ):
            return {}

        dat[:, drive_column] *= gain
        if( len(attribs) > 0 ):
            fsamp = attribs["Fsamp"]
            drive_amplitude = attribs["drive_amplitude"]

            
        xdat, ydat = rotate_data(dat[:,data_columns[0]], dat[:,data_columns[1]], ang)

        drive_amp = np.sqrt(2)*np.std(dat[:,drive_column])

        if( remove_laser_noise ):
            laser_good = bu.laser_reject(dat[:, laser_column], 60., 90., 4e-6, 100, fsamp, False)
        else:
            laser_good = np.ones_like(dat[:, laser_column]) > 0

        corr_full = bu.corr_func(dat[:,drive_column], xdat, fsamp, fdrive, good_pts=laser_good)

        corr = corr_full[ maxv ]
        corr_max = np.max(corr_full)
        corr_max_pos = np.argmax(corr_full)
        xpsd, freqs = matplotlib.mlab.psd(xdat, Fs = fsamp, NFFT = NFFT) 
        #ypsd, freqs = matplotlib.mlab.psd(ydat, Fs = fsamp, NFFT = NFFT) 
        max_bin = np.argmin( np.abs( freqs - fdrive ) )
        ref_bin = np.argmin( np.abs( freqs - fref ) )

        ## also correlate signal with drive squared
        dsq = dat[:,drive_column]**2
        dsq -= np.mean(dsq)
        sq_amp = np.sqrt(2)*np.std( dsq )
        ## only normalize by one factor of the squared amplitude
        corr_sq_full = bu.corr_func(dsq*sq_amp, xdat, fsamp, fdrive)
        corr_sq_max = np.max(corr_sq_full)
        corr_sq_max_pos = np.argmax(corr_sq_full)

        xoff = sp.filtfilt(boff, aoff, xdat)

        if(False):
            plt.figure()
            plt.plot( xdat )
            plt.plot( dat[:, drive_column] )

            plt.figure()
            plt.plot( corr_full )
            plt.show()

        ctime = attribs["time"]

        ## is this a calibration file?
        cdir,_ = os.path.split(fname)
        is_cal = cdir == cal_path

        curr_scale = 1.0
        ## make a dictionary containing the various calculations
        out_dict = {"corr_t0": corr,
                    "max_corr": [corr_max, corr_max_pos],
                    "max_corr_sq": [corr_sq_max, corr_sq_max_pos],
                    "psd": np.sqrt(xpsd[max_bin]),
                    "ref_psd": np.sqrt(xpsd[ref_bin]),
                    "temps": attribs["temps"],
                    "time": bu.labview_time_to_datetime(ctime),
                    "num_flashes": attribs["num_flashes"],
                    "is_cal": is_cal,
                    "drive_amp": drive_amp}

        cf.close()
        return out_dict

if reprocessfile:

  init_list = glob.glob(path + "/*.h5")
  files = sorted(init_list, key = bu.find_str)

  if(cal_path):
      cal_list = glob.glob(cal_path + "/*.h5")
      cal_files = sorted( cal_list, key = bu.find_str )
      files = zip(cal_files[:-1],np.zeros(len(cal_files[:-1]))+amp_gain_cal) \
              + zip(files[:-1],np.zeros(len(files[:-1]))+amp_gain)
  else:
      files = zip(files[:-1],np.zeros(len(files[:-1]))+amp_gain)      
      

  ang = 0 ##getangle(files[ref_file])
  phase = getphase(files[ref_file][0], ang)
  corrs_dict = {}
  for f,gain in files[file_start:]:
    curr_dict = getdata(f, phase, ang, gain)

    for k in curr_dict.keys():
        if k in corrs_dict:
            corrs_dict[k].append( curr_dict[k] )
        else:
            corrs_dict[k] = [curr_dict[k],]
    
  of = open(os.path.join(outpath, "processed.pkl"), "wb")
  pickle.dump( corrs_dict, of )
  of.close()
else:
  of = open(os.path.join(outpath, "processed.pkl"), "rb")
  corrs_dict = pickle.load( of )
  of.close()

## if a calibration data set is defined and the scale factor is 1,
## then try to calculate the scale factor from the calibration
is_cal = np.array( corrs_dict["is_cal"] )
if( np.sum(is_cal) > 0 and scale_fac == 1.):
    cal_dat = np.array(corrs_dict["corr_t0"])[is_cal]
    ## take a guess at the step size
    step_vals = np.abs( np.diff( cal_dat ) )
    step_guess = np.median( step_vals[ step_vals > 3*np.std(step_vals)] )
    ## only keep non-zero points (assuming sig-to-noise > 5)
    cal_dat = cal_dat[cal_dat > 0.2*step_guess]
    def scale_resid( s ):
        return np.sum( (cal_dat/s - np.round(cal_dat/s))**2  )
    ## do manual search for best scale fac
    slist = np.linspace(step_guess/1.2, step_guess*1.2, 1e4)
    scale_fac = 1./slist[np.argmin( map(scale_resid, slist) ) ]
    print "Calibration: guess, best_fit: ", 1./step_guess, scale_fac
    
## first plot the variation versus time
dates = matplotlib.dates.date2num(corrs_dict["time"])
corr_t0 = np.array(corrs_dict["corr_t0"])*scale_fac
max_corr = np.array(corrs_dict["max_corr"])[:,0]*scale_fac
max_corr_sq = np.array(corrs_dict["max_corr_sq"])[:,0]*scale_fac
best_phase = np.array(corrs_dict["max_corr"])[:,1]
psd = np.array(corrs_dict["psd"])*scale_fac
ref_psd = np.array(corrs_dict["ref_psd"])*scale_fac
temp1 = np.array(corrs_dict["temps"])[:,0]
temp2 = np.array(corrs_dict["temps"])[:,1]
num_flashes = np.array(corrs_dict["num_flashes"])
drive_amp = np.array(corrs_dict["drive_amp"])

plt.figure() 
plt.plot_date(dates, corr_t0, 'r.', label="Max corr")

## fit a polynomial to the ref pdf
p = np.polyfit(dates, ref_psd/np.median(ref_psd), 1)
xx = np.linspace(dates[0], dates[-1], 1e3)


def plot_avg_for_per(x, y, idx1, idx2, linecol):
    ## get the average and error (given by std of points) for a sub period between flashes
    eval, eerr = np.median(y[idx1:idx2]), np.std(y[idx1:idx2])/np.sqrt(idx2-idx1)
    ax = plt.gca()

    mid_idx = int( (idx1 + idx2)/2 )
    ax.vlines(x[mid_idx],eval-eerr,eval+eerr, color=linecol, linewidth=1.5)
    hash_width = (x[idx2]-x[idx1])/10.
    ax.hlines(eval+eerr,x[mid_idx]-hash_width,x[mid_idx]+hash_width, color=linecol, linewidth=1.5)
    ax.hlines(eval-eerr,x[mid_idx]-hash_width,x[mid_idx]+hash_width, color=linecol, linewidth=1.5)

    return x[mid_idx], eval
    

flash_idx = np.argwhere( num_flashes > 0 )

yy = plt.ylim()
## plot the location of the flashes and average each period between
## make sure to plot for first period
avg_vals = []
if(len(flash_idx)>1 and plot_flashes):
    plot_avg_for_per( dates, corr_t0, 0, flash_idx[0], 'r')
    for i,f in enumerate(flash_idx):
        plt.plot_date( [dates[f], dates[f]], yy, linestyle='-', color=[0.5, 0.5, 0.5], marker=None)
        if( i < len(flash_idx)-1 ):
            cx, eval_corr = plot_avg_for_per( dates, corr_t0, flash_idx[i], flash_idx[i+1], 'r')
            eval_psd = 0.0
            avg_vals.append( [cx, eval_corr, eval_psd] )

plt.ylim(yy)

plt.xlabel("Time")
plt.ylabel("Correlation with drive")
##plt.legend(numpoints = 1, loc="upper left")


fig1 = plt.figure() 
plt.subplot(1,2,1)

resid_data = corr_t0-np.round(corr_t0)
plt.plot_date(dates, resid_data, 'r.', markersize=2, label="Max corr")
## set limits at +/- 5 sigma
cmu, cstd = np.median(resid_data), np.std(resid_data)
yy = plt.ylim([cmu-5*cstd, cmu+5*cstd])
plt.ylim(yy)
plt.xlabel("Time")
plt.ylabel("Residual to nearest integer charge [$e$]")
ax = plt.gca()

hh, be = np.histogram( resid_data, bins = np.max([30, len(resid_data)/50]), range=yy )
bc = be[:-1]+np.diff(be)/2.0

## fit the data
def gauss_fun(x, A, mu, sig):
    return A*np.exp( -(x-mu)**2/(2*sig**2) )

amp0 = np.sum(hh)/np.sqrt(2*np.pi*cstd)
bp, bcov = opt.curve_fit( gauss_fun, bc, hh, p0=[amp0, cmu, cstd] )

if( remove_outliers ):

    ## throw out any bad times before doing the fit
    time_window = 5 ## mins
    nsig = 5
    bad_points = np.argwhere(np.abs(resid_data > bp[1]+nsig*bp[2]))
    pts_to_use = np.logical_not(is_cal)
    #pts_to_use = np.logical_and(np.logical_not(is_cal), bu.inrange(drive_amp, 5, 2000))
    print np.sum(pts_to_use)
    for p in bad_points:
        pts_to_use[ np.abs(dates - dates[p]) < time_window/(24.*60.)] = False

    plt.plot_date(dates[pts_to_use], resid_data[pts_to_use], 'k.', markersize=2, label="Max corr")
    cmu, cstd = np.median(resid_data[pts_to_use]), np.std(resid_data[pts_to_use])
    hh, be = np.histogram( resid_data[pts_to_use], bins = np.max([50, len(resid_data[pts_to_use])/50]), range=[cmu-10*cstd, cmu+10*cstd] )
    bc = be[:-1]+np.diff(be)/2.0
    amp0 = np.sum(hh)/np.sqrt(2*np.pi*cstd)
    bp, bcov = opt.curve_fit( gauss_fun, bc, hh, p0=[amp0, cmu, cstd] )

plt.subplot(1,2,2)
ax2 = plt.gca()
ax2.yaxis.set_visible(False)
ax.set_position(matplotlib.transforms.Bbox(np.array([[0.125,0.1],[0.675,0.9]])))
ax2.set_position(matplotlib.transforms.Bbox(np.array([[0.725,0.1],[0.9,0.9]])))

xx = np.linspace(yy[0], yy[1], 1e3)
plt.errorbar( hh, bc, xerr=np.sqrt(hh), yerr=0, fmt='k.', linewidth=1.5 )
plt.plot( gauss_fun(xx, bp[0], bp[1], bp[2]), xx, 'r', linewidth=1.5, label="$\mu$ = %.3e $\pm$ %.3e $e$"%(bp[1], np.sqrt(bcov[1,1])))
plt.legend()
plt.ylim(yy)

plt.xlabel("Counts")

## plot correlation with drive squared vs voltage
def make_corr_plot( amp_vec, corr_vec, col, lab=""):
    ## get a list of the drive amplitudes
    drive_list = amp_vec
    amp_list = np.transpose(np.vstack((corr_vec, np.zeros_like(corr_vec))))

    sf = 1.0 ##np.median( amp_list[:,0] )
    #plt.plot( amp_vec, corr_vec/sf, '.', color=[col[0]+0.5, col[1]+0.5, col[2]+0.5], zorder=1)
    plt.errorbar( drive_list, amp_list[:,0]/sf, yerr=amp_list[:,1]/sf, fmt='.', color=col, linewidth = 1.5, label=lab )
    fit_pts = drive_list < 40
    p = np.polyfit( drive_list[fit_pts], amp_list[fit_pts,0]/sf, 1)
    xx = np.linspace( np.min(drive_list), np.max(drive_list), 1e2)
    plt.plot(xx, np.polyval(p, xx), color=col, linewidth = 1.5)
    #plt.xlim([0, 1e3])
    plt.xlabel("Drive voltage [V]")
    plt.ylabel("Correlation with drive signal [V]")
    plt.legend(loc="upper left", numpoints = 1)
    #plt.ylim([-1, 2])

plt.figure()
pts_to_use = np.ones_like(drive_amp) > 0
make_corr_plot( drive_amp[pts_to_use], np.sqrt(max_corr_sq[pts_to_use]), [0,0,0], "sqrt(Corr w/ drive squared)")
make_corr_plot( drive_amp[pts_to_use], corr_t0[pts_to_use]*drive_amp[pts_to_use], [1,0,0], "Corr w/ drive")


plt.show()

