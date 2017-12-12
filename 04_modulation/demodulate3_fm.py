#!/usr/bin/env python

# Stuff from last time
import numpy as np
with open('held_start_ch9_4msps.iq', 'rb') as iq_file:
    samples = np.fromfile(iq_file, dtype=np.int8) / 128.
samples = samples[0::2] + samples[1::2]*1j

dc_spike = np.mean(samples)
samples -= dc_spike

samples = samples[2000000:]
window = np.hanning(30) # This generates a 30-sample-wide gently-sloping window function
window /= np.sum(window) # This "normalizes" it (so it sums to 1)
level = np.convolve(np.abs(samples), window, mode='same')
mean = level.mean()
signal_level = level[level>mean].mean()
noise_level = level[level<mean].mean()
signal_threshold = 0.75*signal_level + 0.25*noise_level
noise_threshold = 0.75*noise_level + 0.25*signal_level
first_noise = np.argwhere(level < noise_threshold)[0][0]
first_signal = np.argwhere(level[first_noise:] > signal_threshold)[0][0] + first_noise
last_signal = np.argwhere(level[first_signal:] < noise_threshold)[0][0] + first_signal
first_signal -= 30
last_signal += 30
burst = samples[first_signal:last_signal]

# Okay, let's FM-demodulate 'burst'. As I said, there's a *bunch* of ways to do
# this, but we'll just measure the phase difference between each pair of
# samples.
burst_conj = np.conjugate(burst) # Negate all angles
autocorrelation = burst[1:] * burst_conj[:-1] # Multiply each sample by its previous sample's conjugate
fm = np.angle(autocorrelation) # Have numpy tell us the angles for each

# Now let's see what it looks like...
from matplotlib import pyplot as plt
plt.plot(fm)
plt.show()
