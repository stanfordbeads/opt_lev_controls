## set of utility functions useful for analyzing bead data

import h5py, os, matplotlib, re, sys, fnmatch
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
import scipy.optimize as opt
import scipy.signal as sp
import scipy.interpolate as interp

bead_radius = 2.53e-6 ##m
bead_rho = 2.0e3 ## kg/m^3
kb = 1.3806488e-23 #J/K
bead_mass = 4./3*np.pi*bead_radius**3 * bead_rho

## default columns for data files
data_columns = [0, 1] ## column to calculate the correlation against
drive_column = -1
laser_column = 3

## get the shape of the chameleon force vs. distance from Maxime's calculation
cforce = np.loadtxt(r"c:\GitHub\opt_lev_controls\scripts\data\chameleon_force.txt", delimiter=",")
## fit a spline to the data
cham_spl = interp.UnivariateSpline( cforce[::5,0], cforce[::5,1], s=0 )

def gain_fac( val ):
    ### Return the gain factor corresponding to a given voltage divider
    ### setting.  These numbers are from the calibration of the voltage
    ### divider on 2014/06/20 (in lab notebook)
    volt_div_vals = {0.:  1.,
                     1.:  1.,
                     20.0: 100./5.07,
                     40.0: 100./2.67,
                     80.0: 100./1.38,
                     200.0: 100./0.464}
    if val in volt_div_vals:
        return volt_div_vals[val]
    else:
        print "Warning, could not find volt_div value"
        return 1.
    

def getdata(fname):
    ### Get bead data from a file.  Guesses whether it's a text file
    ### or a HDF5 file by the file extension

    _, fext = os.path.splitext( fname )
    if( fext == ".h5"):
        try:
            f = h5py.File(fname,'r')
            dset = f['beads/data/pos_data']
            dat = np.transpose(dset)
            #max_volt = dset.attrs['max_volt']
            #nbit = dset.attrs['nbit']
            max_volt = 10.
            nbit = 32767.
            dat = 1.0*dat*max_volt/nbit
            attribs = dset.attrs

            ## correct the drive amplitude for the voltage divider. 
            ## this assumes the drive is the last column in the dset
            vd = 1. #vd = attribs['volt_div'] if 'volt_div' in attribs else 1.0
            curr_gain = gain_fac(vd)
            dat[:,-1] *= curr_gain

            ## now double check that the rescaled drive amp seems reasonable
            ## and warn the user if not
            offset_frac = 0.#offset_frac = np.abs(np.sqrt(2)*np.std( dat[:,-1] )/(200.0 * attribs['drive_amplitude'] )-1.0)
            if( curr_gain != 1.0 and offset_frac > 0.1):
                print "Warning, voltage_div setting doesn't appear to match the expected gain for ", fname

        except (KeyError, IOError):
            print "Warning, got no keys for: ", fname
            dat = []
            attribs = {}
            f = []
    else:
        dat = np.loadtxt(fname, skiprows = 5, usecols = [2, 3, 4, 5])
        attribs = {}
        f = []

    return dat, attribs, f

def copy_attribs(attribs):
    '''copies an hdf5 attributes into a new dictionary 
       so the original file can be closed.'''
    new_dict = {}
    for k in attribs.keys():
        new_dict[k] = attribs[k]
    return new_dict

def labview_time_to_datetime(lt):
    ### Convert a labview timestamp (i.e. time since 1904) to a 
    ### more useful format (python datetime object)
    
    ## first get number of seconds between Unix time and Labview's
    ## arbitrary starting time
    lab_time = dt.datetime(1904, 1, 1, 0, 0, 0)
    nix_time = dt.datetime(1970, 1, 1, 0, 0, 0)
    delta_seconds = (nix_time-lab_time).total_seconds()

    lab_dt = dt.datetime.fromtimestamp( lt - delta_seconds)
    
    return lab_dt
    

def inrange(x, xmin, xmax):
    return np.logical_and( x >= xmin, x<=xmax )

def bead_spec_rt_hz(f, A, f0, Damping):
    omega = 2*np.pi*f
    omega_0 = 2*np.pi*f0
    return np.sqrt(A*Damping/((omega_0**2 - omega**2)**2 + omega**2*Damping**2))


def get_calibration(refname, fit_freqs, make_plot=False, 
                    data_columns = [0,1], drive_column=-1, NFFT=2**14, exclude_peaks=False):
    ## given a reference file, fit the spectrum to a Lorentzian and return
    ## the calibration from V to physical units
    dat, attribs, cf = getdata(refname)
    if( len(attribs) > 0 ):
        fsamp = attribs["Fsamp"]
    xdat = dat[:,data_columns[1]]
    xpsd, freqs = matplotlib.mlab.psd(xdat, Fs = fsamp, NFFT = NFFT) 

    ##first, fit for the absolute calibration
    damp_guess = 400
    f0_guess = 150
    Aemp = np.median( xpsd[fit_freqs[0]:fit_freqs[0]+10] )
    spars = [Aemp*(2*np.pi*f0_guess)**4/damp_guess, f0_guess, damp_guess]

    fit_bool = inrange( freqs, fit_freqs[0], fit_freqs[1] )

    ## if there's large peaks in the spectrum, it can cause the fit to fail
    ## this attempts to exclude them.  If a single boolean=True is passed,
    ## then any points 50% higher than the starting points are excluded (useful
    ## for th overdamped case). If a list defining frequency ranges is passed, e.g.:
    ## [[f1start, f1stop],[f2start, f2stop],...], then points within the given
    ## ranges are excluded
    if( isinstance(exclude_peaks, list) ):
        for cex in exclude_peaks:
            fit_bool = np.logical_and(fit_bool, np.logical_not( inrange(freqs, cex[0],cex[1])))
    elif(exclude_peaks):
        fit_bool = np.logical_and( fit_bool, xpsd < 1.5*Aemp )

    xdat_fit = freqs[fit_bool]
    ydat_fit = np.sqrt(xpsd[fit_bool])
    bp, bcov = opt.curve_fit( bead_spec_rt_hz, xdat_fit, ydat_fit, p0=spars)
    #bp = spars
    #bcov = 0.

    print bp

    print attribs["temps"][0]+273
    norm_rat = (2*kb*(attribs["temps"][0]+273)/(bead_mass)) * 1/bp[0]

    if(make_plot):
        fig = plt.figure()
        plt.loglog( freqs, np.sqrt(norm_rat * xpsd), '.' )
        plt.loglog( xdat_fit, np.sqrt(norm_rat * ydat_fit**2), 'k.' )
        xx = np.linspace( freqs[fit_bool][0], freqs[fit_bool][-1], 1e3)
        plt.loglog( xx, np.sqrt(norm_rat * bead_spec_rt_hz( xx, bp[0], bp[1], bp[2] )**2), 'r')
        plt.xlabel("Freq [Hz]")
        plt.ylabel("PSD [m Hz$^{-1/2}$]")
    
    return np.sqrt(norm_rat), bp, bcov

def fit_spec(refname, fit_freqs, make_plot=False, 
                    data_columns = [0,1], drive_column=-1, NFFT=2**14, exclude_peaks=False):
    ## given a reference file, fit the spectrum to a Lorentzian and return
    ## the calibration from V to physical units
    dat, attribs, cf = getdata(refname)
    if( len(attribs) > 0 ):
        fsamp = attribs["Fsamp"]
        press = attribs["pressures"]
    xdat = dat[:,data_columns[0]]
    xpsd, freqs = matplotlib.mlab.psd(xdat, Fs = fsamp, NFFT = NFFT) 

    ##first, fit for the absolute calibration
    damp_guess = 400
    f0_guess = 150
    Aemp = np.median( xpsd[fit_freqs[0]:fit_freqs[0]+10] )
    spars = [Aemp*(2*np.pi*f0_guess)**4/damp_guess, f0_guess, damp_guess]

    fit_bool = inrange( freqs, fit_freqs[0], fit_freqs[1] )

    ## if there's large peaks in the spectrum, it can cause the fit to fail
    ## this attempts to exclude them.  If a single boolean=True is passed,
    ## then any points 50% higher than the starting points are excluded (useful
    ## for th overdamped case). If a list defining frequency ranges is passed, e.g.:
    ## [[f1start, f1stop],[f2start, f2stop],...], then points within the given
    ## ranges are excluded
    if( isinstance(exclude_peaks, list) ):
        for cex in exclude_peaks:
            fit_bool = np.logical_and(fit_bool, np.logical_not( inrange(freqs, cex[0],cex[1])))
    elif(exclude_peaks):
        fit_bool = np.logical_and( fit_bool, xpsd < 1.5*Aemp )

    xdat_fit = freqs[fit_bool]
    ydat_fit = np.sqrt(xpsd[fit_bool])
    bp, bcov = opt.curve_fit( bead_spec_rt_hz, xdat_fit, ydat_fit, p0=spars)
    #bp = spars
    #bcov = 0.

    print bp

    print attribs["temps"][0]+273
    norm_rat = (2*kb*(attribs["temps"][0]+273)/(bead_mass)) * 1/bp[0]

    if(make_plot):
        fig = plt.figure()
        plt.loglog( freqs, np.sqrt(norm_rat * xpsd), '.' )
        plt.loglog( xdat_fit, np.sqrt(norm_rat * ydat_fit**2), 'k.' )
        xx = np.linspace( freqs[fit_bool][0], freqs[fit_bool][-1], 1e3)
        plt.loglog( xx, np.sqrt(norm_rat * bead_spec_rt_hz( xx, bp[0], bp[1], bp[2] )**2), 'r')
        plt.xlabel("Freq [Hz]")
        plt.ylabel("PSD [m Hz$^{-1/2}$]")
    
    #return np.sqrt(norm_rat), bp, bcov, press
    bin_low = np.argmin( np.abs( freqs - 10. ))
    bin_hi = np.argmin( np.abs( freqs - 40. ))
    noise_val = np.median( xpsd[bin_low:bin_hi] )
    return noise_val, bp, bcov, press

def find_str(str):
    """ Function to sort files.  Assumes that the filename ends
        in #mV_#Hz[_#].h5 and sorts by end index first, then
        by voltage """
    #idx_offset = 1e10 ## large number to ensure sorting by index first

    #fname, _ = os.path.splitext(str)

    endstr = int(re.findall("\d+", str)[-2])
    #if( len(endstr) != 1 ):
        ## couldn't find the expected pattern, just return the 
        ## second to last number in the string
        #return int(re.findall('\d+', fname)[-2])
        
    ## now check to see if there's an index number
    #sparts = endstr[0].split("_")
    #if( len(sparts) == 3 ):
        #return idx_offset*int(sparts[2]) + int(sparts[0][:-2])
    #else:
        #return int(sparts[0][:-2])
    return endstr
    
def unwrap_phase(cycles):
    #Converts phase in cycles from ranging from 0 to 1 to ranging from -0.5 to 0.5 
    if cycles>0.5:
        cycles +=-1
    return cycles

def laser_reject(laser, low_freq, high_freq, thresh, N, Fs, plt_filt):
    #returns boolian vector of points where laser is quiet in band. Averages over N points.
    b, a = sp.butter(3, [2.*low_freq/Fs, 2.*high_freq/Fs], btype = 'bandpass')
    filt_laser_sq = np.convolve(np.ones(N)/N, sp.filtfilt(b, a, laser)**2, 'same')
    if plt_filt:
        plt.figure()
        plt.plot(filt_laser_sq)
        plt.plot(np.argwhere(filt_laser_sq>thresh),filt_laser_sq[filt_laser_sq>thresh],'r.')
        plt.show()
    return filt_laser_sq<=thresh


def good_corr(drive, response, fsamp, fdrive):
    corr = np.zeros(fsamp/fdrive)
    response = np.append(response, np.zeros( fsamp/fdrive-1 ))
    n_corr = len(drive)
    for i in range(len(corr)):
        #Correct for loss of points at end
        correct_fac = 1.0*n_corr/(n_corr-i)
        corr[i] = np.sum(drive*response[i:i+n_corr])*correct_fac
    return corr

def corr_func(drive, response, fsamp, fdrive, good_pts = [], filt = False, band_width = 1):
    #gives the correlation over a cycle of drive between drive and response.

    #First subtract of mean of signals to avoid correlating dc
    drive = drive-np.median(drive)
    response  = response - np.median(response)

    #bandpass filter around drive frequency if desired.
    if filt:
        b, a = sp.butter(3, [2.*(fdrive-band_width/2.)/fsamp, 2.*(fdrive+band_width/2.)/fsamp ], btype = 'bandpass')
        drive = sp.filtfilt(b, a, drive)
        response = sp.filtfilt(b, a, response)
    
    #Compute the number of points and drive amplitude to normalize correlation
    lentrace = len(drive)
    drive_amp = np.sqrt(2)*np.std(drive)

      
    #Throw out bad points if desired
    if len(good_pts):
        response[-good_pts] = 0.
        lentrace = np.sum(good_pts)    


    corr_full = good_corr(drive, response, fsamp, fdrive)/(lentrace*drive_amp)
    return corr_full

def corr_blocks(drive, response, fsamp, fdrive, good_pts = [], filt = False, band_width = 1, N_blocks = 20):
    #Computes correlation in blocks to determine error.

    #first determine average phase to use throughout.
    tot_phase =  np.argmax(corr_func(drive, response, fsamp, fdrive, good_pts, filt, band_width))
    
    #Now initialize arrays and loop over blocks
    corr_in_blocks = np.zeros(N_blocks)
    len_block = len(drive)/int(N_blocks)
    for i in range(N_blocks):
        corr_in_blocks[i] = corr_func(drive[i*len_block:(i+1)*len_block], response[i*len_block:(i+1)*len_block], fsamp, fdrive, good_pts, filt, band_width)[tot_phase]
    return [np.mean(corr_in_blocks), np.std(corr_in_blocks)/N_blocks]

def gauss_fun(x, A, mu, sig):
    return A*np.exp( -(x-mu)**2/(2*sig**2) )

def get_chameleon_force( sep ):
    return cham_spl(sep)




def extract_quad(quad_dat, timestamp, verbose=False):
    '''Reads a stream of I32s, finds the first timestamp,
       then starts de-interleaving the demodulated data
       from the FPGA'''
    
    if timestamp == 0.0:
        # if no timestamp given, use current time
        # and set the timing threshold for 1 month.
        # This threshold is used to identify the timestamp 
        # in the stream of I32s
        timestamp = time.time()
        diff_thresh = 31.0 * 24.0 * 3600.0
    else:
        timestamp = timestamp * (10.0**(-9))
        diff_thresh = 60.0

    writing_data = False
    quad_ind = 0

    quad_time = []
    amp = [[], [], [], [], []]
    phase = [[], [], [], [], []]
    for ind, dat in enumerate(quad_dat):

        # Data in the 'quad' FIFO comes through as:
        # time_MSB -> time_LSB ->
        # amp0     -> amp1     -> amp2   -> amp3   -> amp4   ->
        # phase0   -> phase1   -> phase2 -> phase3 -> phase4 ->
        # and then repeats. Amplitude and phase variables are 
        # arbitrarily scaled so thinking of them as 32-bit integers
        # is okay. We just care about the bits anyway. The amplitude
        # is unsigned, so we get an extra bit of precision there
        if writing_data:
            if quad_ind == 0 and ind != (len(quad_dat) - 1):
                high = np.uint32(quad_dat[ind])
                low = np.uint32(quad_dat[ind+1])
                dattime = (high.astype(np.uint64) << np.uint64(32)) \
                           + low.astype(np.uint64)
                quad_time.append(dattime)
            elif quad_ind == 2:
                amp[0].append(dat.astype(np.uint32))
            elif quad_ind == 3:
                amp[1].append(dat.astype(np.uint32))
            elif quad_ind == 4:
                amp[2].append(dat.astype(np.uint32))
            elif quad_ind == 5:
                amp[3].append(dat.astype(np.uint32))
            elif quad_ind == 6:
                amp[4].append(dat.astype(np.uint32))
            elif quad_ind == 7:
                phase[0].append(dat)
            elif quad_ind == 8:
                phase[1].append(dat)
            elif quad_ind == 9:
                phase[2].append(dat)
            elif quad_ind == 10:
                phase[3].append(dat)
            elif quad_ind == 11:
                phase[4].append(dat)
            
            quad_ind += 1
            quad_ind = quad_ind % 12

                # Check for the timestamp
        if not writing_data and quad_ind == 0:
            # Assemble time stamp from successive I32s, since
            # it's a 64 bit object
            high = np.int32(quad_dat[ind])
            low = np.int32(quad_dat[ind+1])
            dattime = (high.astype(np.uint64) << np.uint64(32)) \
                        + low.astype(np.uint64)

            # Time stamp from FPGA is a U64 with the UNIX epoch 
            # time in nanoseconds, synced to the host's clock
            if (np.abs(timestamp - float(dattime) * 10**(-9)) < diff_thresh):
                if verbose:
                    print "found timestamp  : ", float(dattime) * 10**(-9)
                    print "comparison time  : ", timestamp 
                quad_time.append(dattime)
                quad_ind += 1
                writing_data = True

    # Since the FIFO read request is asynchronous, sometimes
    # the timestamp isn't first to come out, but the total amount of data
    # read out is a multiple of 12 (2 time + 5 amp + 5 phase) so an
    # amplitude or phase channel ends up with less samples.
    # The following is coded very generally

    min_len = 10.0**9  # Assumes we never more than 1 billion samples
    for ind in [0,1,2,3,4]:
        if len(amp[ind]) < min_len:
            min_len = len(amp[ind])
        if len(phase[ind]) < min_len:
            min_len = len(phase[ind])

    # Re-size everything by the minimum length and convert to numpy array
    quad_time = np.array(quad_time[:min_len])
    for ind in [0,1,2,3,4]:
        amp[ind]   = amp[ind][:min_len]
        phase[ind] = phase[ind][:min_len]
    amp = np.array(amp)
    phase = np.array(phase)
      

    return quad_time, amp, phase






def extract_xyz(xyz_dat, timestamp, verbose=False):
    '''Reads a stream of I32s, finds the first timestamp,
       then starts de-interleaving the demodulated data
       from the FPGA'''
    
    if timestamp == 0.0:
        # if no timestamp given, use current time
        # and set the timing threshold for 1 month.
        # This threshold is used to identify the timestamp 
        # in the stream of I32s
        timestamp = time.time()
        diff_thresh = 31.0 * 24.0 * 3600.0
    else:
        timestamp = timestamp * (10.0**(-9))
        diff_thresh = 60.0

    writing_data = False
    xyz_ind = 0

    xyz_time = []
    xyz = [[], [], []]

    for ind, dat in enumerate(xyz_dat):

        # Data in the 'xyz' FIFO comes through as:
        # time_MSB -> time_LSB ->
        # X        -> Y        -> Z   -> 
        # and then repeats. Position  variables are 
        # arbitrarily scaled so thinking of them as 32-bit integers
        # is okay. We just care about the bits anyway
        if writing_data:
            if xyz_ind == 0 and ind != (len(xyz_dat) - 1):
                high = np.uint32(xyz_dat[ind])
                low = np.uint32(xyz_dat[ind+1])
                dattime = (high.astype(np.uint64) << np.uint64(32)) \
                           + low.astype(np.uint64)
                xyz_time.append(dattime)
            elif xyz_ind == 2:
                xyz[0].append(dat)
            elif xyz_ind == 3:
                xyz[1].append(dat)
            elif xyz_ind == 4:
                xyz[2].append(dat)
            
            xyz_ind += 1
            xyz_ind = xyz_ind % 5

        # Check for the timestamp
        if not writing_data and xyz_ind == 0:
            # Assemble time stamp from successive I32s, since
            # it's a 64 bit object
            high = np.int32(xyz_dat[ind])
            low = np.int32(xyz_dat[ind+1])
            dattime = (high.astype(np.uint64) << np.uint64(32)) \
                        + low.astype(np.uint64)

            # Time stamp from FPGA is a U64 with the UNIX epoch 
            # time in nanoseconds, synced to the host's clock
            if (np.abs(timestamp - float(dattime) * 10**(-9)) < diff_thresh):
                if verbose:
                    print "found timestamp  : ", float(dattime) * 10**(-9)
                    print "comparison time  : ", timestamp 
                xyz_time.append(dattime)
                xyz_ind += 1
                writing_data = True

    # Since the FIFO read request is asynchronous, sometimes
    # the timestamp isn't first to come out, but the total amount of data
    # read out is a multiple of 5 (2 time + X + Y + Z) so the Z
    # channel usually  ends up with less samples.
    # The following is coded very generally

    min_len = 10.0**9  # Assumes we never more than 1 billion samples
    for ind in [0,1,2]:
        if len(xyz[ind]) < min_len:
            min_len = len(xyz[ind])

    # Re-size everything by the minimum length and convert to numpy array
    xyz_time = np.array(xyz_time[:min_len])
    for ind in [0,1,2]:
        xyz[ind]   = xyz[ind][:min_len]
    xyz = np.array(xyz)        

    return xyz_time, xyz







def get_fpga_data(fname, timestamp=0.0, verbose=False):
    '''Raw data from the FPGA is saved in an hdf5 (.h5) 
       file in the form of 3 continuous streams of I32s
       (32-bit integers). This script reads it out and 
       makes sense of it for post-processing'''

    # Open the file and bring datasets into memory
    try:
        f = h5py.File(fname,'r')
        dset0 = f['beads/data/raw_data']
        dset1 = f['beads/data/quad_data']
        dset2 = f['beads/data/pos_data']
        dat0 = np.transpose(dset0)
        dat1 = np.transpose(dset1)
        dat2 = np.transpose(dset2)
        f.close()

    # Shit failure mode. What kind of sloppy coding is this
    except (KeyError, IOError):
        if verbose:
            print "Warning, got no keys for: ", fname
        dat0 = []
        dat1 = []
        dat2 = []
        attribs = {}
        try:
            f.close()
        except:
            if verbose:
                print "couldn't close file, not sure if it's open"

    # Use subroutines to handle each type of data
    # raw_time, raw_dat = extract_raw(dat0, timestamp)
    raw_time, raw_dat = (None, None)
    quad_time, amp, phase = extract_quad(dat1, timestamp, verbose=verbose)
    xyz_time, xyz = extract_xyz(dat2, timestamp, verbose=verbose)

    # Assemble the output as a human readable dictionary
    out = {'raw_time': raw_time, 'raw_dat': raw_dat, \
           'xyz_time': xyz_time, 'xyz': xyz, \
           'quad_time': quad_time, 'amp': amp, \
           'phase': phase}

    return out



def sync_and_crop_fpga_data(fpga_dat, timestamp, nsamp):
    '''Based on the daqmx timestamp, find the start of the starting
       point in the FPGA and crop the result to have the same number
       of samples.'''

    out = {}
    out['raw_time'] = fpga_dat['raw_time']
    out['raw_dat'] = fpga_dat['raw_dat']

    # Find the xyz and quad timestamps that match the daqmx first 
    # sample timestamp
    xyz_time_ind = np.argmin( np.abs( fpga_dat['xyz_time'] - timestamp ) )
    quad_time_ind = np.argmin( np.abs( fpga_dat['quad_time'] - timestamp ) )

    # Crop the xyz arrays
    out['xyz_time'] = fpga_dat['xyz_time'][xyz_time_ind:xyz_time_ind+nsamp]
    out['xyz'] = fpga_dat['xyz'][:,xyz_time_ind:xyz_time_ind+nsamp]

    # Crop the quad arrays
    out['quad_time'] = fpga_dat['quad_time'][quad_time_ind:quad_time_ind+nsamp]
    out['amp'] = fpga_dat['amp'][:,quad_time_ind:quad_time_ind+nsamp]
    out['phase'] = fpga_dat['phase'][:,quad_time_ind:quad_time_ind+nsamp]

    # return data in the same format as it was given
    return out






def find_all_fnames(dirlist, ext='.h5', sort=True, exclude_fpga=True):
    '''Finds all the filenames matching a particular extension
       type in the directory and its subdirectories .
       INPUTS: dirlist, list of directory names to loop over
               ext, file extension you're looking for
               sort, boolean specifying whether to do a simple sort
       OUTPUTS: files, list of files names as strings'''

    print "Finding files in: "
    print dirlist
    sys.stdout.flush()

    was_list = True

    lengths = []
    files = []

    if type(dirlist) == str:
        dirlist = [dirlist]
        was_list = False

    for dirname in dirlist:
        for root, dirnames, filenames in os.walk(dirname):
            for filename in fnmatch.filter(filenames, '*' + ext):
                if ('_fpga.h5' in filename) and exclude_fpga:
                    continue
                files.append(os.path.join(root, filename))
        if was_list:
            if len(lengths) == 0:
                lengths.append(len(files))
            else:
                lengths.append(len(files) - np.sum(lengths)) 
            
    if sort:
        # Sort files based on final index
        files.sort(key = find_str)

    if len(files) == 0:
        print "DIDN'T FIND ANY FILES :("

    print "Found %i files..." % len(files)
    if was_list:
        return files, lengths
    else:
        return files


def sort_files_by_timestamp(files):
    '''Pretty self-explanatory function.'''
    files = [(get_hdf5_time(path), path) for path in files]
    files.sort(key = lambda x: (x[0]))
    files = [obj[1] for obj in files]
    return files


def get_hdf5_time(fname):
    try:
        f = h5py.File(fname,'r')
        dset = f['beads/data/pos_data']
        attribs = copy_attribs(dset.attrs)
        f.close()

    except (KeyError, IOError):
        print "Warning, got no keys for: ", fname
        attribs = {}

    return attribs["Time"]

