Chapter 7: Specifications and Farewells
=======================================

Throughout this whole series, we worked through every layer necessary in
reverse-engineering the protocol used by Nintendo's WaveBird wireless GameCube
controller. And what an adventure it was! We had joy, we had fun, we had
seasons in the sun... And I really hope you found this as enjoyable to read as
it was to write. But our work is not done _quite_ yet.

Our last responsibility here is to explain what we figured out and put it out
there, so the great hackers of the 'net can use it in their amazing hacks.

So, let's get to it. From the top!

WaveBird protocol introduction
------------------------------

The WaveBird is an FM/FSK radio device operating in the 2.4GHz unlicensed band
of the radio spectrum. It transmits **250 messages per second**, encoding the
states of all 12 buttons and all 6 axes in each message. The WaveBird will
begin transmitting when it receives a user input, and will stop transmitting
when the user lets the controller return to its relaxed state. The
receiver/GameCube need not be in range for the WaveBird to transmit.

All integers are in big-endian, most-significant-bit-first order.

Input state messages
--------------------

An input state message is an 84-bit message, built like so:

0x0BD5**BBBXXYYCXCYLLRR**00

The 4 BBB nybbles are the button status, generated like so:

| Button nybble        | 8s bit | 4s bit | 2s bit  | 1s bit |
| -------------------- | ------ | ------ | ------- | ------ |
|  0 (first)           | Start  | Y      | X       | B      |
|  1                   | A      | L      | R       | Z      |
|  2                   | D-Up   | D-Down | D-Right | D-Left |

Where '1'=pressed and '0'=released

- **XX** is an 8-bit unsigned int representing the X position of the main joystick,
  `0x80` being approximately the resting position, increasing in value as the
  stick is pushed right
- **YY** is an 8-bit unsigned int representing the Y position of the main joystick,
  `0x80` being approximately the resting position, increasing in value as the
  stick is pushed up
- **CX** is the same as XX, but for the C-stick
- **CY** is the same as YY, but for the C-stick
- **LL** is an 8-bit unsigned int representing how pressed the left shoulder
  is, with `0x00` being approximately the resting position
- **RR** is the same but for the right shoulder

Composed all together, this is known as a "raw input message"

An example neutral "resting state" message is:
`0bd50007f7f7f7f000000`

CRC-16 check value
------------------

To compute the CRC-16 check value, first the raw message must be interleaved.
The interleaved input message is calculated by using a 21-bit-wide, 4-bit-high
array, writing the raw message into the array in left-to-right, top-to-bottom
order, then reading the interleaved message out in top-to-bottom, left-to-right
order.

The above example message, when interleaved, is `2202a2aaee4e6e6a66444`.

Next, the CRC-16 value is computed using the CCITT polynomial `0x1021` as
normal. The CRC-16 value must then be XORed with **0xce98**.

The correct transmitted CRC-16 check value is `1a20`.

Forward Error Correction
------------------------

Going back to the **raw** message, the 84 bits are split into 4 equal 21-bit
quarters, like so:

`AAAAAAAAAAAAAAAAAAAAA BBBBBBBBBBBBBBBBBBBBB CCCCCCCCCCCCCCCCCCCCC DDDDDDDDDDDDDDDDDDDDD`

Each of these quarters is _reversed_ and then passed through a (31,21)-cyclic
encoder, using the same polynomial as that used in POCSAG:
`g(x) = x^10 + x^9 + x^8 + x^6 + x^5 + x^3 + 1`

Each of the 31 cyclic-encoded codewords is interleaved as with the CRC input,
but with a 31-bit-wide instead of 21-bit-wide array.

In this example, the FEC-encoded message would be
`40460aa4ae2e22c4a4086cc28080022`.

Framing
-------

The FEC and CRC are framed into a 200-bit _frame_ like so:

0xFAAAAAAA1234**XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXYYYY**110

Where X is the FEC value, and Y is the CRC value computed above.

Continuing with our example:
`faaaaaaa123440460aa4ae2e22c4a4086cc280800221a20110`

Chipping
--------

Each bit (in left-to-right i.e. MSB-first order) is then mapped to one of two
14-chip sequences, each being the other's inverse:

- '1' -> `-+-++--+--++++`
- '0' -> `+-+--++-++----`

This means a full frame becomes 2800 chips.

Transmission
------------

Radio transmission uses frequency-shift keying (FSK).

Depending on the channel selection wheel, the WaveBird can have one of 16
different center frequencies for radio transmission:

| Channel | Frequency (MHz) |
| ------- | --------------- |
|       1 |         2479.2  |
|       2 |         2474.4  |
|       3 |         2404.8  |
|       4 |         2409.6  |
|       5 |         2419.2  |
|       6 |         2414.4  |
|       7 |         2424.0  |
|       8 |         2428.8  |
|       9 |         2438.4  |
|      10 |         2433.6  |
|      11 |         2445.6  |
|      12 |         2450.4  |
|      13 |         2460.0  |
|      14 |         2455.2  |
|      15 |         2464.8  |
|      16 |         2469.6  |

If you would prefer not to hardcode the table, the algorithm for calculating a
frequency for a given channel is provided in chapter 1 of this tutorial.

Messages are transmitted in 4ms periods, consisting of:
- 100 microseconds of unmodulated carrier
- The 2800 chips, transmitted at a rate of **1,344,000 chips/sec**, where a
  '+' chip is +500KHz off the center frequency, and a '-' chip is -500KHz.
- Silence (no carrier, transmitter apparently powered off) until the beginning
  of the next 4ms period.

Project ideas
-------------

In case someone out there wants to do something with this information but isn't
sure what, here are a few ideas for inspiration:

- Try to get this decoded with an RTL-SDR, which has a lower maximum sample
  rate
- Implement a SDR-based joystick/gamepad driver that uses the WaveBird
- [TASBot](http://tasvideos.org/TASBot.html)-like speedrunning with an actual
  GameCube, no electrical connections required
- TASBot-style game glitch exploitation and remote payload upload/execution
