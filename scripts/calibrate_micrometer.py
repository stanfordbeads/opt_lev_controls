import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

dat2 = np.array([2.0525, 2.0365, 2.0215, 2.0070, 1.9925, 1.978, 1.964])
dat = np.array([2.066, 2.051, 2.0365, 2.022, 2.0070, 1.9920, 1.9775, 1.9625, 1.9480, 1.9335, 1.9190])
n_turns = len(dat)
n_plot = 100
turns = np.arange(n_turns)


fun = lambda x, m, b: m*x + b

popt, pcov = curve_fit(fun, turns, dat)

xplt = np.linspace(0, n_turns, n_plot)
plt.plot(turns, dat, 'o')
plt.plot(xplt, fun(xplt, *popt), label = str(popt[0]) + "in/turn")
plt.legend()
plt.show()
