#!/usr/bin/env python

# Stuff copied over from chapter 4
import sys # This time we take the filename on the command line
import numpy as np
with open(sys.argv[1], 'rb') as iq_file:
    samples = np.fromfile(iq_file, dtype=np.int8) / 128.
samples = samples[0::2] + samples[1::2]*1j

dc_spike = np.mean(samples)
samples -= dc_spike

window = np.hanning(30)
window /= np.sum(window)
level = np.convolve(np.abs(samples), window, mode='same')
mean = level.mean()
signal_level = level[level>mean].mean()
noise_level = level[level<mean].mean()
signal_threshold = 0.75*signal_level + 0.25*noise_level
noise_threshold = 0.75*noise_level + 0.25*signal_level

# We're going to chunk apart *all* bursts, not just one from the middle
def hyst(x, th_lo, th_hi, initial = False):
    """
    Analyze 'x' and return False where it's below th_lo,
    True where it's above th_hi, and the previous value if between.

    From https://stackoverflow.com/questions/23289976/how-to-find-zero-crossings-with-hysteresis
    """
    hi = x >= th_hi
    lo_or_hi = (x <= th_lo) | hi
    ind = np.nonzero(lo_or_hi)[0]
    if not ind.size: # prevent index error if ind is empty
        return np.zeros_like(x, dtype=bool) | initial
    cnt = np.cumsum(lo_or_hi) # from 0 to len(x)
    return np.where(cnt, hi[ind[cnt-1]], initial)

is_signal = hyst(level, noise_threshold, signal_threshold)

import itertools
i = 0
bursts = []
for signal,grouper in itertools.groupby(is_signal):
    run_length = len(list(grouper))
    i += run_length

    if signal:
        if 8000 < run_length < 12000: # Ignore bursts of wrong length
            bursts.append(samples[i-run_length:i])

# Now that we have our bursts, the actual decoding stuff comes next
CHIPS = np.array([-1,  1, -1,  1,  1, -1, -1,  1, -1, -1,  1,  1,  1,  1])
# Repeat each item 3 times to try to match the CHIPS rate to the sample rate
CHIPS = CHIPS.repeat(3)

# Threshold for picking up the clock
THRESHOLD = 20

from collections import Counter
counter = Counter()
for burst in bursts:
    # FM demodulation from last chapter
    burst_conj = np.conjugate(burst)
    autocorrelation = burst[1:] * burst_conj[:-1]
    fm = np.angle(autocorrelation)

    # The new part: correlating `fm` with `CHIPS`
    correlation = np.correlate(fm, CHIPS)

    # Find a correlation strong enough to call it the first bit
    first_bit = np.argwhere(np.abs(correlation) > THRESHOLD)[0][0]
    # Fast forward to it
    correlation = correlation[first_bit:]

    bits = ''
    while len(correlation):
        # Look for the strongest correlation somewhere in the window
        strongest = np.argmax(np.abs(correlation[:5]))

        # Record its polarity in 'bits'
        bits += ('1' if correlation[strongest] > 0 else '0')

        # Fast forward to where the next bit is expected
        correlation = correlation[strongest + len(CHIPS) - 2:]

    print(bits)
    counter.update([bits])

# Also print the most common (i.e. the 'mode') bitstring. The mode is the
# most likely to be error-free and devoid of random noise from e.g. the analog
# sticks.
mode, times = counter.most_common(1)[0]

# If the mode happens to be 200 bits, convert it to hex ;)
if len(mode) == 200:
    mode = '%050x' % int(mode, 2)

print('-'*79)
print('Mode: %s (%s times)' % (mode, times))
