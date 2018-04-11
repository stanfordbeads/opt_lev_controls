import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import norm

def fun(x, A, sig, mu, dc):
    '''gaussian fitting function with amplitude and dc offset'''
    return A*norm.pdf(x, mu, sig) + dc


stage_dist = 1.60 #in length between micrometer screws
fl = 1.0 #focal length of trap lens


dat = np.array([[0., 13.], [20., 13.], [15., 13.], [10., 13.], [5., 13.], [0., 13.], [20., 14.], [15., 13.], [10., 13.], [5., 13.], [0., 16.], [20., 18.], [15., 24.], [10., 26.], [5., 38.], [0., 52.], [20., 28.], [15., 230.], [10., 310.], [5., 306.], [0., 225.], [20., 131.], [15., 44.], [10., 13.], [5., 13.], [0., 13.], [20., 13.]])

dat2 = np.array([[2, 16], [5,17], [7,13], [10,13], [15,13], [17,23], [20,41], [22, 67], [0, 91], [2, 152], [5, 170], [7, 231], [10, 267], [13, 303], [15, 306], [17, 291], [20, 258], [23, 214], [0, 147], [3, 92], [5, 67], [7, 47], [10, 28], [13, 33], [15, 33], [17, 27], [20, 25], [23, 22], [0, 23], [3, 22], [5, 17], [8, 13], [10, 13], [13, 13]])


mic = dat2[:, 0]
volt = dat2[:, 1]

mic *= 2.*np.pi/25. #convert to phase
mic = np.unwrap(mic)#unwrap
mic *= 25./(2.*np.pi)#convert back
mic *= 0.001/25.#convert to micrometer_dsiplacement
qs = np.arctan(mic/stage_dist)

qtrap = qs/2.
dtrapin = fl*qtrap
dtrapum = 25000.*dtrapin

popt, pcov = curve_fit(fun, dtrapum, volt)
pltx = np.linspace(np.min(dtrapum), np.max(dtrapum), 1000)

plt.plot(dtrapum, volt, 'o')
lab = 'width = ' + str(popt[1])[:3] + 'um'
plt.plot(pltx, fun(pltx, *popt), 'r', label = lab)

plt.xlabel('displacement at trap [um]')
plt.ylabel('interference amplitude [mV]')
plt.legend()
plt.show()
