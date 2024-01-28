#!/usr/bin/env python2

from __future__ import division

import sys
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def do_annotate(fig, chips):
    for i,chip in enumerate(chips):
        x = i + 0.4
        y = chip * 1.2 - 0.1
        fig.annotate(str(chip), xy=(x, y))

CHIPS = np.array([-1,  1, -1,  1,  1, -1, -1,  1, -1, -1,  1,  1,  1,  1])

f, (pos, neg) = plt.subplots(2, sharex=True, sharey=True)
for fig, chips in [(pos, CHIPS), (neg, -CHIPS)]:
    fig.plot([chips[0]] + list(chips), color='g' if fig == pos else 'r', drawstyle='steps-pre')
    fig.axes.get_xaxis().set_visible(False)
    fig.axes.get_yaxis().set_visible(False)
    do_annotate(fig, chips)

plt.ylim(-1.5, 1.5)
f.subplots_adjust(hspace=0)
plt.savefig('../05_line_coding_and_framing/img/chip_sequences.png')
