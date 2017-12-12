#!/usr/bin/env python2

SYNTHESIZE_PY = r"""
#!/usr/bin/python

# This is a very quick-and-dirty script to synthesize audio using Fourier
# synthesis. It uses a table of initial phases and magnitudes for each
# frequency from 0 Hz (constant) up to 2000 Hz. The audio is voice; nothing
# higher than 2000 Hz is really important to preserve the essence of the
# original clip.

# Fun fact: This uses only 8000 coefficients to produce 22050 samples. By not
# storing some of the frequencies, we manage to produce a smaller
# representation of the audio than the raw samples. This is the basis of
# compression algorithms like MP3 and Vorbis (although those are smarter about
# what they choose not to store).

# This is very, very slow. It could be made to run faster if using numpy arrays
# instead of Python lists, and even faster if using numpy's ifft function
# instead of doubly-nested for loops. I opted not to do this, however, to prove
# a point: you only need math.cos (or math.sin) to synthesize anything you
# want.

from __future__ import division

import sys
import wave
import math
import struct

# This table is formatted like so:
    # (PHASE_RAD, MAG), # 0 Hz (constant)
    # (PHASE_RAD, MAG), # 0.5 Hz
    # (PHASE_RAD, MAG), # 1.0 Hz
    # (PHASE_RAD, MAG), # 1.5 Hz

# That is, it contains the initial phase and amplitude for each frequency
# necessary to reconstruct the original audio:
TABLE = [INSERT_TABLE_HERE]

LENGTH = 2.0
SAMPLE_RATE = 11025

output = [0] * int(LENGTH * SAMPLE_RATE)

print('Please wait. This is kinda slow; there are ways to do it MUCH faster, but this script exists to prove a point...')

progress = 0

for freq, (phase_offset, magnitude) in enumerate(TABLE):
    # Update progress bar to keep the user satisfied...
    percentage = (freq*100)//len(TABLE)
    if percentage > progress:
        progress = percentage
        if percentage%10 == 0:
            sys.stdout.write('%')
        elif percentage%10 == 9:
            sys.stdout.write('0')
        elif percentage%10 == 8:
            sys.stdout.write('%d' % ((percentage+3)//10))
        else:
            sys.stdout.write('.')
        sys.stdout.flush()

    # Format frequency in Hz:
    freq *= 0.5

    # Angular frequency is radians per second:
    angular_freq = freq * math.pi * 2

    # Now we mix (sum) the frequency into the output:
    for i in range(len(output)):
        # i (sample number) to time (seconds):
        time = i / SAMPLE_RATE

        phase = angular_freq * time + phase_offset

        output[i] += math.sin(phase) * magnitude

sys.stdout.write('\n')
print('Okay; writing to synthesized.wav...')

w = wave.open('synthesized.wav', 'w')
w.setnchannels(1)
w.setsampwidth(1)
w.setframerate(SAMPLE_RATE)
for sample in output:
    sample = min(max(sample, -1), 1)
    w.writeframes(struct.pack('B', int(sample*127)+127))
w.close()
""".strip()

import numpy
import scipy.io.wavfile

rate, samples = scipy.io.wavfile.read('mario2s.wav')

assert rate == 44100
assert len(samples) == 88200

# Normalize to -1..1:
samples = samples.astype(numpy.float64)
samples /= numpy.max(numpy.abs(samples))

# DC balance:
samples -= numpy.mean(samples)

fft = numpy.fft.fft(samples)

# Averages, not sums:
fft /= len(fft)
# Truncate to positive bins only:
fft = fft[:len(fft)//2]
# Double the positive energy:
fft[1:] *= 2

[BEFORE_TABLE, AFTER_TABLE] = SYNTHESIZE_PY.split('INSERT_TABLE_HERE')

print(BEFORE_TABLE)
for freq, (phase, mag) in enumerate(zip(numpy.angle(fft), numpy.abs(fft))):
    if freq > 4000: break
    print('    (%f, %f),' % (phase, mag))
print(AFTER_TABLE)
