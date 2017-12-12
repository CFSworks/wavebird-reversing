#!/usr/bin/env python

# Make Python 2's a/b act like Python 3's.
from __future__ import division

import numpy as np
import sys

# Some constants
CHIPS = np.array([-1,  1, -1,  1,  1, -1, -1,  1, -1, -1,  1,  1,  1,  1])
BITRATE = 96000
CHIPRATE = BITRATE*len(CHIPS)
SAMPLERATE = 4000000
FREQUENCY = 500000*np.pi*2 # Angular frequency (radians/sec) of FSK

# Get the command-line arguments
msg = sys.argv[1]
iq_file = sys.argv[2]

# Make sure 'msg' is a 200-bit hex string
try:
    if len(msg) != 50:
        raise ValueError('invalid length')
    msg_int = int(msg, 16)
except ValueError:
    print('Message should be a 200-bit hex string!')

# Convert msg to binary
msg_bin = np.array([msg_int&(1<<x) for x in range(199,-1,-1)], dtype=np.bool)

# Map True(1)/False(0) to +1/-1
msg_bits = msg_bin * 2 - 1

# Multiply each bit by the whole chipping sequence
msg_chips = np.outer(msg_bits, CHIPS).flatten()

# Turn the message into a series of angular frequencies
msg_frequencies = msg_chips * FREQUENCY

# Render that out into a series of phase angles - we're about to resample this,
# and phase angles behave better under under a linear interpolation than
# complex-valued samples
msg_phases = np.cumsum(msg_frequencies/CHIPRATE)

# Pad with the 100-microsecond "warmup"
warmup = [0] * int(CHIPRATE * 0.0001)
msg_phases = np.concatenate([warmup, msg_phases])

# Resample from CHIPRATE (what msg_phases is in) to SAMPLERATE (what we'll be
# transmitting in)
msg_resampled = np.interp(np.arange(0, len(msg_phases), CHIPRATE/SAMPLERATE),
                          np.arange(0, len(msg_phases)),
                          msg_phases)

# We're still working in phase angles; we need complex-valued samples
# Let's do that using Euler's formula
# https://en.wikipedia.org/wiki/Euler%27s_formula
samples = np.e ** (1j * msg_resampled)

# WaveBird protocol proper requires each burst be 4ms apart, so let's pad
# "samples" to 4ms using silence.
padding_needed = int(SAMPLERATE*0.004) - len(samples)
# Let's put half of the padding on either side
half_padding = [0]*(padding_needed//2)
samples = np.concatenate([half_padding, samples, half_padding])

# Repeat (actually, "tile") the buffer 250 times (to last 1 second)
samples = np.tile(samples, 250)

# Reformat as real/imag/real/imag 8-bit signed ints
# (This is kinda messy since I didn't know how else to do it in a compact way)
samples_8bit = (np.outer(samples, [1, -1j]).flatten().real * 127).astype(np.int8)

# Now it's out to a .iq file
with open(iq_file, 'wb') as output:
    samples_8bit.tofile(output)
