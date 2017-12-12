#!/usr/bin/env python

# The buttons on the controller (in no particluar order)
BUTTONS = ['A', 'B', 'X', 'Y', 'START', 'Z', 'UP', 'DOWN', 'LEFT', 'RIGHT', 'L', 'R']

# Assign a bit to each button (just for this script's purposes)
BUTTON_MAP = {x: 1<<i for i,x in enumerate(BUTTONS)}
globals().update(BUTTON_MAP)

# The mode (most common) message for holding various combinations of buttons
MESSAGES = {
    START: 0x0002a64631175330f65e78a681a3233,
    Z: 0x44426ac6ec4b02f1e20928d19790611, 
    A: 0xccc2c2ecffeb30c2c07f6a969380211,
    A+B: 0xc44aca6c7fe330c2d16f7b979390211,
    A+X: 0xcc4a4260b2fef192c56e7b979390211,
    A+Y: 0xccca4ae03a7e7992c56e7b979390211,
    A+X+Y: 0xcc40c808553bff94c01b68b59390211,
    A+START: 0x88800c4c11a64121e75f78b791b2233,
    A+Z: 0x888084cc88af40b1e60b28f395b2633,
    B: 0x4cca6242384652a0f65c68959390211,
    B+X: 0x4c42e2ca2047c2b1e64d68959390211,
    B+Y: 0x4cc2ea4aa8c74ab1e74d79948291311,
    B+Z: 0x4cca6242295643a1f70839d08691711,
    X: 0x44caea4aa04fc2b1e74d79948291311,
    X+Y: 0x44c2624231dfdbb0f65c78848381211,
    X+START: 0x44ca62ca3957d330f65c78848381211,
    X+Z: 0x44caea4ab15fd3b0f61838c08781611,
    UP: 0x44426ac6ec4b02f1e6096cd5d394211,
    UP+A: 0xccc2e2ceeccb02f1e6096cd5d394211,
    UP+B: 0x088a06206a614691a0096cf5d1b6233,
    UP+Z: 0x44426ac2a84d4293e06f2eb1d794611,
    LEFT: 0x44426ac2a84f42f5b6087c84c381211,
    LEFT+UP: 0x44426ac2a84f42f5b24c78c48385211,
    LEFT+A: 0xccc2e2caa8cf42f5b7197d94d380211,
    LEFT+B: 0x4cca6242284742f5a24d68d59394211,
    LEFT+X: 0x44caea4ab15fd3f4e2592891d3d0211,
    LEFT+Z: 0x44426ac2a84d42d7a46f2ef1d790611,
    DOWN: 0x00000c84dc6a54a4b65a2cb391f2233,
    DOWN+START: 0x0000840445724525b64a2cb391f2233,
    DOWN+Z: 0x44426ac2a84f42b1a2496cd597d0611,
    DOWN+X: 0x44caea0ae40bc6b5a6492c9193d0211,
    DOWN+A: 0x8882a6cea88f42f5e24b28b3d1f2233,
    DOWN+LEFT: 0x00022ec6a80f42f5e24b28b3d1f2233,
    RIGHT: 0x00000cc4882f40b5a24b28f795b2233,
    RIGHT+DOWN: 0x00000c84cc6b44b1e24f6cf395f2233,
    RIGHT+UP: 0x00000c84cc6b44b1a24b2cb7d5b6233,
    RIGHT+Y: 0x000aa6ce288f4ab5a24b28f795b2233,
    RIGHT+Z: 0x44404880dd3b55b0a65968919390611,

    # Now for the shoulder buttons:
    L: 0x20200c84ee4964b5e21a2df6c5b7336,
    R: 0x00000c84cc6b54a4f30e2db2c0f2273,
    L+R: 0x20200c84fe4864b5e20f79e384e7267,
    L+START: 0x2020840477535736c33a2ef7d4a7327,
    L+DOWN: 0x20200c84ff5b57b6976b6ae2c4e7236,
    R+X: 0x00888c0cc568f6a6c22f3eb2d1e3373,
    R+A: 0x8880848ccceb54a4e31e2db2d1e3373,
    R+B: 0x088804045d7167a7c32e2fb2d1e3373,
}

# Include our decode function, modified to work on a SINGLE 31-bit block
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

# This deinterleaves the 124-bit block into 4x 31-bit
def deinterleave(x):
    a = b = c = d = 0

    for i in range(124):
        d |= (x & 1) << (i//4)
        x = x >> 1
        a, b, c, d = d, a, b, c

    return (a, b, c, d)

# And this does a full decode
def full_decode(x):
    a, b, c, d = deinterleave(x)

    return (cyclic_decode(a) << 63 |
            cyclic_decode(b) << 42 |
            cyclic_decode(c) << 21 | 
            cyclic_decode(d))

# Now find the difference masks for each button
BUTTON_MASKS = {}
for name, bit in BUTTON_MAP.items():
    masks = BUTTON_MASKS[name] = []

    for combination, codeword in MESSAGES.items():
        if combination & bit: continue

        other_codeword = MESSAGES.get(combination | bit)
        if not other_codeword: continue

        # It's a linear code, so we save time by doing this instead of
        # full_decode(codeword) ^ full_decode(other_codeword)
        mask = full_decode(codeword ^ other_codeword)
        masks.append(mask)

for name, masks in BUTTON_MASKS.items():
    if not masks: continue

    print('------- %5s -------' % name)
    common = ~0
    for mask in masks:
        print('%021x' % (mask))
        common &= mask
    print('-' * 21)
    print('%021x' % common)
    print('')
