#!/usr/bin/env python

# Load up numpy and have it read the samples
import numpy as np
with open('held_start_ch9_4msps.iq', 'rb') as iq_file:
    samples = np.fromfile(iq_file, dtype=np.int8) / 128.
samples = samples[0::2] + samples[1::2]*1j # Every other byte is imaginary

# Remove the "DC spike" - the small offset from zero due to charges on the
# HackRF's ADC. This is easy: it's the only nonperiodic component in the
# signal, so we can find it by just averaging the whole signal.
dc_spike = np.mean(samples)
samples -= dc_spike # And we simply subtract it out to make the mean zero!

# Now we look for the OOK modulation. We don't care about the phase of each
# sample, only the magnitude.
mag = np.abs(samples)

# We'll consider anything above a certain threshold to be "on" and anything
# below to be "off" - let's set the threshold as the average:
threshold = np.mean(mag)

# And now we ask numpy to find what's above the threshold!
ook = mag > threshold

# Let's use matplotlib to see what we just got
from matplotlib import pyplot as plt
plt.ylim(0, 3)
plt.plot(ook)
plt.show()
