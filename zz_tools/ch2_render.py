#!/usr/bin/env python2

from __future__ import division

import sys
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

visualization = sys.argv[1]

SAMP_RATE = 42500
DIALTONE_US = np.zeros(SAMP_RATE, dtype=np.complex64)
for i in range(len(DIALTONE_US)):
    for frequency in [350, 440]:
        phase = math.pi*2 * frequency * i/SAMP_RATE
        DIALTONE_US[i] += math.e**(phase*1j) * 0.5

DIALTONE_EU = np.zeros(SAMP_RATE, dtype=np.complex64)
for i in range(len(DIALTONE_EU)):
    phase = math.pi*2 * 425 * i/SAMP_RATE
    DIALTONE_EU[i] += math.e**(phase*1j) * 0.5

if visualization == 'signal':
    SAMPLES = 1250
    plt.title("A dial tone (Europe)")
    plt.plot(np.arange(0,SAMPLES)/SAMP_RATE, DIALTONE_EU[:SAMPLES])
    plt.xlabel('Time (seconds)')
    plt.ylabel('Amplitude')
elif visualization in ['sampled', 'nyquist', 'aliased']:
    SAMPLES = 1250
    plt.plot(np.arange(0,SAMPLES)/SAMP_RATE, DIALTONE_EU[:SAMPLES])
    plt.xlabel('Time (seconds)')
    plt.ylabel('Amplitude')

    DECIMATION = {'sampled': 18,
                  'nyquist': 50,
                  'aliased': 95}[visualization]
    TITLE = {'sampled': 'Sampled dial tone (Europe)',
             'nyquist': 'Sampled dial tone (Europe) at Nyquist rate',
             'aliased': 'Undersampled dial tone (Europe) showing aliasing'}[visualization]
    plt.title(TITLE)

    sampled = DIALTONE_EU[:SAMPLES:DECIMATION]
    plt.quiver(np.arange(0,len(sampled))*DECIMATION/SAMP_RATE, sampled*0,
               sampled*0, sampled.real,
               units='y', width=0.01, scale=1)

plt.savefig('../02_signals_and_sampling/%s.png' % visualization)
