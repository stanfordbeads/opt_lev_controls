import numpy, h5py
import matplotlib
import matplotlib.pyplot as plt
import os
import scipy.signal as sp
import numpy as np
import bead_util as bu


refname = r"1_5mbar_nocool.h5"
reflab = ""

fname0 = r""
fillab = ""

path = r"C:\Data\20170720\bead3"
d2plt = 0
conv_fac = 6.4e-14

Fs = 5e3  ## this is ignored with HDF5 files
NFFT = 2**14

plot_second_xy = False
plot_pow = False
plot_drive = False

if fname0 == "":
	filelist = os.listdir(path)

	mtime = 0
	mrf = ""
	for fin in filelist:
		f = os.path.join(path, fin) 
		if os.path.getmtime(f)>mtime:
			mrf = f
			mtime = os.path.getmtime(f) 
 
	fname0 = mrf		


		 

def getdata(fname):
	print "Opening file: ", fname
	## guess at file type from extension
	_, fext = os.path.splitext( fname )
	if( fext == ".h5"):
		f = h5py.File(fname,'r')
		dset = f['beads/data/pos_data']
		dat = numpy.transpose(dset)
		#max_volt = dset.attrs['max_volt']
		#nbit = dset.attrs['nbit']
		Fs = dset.attrs['Fsamp']
		
		#dat = 1.0*dat*max_volt/nbit
                dat = dat * 10./(2**15 - 1)
                
	else:
		dat = numpy.loadtxt(fname, skiprows = 5, usecols = [2, 3, 4, 5, 6] )

	xpsd, freqs = matplotlib.mlab.psd(dat[:, 0]-np.mean(dat[:, 0]), Fs = Fs, NFFT = NFFT, detrend = 'linear') 
	ypsd, freqs = matplotlib.mlab.psd(dat[:, 1]-np.mean(dat[:, 1]), Fs = Fs, NFFT = NFFT, detrend = 'linear')
        zpsd, freqs = matplotlib.mlab.psd(dat[:, 2]-np.mean(dat[:, 2]), Fs = Fs, NFFT = NFFT, detrend = 'linear')
        powpsd, freqs = matplotlib.mlab.psd(dat[:, 3]-np.mean(dat[:, 3]), Fs = Fs, NFFT = NFFT, detrend = 'linear')
        xpsd2, freqs = matplotlib.mlab.psd(dat[:, 4]-np.mean(dat[:, 4]), Fs = Fs, NFFT = NFFT, detrend = 'linear') 
        ypsd2, freqs = matplotlib.mlab.psd(dat[:, 5]-np.mean(dat[:, 5]), Fs = Fs, NFFT = NFFT, detrend = 'linear') 

	norm = numpy.median(dat[:, 2])
        #for h in [xpsd, ypsd, zpsd]:
        #        h /= numpy.median(dat[:,2])**2
	return [freqs, xpsd, ypsd, dat, zpsd, powpsd, xpsd2, ypsd2]

data0 = getdata(os.path.join(path, fname0))
if refname:
	data1 = getdata(os.path.join(path, refname))

if plot_pow:
    plt.figure()
    plt.plot(data0[3][:,3])
    plt.plot(data1[3][:,3])
    plt.figure()
    plt.loglog(data0[0], np.sqrt(data0[5]))
    plt.loglog(data1[0], np.sqrt(data1[5]))
    plt.show()
    

def rotate(vec1, vec2, theta):
    vecn1 = numpy.cos(theta)*vec1 + numpy.sin(theta)*vec2
    vecn2 = numpy.sin(theta)*vec1 + numpy.cos(theta)*vec2
    return [vec1, vec2]



Fs = 10000
b, a = sp.butter(1, [2*5./Fs, 2*10./Fs], btype = 'bandpass')


if plot_drive:

        fig = plt.figure()
        plt.subplot(311)
        plt.plot(data0[3][:,17])
        plt.subplot(312)
        plt.plot(data0[3][:,18])
        plt.subplot(313)
        plt.plot(data0[3][:,19])
        plt.show()


if d2plt:	

        fig = plt.figure()
        plt.plot(data0[3][:, 2] - np.mean(data0[3][:, 2]) )
        #plt.plot(data0[3][:, 1])
        if refname:
                plt.plot(data1[3][:, 2] - np.mean(data1[3][:, 2]) )
       # plt.plot(np.abs(data0[3][:, 3])-np.mean(np.abs(data0[3][:, 3])))
       

#r, bp, pcov = bu.get_calibration(os.path.join(path, refname), [1, 1000], make_plot = True)

#k = (bp[1]*2.*np.pi)**2*bu.bead_mass
#fu = r*k

#print fu

fu = conv_fac

meanpow0 = np.mean(data0[3][:,4])
if refname:
        meanpow1 = np.mean(data1[3][:,4])

fig, axarr = plt.subplots(3, sharex=True)

if not fillab:
        fillab = 'file'
        
if not reflab:
        reflab = 'ref'

axarr[0].loglog(data0[0], np.sqrt(data0[1]), label=fillab, color='b')
if plot_second_xy:
        axarr[0].loglog(data0[0], np.sqrt(data0[6]), label=fillab+' 2', color='r')
if refname:
        axarr[0].loglog(data1[0], np.sqrt(data1[1]), label=reflab, color='g')
        if plot_second_xy:
                axarr[0].loglog(data1[0], np.sqrt(data1[6]), label=reflab+' 2', color='m')
        axarr[0].legend(loc=3,fontsize=10)
axarr[0].set_ylabel("V/rt(Hz)")
axarr[0].set_xlabel("Frequency[Hz]")

axarr[1].loglog(data0[0], np.sqrt(data0[2]), color='b')
if plot_second_xy:
        axarr[1].loglog(data0[0], np.sqrt(data0[7]), color='r')
if refname:
        axarr[1].loglog(data1[0], np.sqrt(data1[2]), color='g')
        if plot_second_xy:
                axarr[1].loglog(data1[0], np.sqrt(data1[7]), color='m')
axarr[1].set_ylabel("V/rt(Hz)")
axarr[1].set_xlabel("Frequency[Hz]")


axarr[2].loglog(data0[0],  np.sqrt(data0[4]), color='b')
if refname:
        axarr[2].loglog(data1[0], np.sqrt(data1[4]), color='g')
axarr[2].set_ylabel("V/rt(Hz)")
axarr[2].set_xlabel("Frequency[Hz]")

plt.legend()
plt.show()
