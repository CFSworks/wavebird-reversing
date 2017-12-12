#!/usr/bin/env python

import argparse

def crc16(n):
    """
    Compute CRC-CCITT on the bits of integer 'n'

    This implementation uses a continuously-running shift register going in
    reverse to work on the bits in lowest-first order!
    """

    g = 0x1021 # Polynomial

    crc = 0
    r = g # Shift register seeded with polynomial

    while n:
        if n&1:
            crc ^= r

        n >>= 1

        # Perform a shift-xor operation on 'r'
        r <<= 1
        if r&0x10000:
            r ^= g
            r &= 0xFFFF

    return crc

def interleave(n, b):
    """
    Interleaves 'n', where n is understood to be a b-bit integer

    The interleaving scheme is essentially this: write the bits of 'n' into a
    b/4-wide, 4-high matrix (in left-right, top-bottom order), then transpose
    the matrix, then read the bits back out in the same order
    """

    assert n.bit_length() <= b

    out = 0
    for i in range(b):
        x = (n>>i) & 1 # x = 'i'th bit of 'n'

        row, col = divmod(i, b//4)
        j = col*4 + row # j = where 'i' gets interleaved to

        if x:
            out |= 1<<j

    return out

def cyclic_encode(x):
    """
    Encode a 21-bit value into a 31-bit cyclic-encoded codeword.

    This scheme is essentially what POCSAG uses.
    """
    g = 0b11101101001

    codeword = 0
    for i in range(21):
        codeword <<= 1

        if x&1:
            codeword ^= g

        x >>= 1

    return codeword

def fec_encode(x):
    """
    Encode 84-bit value 'x' using 4 cyclic_encodes, then interleave
    """

    assert x.bit_length() <= 84

    d = cyclic_encode(x & 0x1FFFFF)
    c = cyclic_encode(x>>21 & 0x1FFFFF)
    b = cyclic_encode(x>>42 & 0x1FFFFF)
    a = cyclic_encode(x>>63 & 0x1FFFFF)

    return interleave(a<<93 | b<<62 | c<<31 | d, 124)

def frame(fec, crc):
    """
    'Frame' the encoded 124-bit payload and 16-bit CRC for transmission
    """
    
    PREAMBLE = 0xfaaaaaaa
    SYNC = 0x1234
    FOOTER = 0x110

    return (PREAMBLE<<168 |
            SYNC<<152 |
            fec<<28 |
            crc<<12 |
            FOOTER)

def pack(start=False, y=False, x=False, b=False, a=False, l=False, r=False,
         z=False, up=False, down=False, right=False, left=False,
         j_x=0x80, j_y=0x80, c_x=0x80, c_y=0x80, l_shoulder=0x00, r_shoulder=0x00):
    """
    Pack a raw WaveBird message given button states and axis values
    """

    MAGIC = 0x0bd5

    buttons = (start, y, x, b, a, l, r, z, up, down, right, left)
    button_map = sum(0x800>>i for i,pressed in enumerate(buttons) if pressed)

    return (MAGIC<<68 |
            button_map<<56 |
            j_x<<48 |
            j_y<<40 |
            c_x<<32 |
            c_y<<24 |
            l_shoulder<<16 |
            r_shoulder<<8)

parser = argparse.ArgumentParser(description='Write digital messages for WaveBird receivers')
for button in ['start', 'y', 'x', 'b', 'a', 'l', 'r', 'z', 'up', 'down', 'right', 'left']:
    flag = ('-' if len(button) == 1 else '--') + button
    parser.add_argument(flag, default=False, action='store_true', help='Simulate the "%s" button being pressed' % button.capitalize())

parser.add_argument('--jx', default=0.0, type=float, help='Joystick X position (-1 to 1)')
parser.add_argument('--jy', default=0.0, type=float, help='Joystick Y position (-1 to 1)')
parser.add_argument('--cx', default=0.0, type=float, help='C-Stick X position (-1 to 1)')
parser.add_argument('--cy', default=0.0, type=float, help='C-Stick Y position (-1 to 1)')
parser.add_argument('--laxis', type=float, help='L-shoulder depression (0 to 1)')
parser.add_argument('--raxis', type=float, help='R-shoulder depression (0 to 1)')

parser.add_argument('--output', default='full',
                    choices=('raw', 'interleaved', 'fec', 'crc', 'full'),
                    help="""\
How to encode the output.
'raw' - pack the button/axis values and print that in hex
'interleaved' - interleave the raw data for CRC (FEC uses its own interleave)
'crc' - give the correct CRC value (with XOR of 0xce98 applied)
'fec' - give the cyclic-encoded and FEC-interleaved message
'full' - give a fully framed message ready for modulation with `encode_wavebird.py`
""")

if __name__ == '__main__':
    args = parser.parse_args()

    args_dict = vars(args)

    args_dict['j_x'] = min(max(int((args_dict.pop('jx')/2 + 0.5) * 0xFF), 0), 0xFF)
    args_dict['j_y'] = min(max(int((args_dict.pop('jy')/2 + 0.5) * 0xFF), 0), 0xFF)
    args_dict['c_x'] = min(max(int((args_dict.pop('cx')/2 + 0.5) * 0xFF), 0), 0xFF)
    args_dict['c_y'] = min(max(int((args_dict.pop('cy')/2 + 0.5) * 0xFF), 0), 0xFF)

    # Default values for shoulders depends on button state
    l_default = 0xFF if args_dict['l'] else 0x00
    if args_dict['laxis'] is None: args_dict['laxis'] = l_default
    r_default = 0xFF if args_dict['r'] else 0x00
    if args_dict['raxis'] is None: args_dict['raxis'] = r_default

    args_dict['l_shoulder'] = min(max(int(args_dict.pop('laxis') * 0xFF), 0), 0xFF)
    args_dict['r_shoulder'] = min(max(int(args_dict.pop('raxis') * 0xFF), 0), 0xFF)

    output = args_dict.pop('output')

    raw = pack(**args_dict)
    interleaved = interleave(raw, 84)
    fec = fec_encode(raw)
    crc = crc16(interleaved) ^ 0xce98
    full = frame(fec, crc)
    if output == 'raw':
        print('%021x' % raw)
    elif output == 'interleaved':
        print('%021x' % interleaved)
    elif output == 'fec':
        print('%031x' % fec)
    elif output == 'crc':
        print('%04x' % crc)
    elif output == 'full':
        print('%050x' % full)
