#!/usr/bin/env python

import re
import bz2

REGEX = re.compile(r'^[01]{200}$')

# Functions copied from analyze_buttons.py:
def cyclic_decode(x):
    g = 0b11101101001

    msg = 0
    for i in range(21):
        msg = msg << 1
        if x&1:
            x ^= g
            msg |= 1
        x = x >> 1

    assert x == 0 # Ensure everything got cleared (i.e. no bit errors)

    return msg

def deinterleave(x):
    a = b = c = d = 0

    for i in range(124):
        d |= (x & 1) << (i//4)
        x = x >> 1
        a, b, c, d = d, a, b, c

    return (a, b, c, d)

def full_decode(x):
    a, b, c, d = deinterleave(x)

    return (cyclic_decode(a) << 63 |
            cyclic_decode(b) << 42 |
            cyclic_decode(c) << 21 | 
            cyclic_decode(d))

messages = {}
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

        # Extract just "fec" part
        fec = (msg >> 28) & ((1 << 124) - 1)

        # Decode it
        try:
            raw = full_decode(fec)
        except AssertionError:
            # Bit error detected! Just move along...
            continue

        # Extract the crc
        crc = (msg >> 12) & 0xFFFF

        #raw = sum(((raw>>i)&1)<<(4*(i%21)+i//21) for i in range(84))

        # Record it in the set of messages
        # First make sure we aren't overwriting a differing CRC
        assert messages.get(raw, crc) == crc
        messages[raw] = crc

# This prints a few of the raw/crcs, if enabled:
#for raw,crc in list(messages.items())[:3]:
#    print('crc(%021x) = %04x' % (raw, crc))

# Now for the main candidate-finding loop
candidates = []
for msg,crc in messages.items():

    # For each '0' bit in 'msg', try to find another message where the bit is 1
    for i in range(84):
        if (msg>>i) & 1: continue # Only interested in '0' bits

        msg2 = msg | (1<<i)
        assert msg2 != msg

        crc2 = messages.get(msg2)
        if crc2 is None: continue # We don't have msg2

        msg_difference = msg^msg2
        crc_difference = crc^crc2

        candidates.append((msg_difference, crc_difference))

# Sort in ascending order of 'msg' so we print cleanly;
# ascending order is also increasing the number of shift-xor iterations the
# polynomial has to go through before being presented as output
candidates.sort(key=lambda (msg, crc): msg)

last_line = None
last_msg = 0
for msg,crc in candidates:
    line = ('crc(%021x) = %04x' % (msg, crc))

    if line != last_line: # Don't repeat ourselves
        if msg != last_msg<<1:
            print('') # Break it apart where they aren't really "in a row"
        last_msg = msg

        print(line)
        last_line = line
