#!/usr/bin/env python

# Stuff from last time
import numpy as np
with open('held_start_ch9_4msps.iq', 'rb') as iq_file:
    samples = np.fromfile(iq_file, dtype=np.int8) / 128.
samples = samples[0::2] + samples[1::2]*1j

dc_spike = np.mean(samples)
samples -= dc_spike



# We found out last time that the transmitter sends multiple bursts of data.
# To save time, we can just look at one. First let's discard like half of the
# sample buffer, just to get something nearer to the middle
samples = samples[2000000:]

# We need a more reliable indicator of signal level. Let's smooth out the
# amplitude to remove noise spikes so we can just use that.
window = np.hanning(30) # This generates a 30-sample-wide gently-sloping window function
window /= np.sum(window) # This "normalizes" it (so it sums to 1)
# Finally, this sweeps it across the samples, sorta performing a per-sample
# weighted average with each of its 30 nearest neighbors
level = np.convolve(np.abs(samples), window, mode='same')

# Because the WaveBird transmits ~50% of the time, the mean level makes a great
# threshold
mean = level.mean()

# We'll say anything above the mean is signal, and anything below the mean is
# noise...
signal_level = level[level>mean].mean()
noise_level = level[level<mean].mean()

# And we can put our cutoff thresholds somewhere between those two extremes
signal_threshold = 0.75*signal_level + 0.25*noise_level
noise_threshold = 0.75*noise_level + 0.25*signal_level

# We ask numpy for the first sample of noise, the first sample after that of
# signal, and the first sample after *that* of noise again
first_noise = np.argwhere(level < noise_threshold)[0][0]
first_signal = np.argwhere(level[first_noise:] > signal_threshold)[0][0] + first_noise
last_signal = np.argwhere(level[first_signal:] < noise_threshold)[0][0] + first_signal

# Spread apart first_signal and last_signal a little
first_signal -= 30
last_signal += 30

# Ta-daaaa
burst = samples[first_signal:last_signal]

# Let's see it
from matplotlib import pyplot as plt
plt.plot(np.abs(burst))
plt.show()
