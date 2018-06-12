import numpy, h5py
import matplotlib
import matplotlib.pyplot as plt
import os
import scipy.signal as sp
import numpy as np
import bead_util as bu


refname = r"turbombar_xyzcool_0.h5"
reflab = ""

fname0 = r"turbombar_xyzcool_10.h5"
fillab = ""

path = r"C:\Data\20180605\bead1\post_pump"
d2plt = 0
conv_fac = 6.4e-14

Fs = 5e3  ## this is ignored with HDF5 files
userNFFT = 2**12

fullNFFT = True
#window = matplotlib.mlab.window_none
window = matplotlib.mlab.window_hanning

plot_second_xy = False
plot_pow = False
plot_drive = False

if fname0 == "":
	filelist = os.listdir(path)

	mtime = 0
	mrf = ""
	for fin in filelist:
                if '_fpga.h5' in fin:
                        continue
		f = os.path.join(path, fin) 
		if os.path.getmtime(f)>mtime:
			mrf = f
			mtime = os.path.getmtime(f) 
 
	fname0 = mrf		


		 

def getdata(fname):
	print "Opening file: ", fname
	## guess at file type from extension
	_, fext = os.path.splitext( fname )
	if( fext == ".h5") and ('_fpga.h5' not in fname):
		f = h5py.File(fname,'r')
		dset = f['beads/data/pos_data']
		dat = numpy.transpose(dset)
		#max_volt = dset.attrs['max_volt']
		#nbit = dset.attrs['nbit']
		Fs = dset.attrs['Fsamp']
                timestamp = dset.attrs['Time']
		
		#dat = 1.0*dat*max_volt/nbit
                dat = dat * 10./(2**15 - 1)
                
	else:
                print 'Not an .h5 file!'
                return

        fpga_fname = fname[:-3] + '_fpga.h5'
        fpga_dat = bu.get_fpga_data(fpga_fname,timestamp=timestamp)
        fpga_dat = bu.sync_and_crop_fpga_data(fpga_dat, timestamp, \
                                              len(dat[:,0]))

        xdat = fpga_dat['xyz'][0]
        ydat = fpga_dat['xyz'][1]
        zdat = fpga_dat['xyz'][2]

        if fullNFFT:
                NFFT = len(dat[:,0])
        else:
                NFFT = userNFFT
	xpsd, freqs = matplotlib.mlab.psd(xdat-np.mean(xdat), \
                                Fs = Fs, NFFT = NFFT, detrend = 'linear', \
                                window=window) 
	ypsd, freqs = matplotlib.mlab.psd(ydat-np.mean(ydat), \
                                Fs = Fs, NFFT = NFFT, detrend = 'linear', \
                                window=window) 
        zpsd, freqs = matplotlib.mlab.psd(zdat-np.mean(zdat), \
                                Fs = Fs, NFFT = NFFT, detrend = 'linear', \
                                window=window) 
        powpsd, freqs = matplotlib.mlab.psd(dat[:, 3]-np.mean(dat[:, 3]), \
                                Fs = Fs, NFFT = NFFT, detrend = 'linear')
        xpsd2, freqs = matplotlib.mlab.psd(dat[:, 4]-np.mean(dat[:, 4]), \
                                Fs = Fs, NFFT = NFFT, detrend = 'linear') 
        ypsd2, freqs = matplotlib.mlab.psd(dat[:, 5]-np.mean(dat[:, 5]), \
                                Fs = Fs, NFFT = NFFT, detrend = 'linear') 

	norm = numpy.median(dat[:, 2])
        #for h in [xpsd, ypsd, zpsd]:
        #        h /= numpy.median(dat[:,2])**2
	return [freqs, xpsd, ypsd, dat, zpsd, powpsd, xpsd2, ypsd2]

data0 = getdata(os.path.join(path, fname0))
if refname:
	data1 = getdata(os.path.join(path, refname))


fu = conv_fac


fig, axarr = plt.subplots(3, sharex=True)

if not fillab:
        fillab = 'file'
        
if not reflab:
        reflab = 'ref'

axarr[0].loglog(data0[0], np.sqrt(data0[1]), label=fillab, color='b')
if refname:
        axarr[0].loglog(data1[0], np.sqrt(data1[1]), label=reflab, color='g')
        axarr[0].legend(loc=3,fontsize=10)
axarr[0].set_ylabel("V/rt(Hz)")
axarr[0].set_xlabel("Frequency[Hz]")

axarr[1].loglog(data0[0], np.sqrt(data0[2]), color='b')
if refname:
        axarr[1].loglog(data1[0], np.sqrt(data1[2]), color='g')
axarr[1].set_ylabel("V/rt(Hz)")
axarr[1].set_xlabel("Frequency[Hz]")


axarr[2].loglog(data0[0],  np.sqrt(data0[4]), color='b')
if refname:
        axarr[2].loglog(data1[0], np.sqrt(data1[4]), color='g')
axarr[2].set_ylabel("V/rt(Hz)")
axarr[2].set_xlabel("Frequency[Hz]")

plt.legend()
plt.show()
