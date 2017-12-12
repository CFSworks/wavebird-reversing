#!/usr/bin/env python

import re
import bz2
import collections

def hamming_distance(a,b):
    """
    Find the Hamming distance between a<->b, treating both as equal-length ints
    """
    assert isinstance(a, (int, long)) and isinstance(b, (int, long))
    x = a^b # XOR results in all differing bits set as '1'

    # Now we just count the 1s in x
    d = 0
    while x:
        x &= x-1 # Clears lowest set bit in x
        d += 1

    return d

REGEX = re.compile(r'^[01]{200}$')

counter = collections.Counter()
with bz2.BZ2File('button_mashing.log.bz2', 'r') as logfile:
    for line in logfile:
        # Strip off extra newline or space characters that may be in the log
        line = line.strip()

        # Only match 200-bit binary lines
        if not REGEX.match(line): continue

        # Parse binary to int
        msg = int(line, 2)

        # Check preamble/sync
        if (msg >> 152) != 0xfaaaaaaa1234: continue

        # Check footer
        if (msg & 0xFFF) != 0x110: continue

        # Extract just the "fec" part
        fec = (msg >> 28) & ((1 << 124) - 1)

        # Record it in the counter
        counter.update([fec])

# We want to eliminate any messages containing errors, but how do we do that
# without knowing the code? An easy heuristic is to accept anything that occurs
# 3+ times as error-free, and thus anything appearing only once or twice is
# ignored.
codewords = [k for k,v in counter.iteritems() if v >= 3]

# Now we test every possible combination of two codewords - essentially testing
# every codeword against everything after it in the list - to find the minimum
# distance
minimum_distance = 1000 # Insanely high default that will get reset
for i,code1 in enumerate(codewords):
    for code2 in codewords[i+1:]:
        d = hamming_distance(code1, code2)
        if d < minimum_distance:
            minimum_distance = d
            closest_codewords = (code1, code2)

print('Minimum distance: %d' % minimum_distance)
print('Closest two codewords:')
print(hex(closest_codewords[0]))
print(hex(closest_codewords[1]))
