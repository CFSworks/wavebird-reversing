Chapter 6: Error Detection and Correction
=========================================

Last time, we decoded a few WaveBird packets and found them to have about 140
bits of data each. This is a lot more than our expected 60. Where is that
coming from?

If you ask a gamer to name the top 3 controller frustrations, they'll probably
say:
1. The controller breaking down, buttons not working, etc.
2. The controller registering inputs (e.g. button presses) falsely.
3. Controller lag.

We can't do much about #1. That's usually from the batteries dying or a
physical switch failing from over(ab)use. Nintendo probably solved that by
sourcing high-quality parts rated for the kind of stress some gamers can
put on their controllers.

However, #2 can be caused by mistakes in the demodulator/decoder. A flash of
interference might strike at the worst possible time, flipping a bit that
represents a controller button. And if that controller button happens to be,
say, the "use powerup" button, the controller might end up inside the broken
glass of somebody's TV set.

With this in mind, we can reason that the extra bits are most likely
_redundancy_ added by error detection/correction codes, so that if interference
does strike at the worst possible time, the WaveBird receiver won't blindly
accept the error and mess up someone's perfect Mario Kart driving.

(If you've ever looked at an FCC Part 15 disclaimer, you may remember that it
says "this device must accept any interference received, including interference
that may cause undesired operation" and think "Wait, it has to _accept any_
interference? Doesn't that ban error detection?" Actually, no. Their use of the
word "accept" is really confusing, since they don't mean it in a technical
sense, but rather a legal one: If there's interference messing up your
controller, you have no legal recourse. I digress, but it perplexed me when I
first saw it too, so I figured I'd clear that up.)

So, by being able to detect errors, the WaveBird receiver can just ignore the
packet and wait for the next transmission in about 4ms. This is great, except
we have to remember point #3: Gamers hate lag. Therefore, rather than merely
_detect_ the error, it'd be better if the receiver could figure out where the
error happened and _correct_ it, thereby repairing a message that would
otherwise have to be thrown out.

In this chapter, we'll explore various techniques and codes used to detect and
correct transmission errors. I should note that this is the part where I'm in a
little over my head, but I'll do my best to tell you what I know.

What are transmission errors?
-----------------------------

There are 3 types of errors that can happen to a bit:

- Bit error: A bit is silently flipped; a '0' is received as a '1' or a '1' is
  received as a '0'.
- Bit erasure: This is where a bit is "erased;" the receiver can't be
  confident whether it's supposed to be a '1' or a '0', so it leaves an empty
  space instead.
- Bit deletion: This is similar to bit erasure, but the receiver isn't even
  aware it missed a bit. The bit is simply skipped.

An astute reader may ask, "What about transposition errors?" Transposition
errors are what happens when the order of two consecutive bits/letters/symbols
is switched, and you end up with mistakes like "transpositoin." We're not
concerned about those, for 3 reasons:

1. These are mostly common when bits/letters/symbols are arriving by multiple
   paths and reassembled. For example, they're pretty common when typing on
   a keyboard because the timing of one finger may be slightly delayed and end
   up typing a letter later than it should appear. Our radio beam doesn't
   really have a way for a bit to "get in front of" an earlier bit.
2. If the two bits being transposed happen to be the same, then no error has
   actually occurred. If I switched the Rs, Ls, and/or Cs in "error," "actually,"
   and "occurred," there'd be no difference.
3. If the two bits being transposed happen to be different, then this is really
   just two consecutive bit errors.

And as long as we're reducing problems by turning them into other problems, we
can actually handle an erasure by 50-50 guess. 50% of the time we guess right
and the error is gone, the other 50% of the time it turns into a bit error
instead. (The decoder we wrote in the last chapter just tries its best to guess
the bit in case nothing stands out clearly.)

We also don't have to worry about bit deletion because we know the expected
timing for each bit; if nothing stands out strongly enough during the expected
interval, we treat it like an erasure. (Indeed, our decoder does this as well.)

So, since we only have to guard against bit _error_ (i.e. bits being flipped),
let's look at ways to combat that!

Error detection
---------------

Error detection works by adding a little extra information to provide some
degree of assurance that an error has _not_ occurred. (I say "some degree of
assurance" because, theoretically, the right combination of errors could still
go undetected.)

If you'd like to see this in action, pick up anything sold in U.S. stores
and look for the 12-digit UPC barcode on the back/bottom of the box. Sum the
first, third, fifth, seventh, ninth, and eleventh digits (i.e. the ones in
odd-numbered places), multiply by 3, then add in the remaining digits. You will
always end up with a number divisible by 10. This is because the UPC standard
dictates that the last digit must be calculated to ensure this property. The
last digit is the "check digit," and serves as a way of catching some
circumstances where a scanner might misread, or a cashier might mistype, the
UPC number. (It can detect any single digit being misread/mistyped, and can
detect about 90% of transposition errors thanks to the odd digits being
multiplied by 3.) This could also be used as a magic trick: Tell your friends
you can read their minds, have them pick any barcode and do the above math, then
dramatically reveal that you know they're thinking of a multiple of 10. I
guarantee that this will convince them that you're especially strange.

In binary land, the simplest form of error detection is what's known as a
_parity bit_. When this is used, every so often (perhaps only once per message,
or once after every block of bits) a bit is added that is '1' if there were an
odd number of '1's before it, or '0' if there were an even number. (Which means
that, including the parity bit, there will _always_ be an even number of '1's)

This detects any single-bit error, because any bit being flipped will change
the parity (odd '1's becomes even '1's and vice versa) and invalidate the
parity bit. If the parity bit itself suffers the error, then the outcome is
the same: the parity bit is wrong, and the bit error is detected.

The weakness to the parity bit is that two bit errors at once will come back
around and make the parity bit valid again. This makes it a fairly unpopular
check scheme except in circumstances where single-bit errors are so rare that a
double-bit error is practically unheard of. Engineers usually prefer error
detection algorithms with stronger guarantees.

One option is to interpret the message as an array of integers, and include a
sum at the end. For example, the internet's own TCP/IP uses 16-bit checksums,
which can detect any 16-bit errors in a row.

Another good option is to use a _cyclic redundancy check_ code, which basically
sweeps a sequence across the bit string, XORs it in wherever it sees a '1', and
appends whatever's left over. These can detect any single-bit, double-bit (and
sometimes triple-bit) errors over very long block lengths.

Forward Error Correction (FEC)
------------------------------

Error detection is good enough for rejecting corrupt packets and waiting for
valid retransmissions to arrive, but as we discussed above, we may not want to
wait for a valid retransmission when the errors may be minor enough that we can
just fix them ourselves.

This is where we get even more proactive and start using error _correction_. If
the redundant check information helps a receiver not only identify that there is
an error, but solve for _where the error happened_, it can just flip the bit
back itself and carry on with its day.

You've probably seen this in action yourself without even realizing it, every
time you came across a QR code with a logo in the middle. There isn't any magic
to that - you can make them yourself by using your QR code generator's highest
forward error correction setting, then just stamping the logo in the center. As
long as the logo isn't _too_ large, the QR scanner's FEC decoder will simply
see the logo as one massive blob of error in the center and correct it to
produce a good scan.

And now for a whole bunch of terminology:

It's called _forward_ error correction because it requires the sender to
convert the message into a sequence of **codewords**, each decodable back to the
original message. The coding generally works on blocks of a fixed size - called
its **message length**, producing codewords of an even larger fixed size,
called its **block length**.

If every bit of the original message is found somewhere in the encoded
codeword, the code is said to be **systematic**. Systematic codes are convenient
for receivers not wishing to implement error correction; they can simply delete
the redundant bits to get the original message back - although in so doing they
lose the protections the FEC code would otherwise guarantee, essentially
_assuming_ there's no error. But if the original bits do not appear, and the
only way to reconstruct the original message is to decode it, the error
correction code is **non-systematic**.

If the XOR of two codewords is also a valid codeword, the code is called
**linear**. This is convenient for lazy engineers who need to implement a FEC
encoder: they can just precalculate the codewords for all 1-bit-set messages,
and have their encoder selectively combine them with XOR as needed.

There are two key factors in determining the _performance_ of an
error-correcting code. The first is its **rate**, which is simply the message
length divided by the block length. This answers the question of how much of a
throughput impact the addition of the code will have.

The second performance factor is its **minimum Hamming distance** (or simply
**distance**). Put succinctly, this is a measure of how different the two most
similar codewords are. It's important because it tells you the bit error
tolerance of a code. To reliably _detect_ a single-bit error, the distance must
be at least 2. (A distance of 1 would mean the existance of two codewords that
differed by only one bit, meaning a single-bit error could turn a valid
codeword into another valid codeword, and detection of any single-bit error is
not guaranteed.) To reliably _correct_ a single-bit error, the distance must be
at least 3. (Since that means an invalid block with a single-bit error differs
from the nearest valid codeword by a distance of only 1! If the distance was 2,
there could be two or more equally-nearest valid codewords.) In general, a FEC
code can detect n bit errors if its distance is at least d=n+1, and can correct
k bit errors if its distance is at least d=2k+1.

Let's look at an example. The simplest FEC code is the (3,1)-repetition code.
The (3,1) is shorthand for a block length of 3 and a message length of 1. It
consists of repeating each bit 3 times. Put another way, it's a block code with
2 valid codewords: '000' and '111'.

Because the original bit _definitely_ appears at least once in each codeword,
it's systematic. Because you can XOR them in any combination and get another
(ahem, either) valid codeword, it's linear. Its rate is 1/3, which makes it a
pretty inefficient code from a speed standpoint. Its distance is 3, since the
two most similar (ahem, only two) codewords differ in 3 places.

Since it has a distance of at least 3, it's tolerant of any single-bit error.
If you receive '110', you know the most similar codeword is '111'. And because
its distance is at least 3, it can detect a double-bit error, so if I change
'000' to '011' and ask "Did an error occur?" you can say "Yes." but you would
recover the wrong original bit.

One last thing to mention: When encoding more data than the message length of
an error correcting code by using multiple blocks, it can be tempting just to
stick the codewords one after another. For example, to encode '101' using the
(3,1)-repetition code as '111000111'. This is easy, but the drawback is that
multiple bit errors tend to occur in bursts, so interference may strike, flip a
few bits in a row, and we'd end up with '11**011**0111', which improperly
decodes to '111' because it violates the single-bit guarantee in the middle
code. To combat this, we can **interleave** the multiple blocks together,
writing out one bit from each block at a time, in '123123123' order instead of
'111222333' order. The result is '101' gets encoded as '111000111' and
interleaved as '101101101'. Now if the same burst of interference hits, we get
'10**001**1101', which deinterleaves to '1**0**10**1**0**0**11', spreading the
error so there's only a single-bit flip per block.

But enough chit-chat: How are these techniques used in the WaveBird???

Experiment: Determining how much of a WaveBird packet is FEC
------------------------------------------------------------

The WaveBird might use all FEC, or no FEC and all of the extra data is a check
value, or some mixture of both.

My hypothesis, from looking at the message specimens in the last chapter, is
that there are 124 bits of FEC-protected data, followed by a 16-bit check
value. If we look at our Z-button example:

faaaaaaa1234**44426ac6ec4b02f1e20928d197906116382**110

We can see that there's a nice repeating sequence for the first 124 bits
(444...611) but the last 16 bits just "feel" more random. In fact, every
message is like this. The "FEC" part ends with a nice 211/233/611/311 pattern,
and the next 16 bits break that.

Because the FEC region should be tolerant of a single-bit error, but the check
value should not, we could conduct an experiment to see if this is correct: Try
a few single-bit errors in each section of the message and see what the
GameCube will accept.

This is being done with the script and HackRF transfer command from the last
chapter:

| What is being flipped    | Message transmitted from HackRF                        | Accepted? | Remarks                                       |
| ------------------------ | ------------------------------------------------------ | --------- | --------------------------------------------- |
| Nothing                  | faaaaaaa123444426ac6ec4b02f1e20928d197906116382110     | **yes**   | Just a sanity-check; nothing surprising here  |
| First bit of preamble    | **7**aaaaaaa123444426ac6ec4b02f1e20928d197906116382110 | **yes**   | Most of preamble probably ignored?            |
| Last bit of preamble     | faaaaaa**b**123444426ac6ec4b02f1e20928d197906116382110 | **yes**   | Preamble is for timing purposes, data ignored |
| First bit of syncword    | faaaaaaa**9**23444426ac6ec4b02f1e20928d197906116382110 | no        | Sync word necessary for start of message...   |
| Last bit of syncword     | faaaaaaa123**5**44426ac6ec4b02f1e20928d197906116382110 | no        | ...and understandably very sensitive to error |
| First bit of FEC data    | faaaaaaa1234**c**4426ac6ec4b02f1e20928d197906116382110 | **yes**   | FEC doing what it does best - corrects error  |
| Second bit of FEC data   | faaaaaaa1234**0**4426ac6ec4b02f1e20928d197906116382110 | **yes**   | Go FEC go!                                    |
| Last bit of FEC data     | faaaaaaa123444426ac6ec4b02f1e20928d1979061**0**6382110 | **yes**   | We're still in the FEC range                  |
| First bit of check value | faaaaaaa123444426ac6ec4b02f1e20928d19790611**e**382110 | no        | We changed the check value, it cries "error"  |
| Last bit of check value  | faaaaaaa123444426ac6ec4b02f1e20928d19790611638**3**110 | no        | It still believes the whole thing is corrupt  |
| First bit of footer      | faaaaaaa123444426ac6ec4b02f1e20928d197906116382**9**10 | **yes**   | No longer in the check value...               |
| Last bit of footer       | faaaaaaa123444426ac6ec4b02f1e20928d19790611638211**1** | **yes**   | ...but what is this "footer"'s purpose???     |

Although this has just left me with some fair amount of confusion about what
that footer really is for, it does confirm something about how Nintendo
engineered the error checking: The 124 bits in the middle are the most likely
target for random bit error, so that's the part they were most sure to guard
with error correction. The 16-bit check value immediately afterward is a
last-ditch effort. Presumably it's computed against the inner message, so if
the error correction fails, it can still be identified as corrupt and rejected.

We'll come back to the 16-bit check value later, but for now, we really need to
know how that 124-bit code works.

WaveBird's FEC: Is it systematic?
---------------------------------

As we recall, if a FEC is _systematic_ it means every original bit appears
somewhere, unmodified, in the codeword. So, if the WaveBird's FEC is
systematic, there should be some bit that is 1 whenever a given button (say,
'B') is held, and 0 otherwise.

We can check with some interactive Python:
```
>>> start = 0x0002a64631175330f65e78a681a3233
>>> a = 0xccc2c2ecffeb30c2c07f6a969380211
>>> b = 0x4cca6242384652a0f65c68959390211
>>> ab = 0xc44aca6c7fe330c2d16f7b979390211
>>> ax = 0xcc4a4260b2fef192c56e7b979390211
>>> by = 0x4cc2ea4aa8c74ab1e74d79948291311
>>> bz = 0x4cca6242295643a1f70839d08691711
>>> axy = 0xcc40c808553bff94c01b68b59390211
>>> z = 0x44426ac6ec4b02f1e20928d19790611
>>> 
>>> ~start&~a&b&ab&~ax&by&bz&~axy&~z
0L
```

Hm. No. But what if it uses '0' for pressed and '1' for released?
```
>>> start&a&~b&~ab&ax&~by&~bz&axy&z
0L
```

So, no, **the WaveBird's FEC is non-systematic**.

WaveBird's FEC: What's its distance?
------------------------------------

We know the distance is the number of bit places that differ in the two most
similar codewords. So to answer this question, we need a sizable dataset of
valid codewords just to determine what the two most similar codewords _are_.

To that end, I've captured a 2-minute recording of myself ~~demonstrating my
impeccable Super Smash Bros. Melee technique~~ mashing random buttons and
moving the sticks around wildly. (Rather than fill up GitHub's
probably-not-so-scarce server space with the .iq file, I have instead included
the output when analyzed by `decode_wavebird.py` as `button_mashing.log.bz2`)

What we then need to do is take the output, somehow filter out any one-off
errors, then check the Hamming distances of all valid codewords against each
other, and report the closest two and their distance.

This means we need another script - so without further ado, onward to
`find_hamming_distance.py`!

...

Upon running it (and it takes a while to run, because it compares every valid
codeword against every other valid codeword), we get this output:
```
Minimum distance: 5
Closest two codewords:
0x80088c0c5df355b5b74b2cb291f2333L
0x80088c0c4df245b5b74b2db281f2333L
```

Note that there may be (and probably are) multiple "closest two codewords" but
the script just picks any two and shows us. But that's beside the point. The
interesting takeaway from all of this is that _whatever FEC algorithm the
WaveBird is using has a distance of 5_.

This also lets us calculate its bit-error tolerance as **2**. The 124-bit FEC
region in the center of the message can withstand _any_ double-bit error and
the receiver will be able to recover it correctly.

WaveBird's FEC: Is it linear?
-----------------------------

I'm not really well-versed enough in error correcting codes myself to give a
good explanation of how to determine this. But since most block FECs are linear,
it's a fair cop we can say "probably" and backtrack if we hit a dead end.

Linear codes basically hold the property:
`encode(a) ^ encode(b) = encode(a ^ b)`

So if we take the two above codewords from our distance-finding script and XOR
them, we get:
```
  0x80088c0c5df355b5b74b2cb291f2333
^ 0x80088c0c4df245b5b74b2db281f2333
-----------------------------------
  0x0000000010011000000001001000000
```

Which should itself be another valid codeword of the-- whoa whoa whoa, wait a
second.
`0x0000000010011000000001001000000` ... that _is_ hexadecimal, right? All of
the bit differences are on the 1s bit. That's funny. Hmm.

Well, whatever, maybe it's nothing. Let's try it on something else.
How about the "A button" and "A + B button" codes from the last chapter?
Because the raw messages should only differ by whatever bit represents the B
button state (but might have other things like noise from the analog sticks),
the XOR of those two codewords should be the codeword for just the B button.

Let's try that:
```
  0xccc2c2ecffeb30c2c07f6a969380211
^ 0xc44aca6c7fe330c2d16f7b979390211
-----------------------------------
  0x0888088080080000111011010010000
```

What.

What's really interesting is I'm seeing the same exact AAABAABABBA pattern
repeating twice here, once affecting the 8s bits, the second time affecting the
1s bits.

In fact...
`0x10011000000001001 = 0x11101101001<<24 ^ 0x11101101001<<20 ^ 0x11101101001`
...it's the same thing just XORed with different bit shifts!

Hold on, I think I need to take a second crack at the section heading:

WaveBird's FEC: Is it _cyclic_?
-------------------------------

Cyclic codes are a kind of linear code where not only the XOR operation is
preserved, but the bit-shift operation is preserved as well. So:
`encode(a) << 1 = encode(a << 1)`

Remember how I said lazy engineers love linear codes because they can just
precompute a table of all 1-bit-set codewords and selectively XOR them together
as necessary? That precomputed table is called the _generator matrix_, because
the "selective XORing" process resembles matrix multiplication.

In a cyclic code, because all rows in the generator matrix are bitshifts of
each other, an entire matrix isn't even necessary! The lazy engineer only needs
to calculate the code for '1' and that's it. This precomputed code is called
the _generator polynomial_, because the bit-shifting resembles multiplying a
polynomial by its variable (since each coefficient/bit shifts to a higher term),
and so the "selective XORing with each bitshift" resembles what happens to the
coefficients when multiplying two polynomials.

If this is a cyclic code, our generator polynomial will be {11101101001}, and
every codeword is generated by shifting-and-XORing that one sequence over and
over.

Let's implement a function in Python to encode a codeword with this cyclic
code:
```
def cyclic_encode(x):
    g = 0x11101101001

    codeword = 0
    for i in range(84): # 124 minus the 40 extra bits added by 'g'
        codeword <<= 1

        if x&1:
            codeword ^= g

        x >>= 1

    return codeword
```

So if we test it out:
```
>>> hex(cyclic_encode(0x80000000000000010))
'0x888088080080000111011010010000L'
```

Well that definitely explains where that codeword came from...

Let's try a decoder. Note that we're not really concerned about error
correction here, so I'm giving this an assert statement that just blows up if
there's anything left in the codeword after XORing out all the bitshifts of the
polynomial we can.

```
def cyclic_decode(x):
    g = 0x11101101001

    msg = 0
    for i in range(84): # 124 minus the 40 extra bits added by 'g'
        msg <<= 1
        if x&1:
            x ^= g
            msg |= 1
        x >>= 1

    assert x == 0 # Ensure everything got cleared (i.e. no bit errors)

    return msg
```

Now to test it out:
```
>>> cyclic_decode(cyclic_encode(1))
1
>>> cyclic_decode(cyclic_encode(200))
200
>>> cyclic_decode(cyclic_encode(1337))
1337
>>> cyclic_decode(cyclic_encode(1337)^0x400)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "<string>", line 13, in cyclic_decode
AssertionError
```

Nice. So we have a function which can, in essence, perform error detection on
this cyclic code. Which means if we're correct about this being a cyclic code,
valid WaveBird codewords should be treated as valid by this function too.
(Alas, I'm not well-versed enough in cyclic codes to do error _correction_, so
I'll just settle for error _detection_ and leave error correction as an
exercise to the reader.)

Let's see:
```
>>> hex(cyclic_decode(0x0002a64631175330f65e78a681a3233)) # 'start' held
'0xcc409017d943810314000L'
>>> hex(cyclic_decode(0x4cca6242295643a1f70839d08691711)) # 'b' + 'z' held
'0x88e01017d94b010304012L'
>>> hex(cyclic_decode(0x0000000010011000000001001000000)) # from our XOR above
'0x800008800000000'
```

I think that settles it. It's a cyclic code.

Another way to write out the generator polynomial {11101101001} is as an
_actual_ polynomial, since the '1's and '0's just represent the coefficients of
each term:
`g(x) = x^10 + x^9 + x^8 + x^6 + x^5 + x^3 + 1`

And if we do some background searching, we find this exact generator polynomial
used in [an old protocol for pagers](https://en.wikipedia.org/wiki/POCSAG#How_it_works).
Huh. I wonder if Nintendo hired somebody who had a background in the pager
industry?

According to the Wikipedia article, the POCSAG code has a minimum Hamming
distance of 6, not the 5 that we're seeing. But that's probably because of the
addition of the extra parity bit, which the WaveBird doesn't have.

The POCSAG code is a (31, 21) code, which encodes 21-bit message blocks with
31-bit codewords. Hm. The FEC we're seeing runs on 124-bit codewords, which is
4x as much... Except because the 8s bits, 4s bits, 2s bits, and 1s bits are all
independent of each other, another way to say this is:

**The WaveBird uses 4 POCSAG-style (31,21) cyclic codes interleaved together.**

This interleaving makes it even more resistant against bursts of error than
just double-bit flips. It can withstand up to 8 bit errors _in a row_ because
the interleaving will spread it out to 2 bit errors per cyclic code block.

Because it's 4 block codes encoding 21 bits each, we're now down to 84 bits of
raw data.

Making sense of the raw, decoded data
-------------------------------------

Since it makes sense to keep checking buttons, I've pressed a bunch of
combinations of buttons and recorded the resulting codewords in
`analyze_buttons.py`, which also decodes each cyclic code, XORs them against
codes which differ by one button, and ANDs all of the difference masks to try
to find the common bit for each button.

Running it tells us that there's pretty consistently one bit that flips for
each button:
| Button      | Bits that always flip when button is toggled |
| ----------- | -------------------------------------------- |
| Start       | 000080000000000000000                        |
| Y           | 000040000000000000000                        |
| X           | 000020000000000000000                        |
| B           | 000010000000000000000                        |
| A           | 000008000000000000000                        |
| Shoulder L  | 000004000000000e00000                        |
| Shoulder R  | 00000200000000000f000                        |
| Z           | 000001000000000000000                        |
| D-Pad Up    | 000000800000000000000                        |
| D-Pad Down  | 000000400000000000000                        |
| D-Pad Right | 000000200000000000000                        |
| D-Pad Left  | 000000100000000000000                        |

So it seems like the 12 bits in the `0000FFF00000000000000` part of the message
encode the states of the 12 buttons.

The shoulder buttons have some extra bits that flip later in the message when
pressed, but those are _most likely_ from the analog axes from the shoulders
themselves, which gives us some clues about where the 6 analog axes are kept.

Since we know what bits _flip_ when buttons are manipulated, we should also
figure out whether '1'=pressed and '0'=released, or vice versa. To do that,
we'll just decode the R+A message and see for ourselves:
```
>>> r_a = 0x8880848ccceb54a4e31e2db2d1e3373
>>> '%021x' % full_decode(r_a)
'0bd50a0878386801de800'
```

So the button bits are `000010100000` - the 'A' bit is '1', the 'R' bit is '1',
and the rest are '0'. So '1'=pressed.

Looking at the following bytes in the message we see: `87 83 86 80 1d e8 00`

Since the analog sticks are all in neutral positions, and 0x80-0x87 are close
to the middle of the range of an unsigned 8-bit integer, those are probably the
analog stick and C-stick axes. The R shoulder is pressed, so it makes sense for
the R shoulder value to be much higher than the L shoulder value.

Let's try manipulating each axis to see what we can decode:
```
>>> '%021x' % full_decode(0x04440880886f44f1e64b0e93b3b0231) # Stick left
'0bd5000228986801a1800'
>>> '%021x' % full_decode(0x044408c0882f04b1a60b2cf791b2233) # Stick right
'0bd5000f98b86801a1800'
>>> '%021x' % full_decode(0x440008c4886f00b5e20d4ab5b192213) # Stick up
'0bd50008ef686801a1800'
>>> '%021x' % full_decode(0x00044cc0cc6f40f1e60b4a97b3b0231) # Stick down
'0bd5000852186801a1800'
>>> '%021x' % full_decode(0x44424aa0ee296497c0296897b1b0011) # C-Stick left
'0bd50008784287f1a1800'
>>> '%021x' % full_decode(0x00002ea4ee6b64b5e0096a97b190233) # C-Stick right
'0bd50008783e3821a1800'
>>> '%021x' % full_decode(0x00020ea4cc6b4697e00968b791b2233) # C-Stick up
'0bd5000878386df1a1800'
>>> '%021x' % full_decode(0x444248a2ec0b6695c22b48b59390211) # C-Stick down
'0bd5000878484231a1800'
>>> '%021x' % full_decode(0x20200c84ee4964b5e21a2df6c5b7336) # L shoulder
'0bd504087838680ee1800'
>>> '%021x' % full_decode(0x00000c84cc6b54a4f30e2db2c0f2273) # R shoulder
'0bd5020878386801ae800'
```

So, the structure of the message is:

- **0bd5**: This is probably a fixed "magic number" to serve as one final check
  against error. (Who knows, maybe someone's initials? B.D.S.?) (16-bit)
- **Buttons**: '1' for pressed, '0' for released. Order of the buttons is:
  Start, Y, X, B, A, L, R, Z, Up, Down, Right, Left (12-bit)
- **Main stick X axis**: Increasing left-to-right, center is approx. 0x80 (8-bit)
- **Main stick Y axis**: Increasing bottom-to-top, center is approx. 0x80 (8-bit)
- **C-Stick X axis**: Increasing left-to-right, center is approx. 0x80 (8-bit)
- **C-Stick Y axis**: Increasing bottom-to-top, center is approx. 0x80 (8-bit)
- **Left shoulder value**: Increasing as the button is pressed (8-bit)
- **Right shoulder value**: Increasing as the button is pressed (8-bit)
- **00**: Zero bits to pad to a multiple of 21 for the FEC encoding (8-bit)

Excluding the padding and magic number, that's exactly 60 bits. We've found our
data!

What's interesting is this ordering is [exactly the same as that used in the
wired GameCube controller](http://www.int03.co.uk/crema/hardware/gamecube/gc-control.htm)
(albeit with the padding bits in different places),
which makes sense because the WaveBird receiver must speak that protocol, so
why make the receiver have to reorder it?

Figuring out the check value
----------------------------

(FAIR WARNING: I wrote this section as I was figuring it out myself; as such, I
might not be explaining things in a very intuitive way. If you think you can
help, send in a pull request!)

If our goal was just to decode WaveBird signals, we could ignore the check
value at the end and rely on the cyclic code for error detection, and we'd be
done by now. However, if we wanted to be able to produce our own WaveBird
signals that the genuine Nintendo receiver would accept, we have to figure out
how to compute proper check values.

I suspect that these are _probably_ cyclic redundancy checks. Not only is the
CRC a popular choice for this sort of work, but it's probably what our WaveBird
engineer would've chosen given the fact that it's also a very close relative
of the _cyclic FEC_ we've been using so far. They both have a "generator
polynomial." But to compute a cyclic FEC, you multiply by the polynomial. To
compute a CRC, you divide by the polynomial and use the remainder as your CRC.

Believe it or not, we've already been doing polynomial division. Our cyclic FEC
decoder, which reverses the process of multiplying by the FEC's generator
polynomial, is actually dividing by the polynomial. That "line up the divisor
(actually the generator polynomial) with each digit (actually bit) in the
dividend (actually encoded message), subtract (actually XOR) it out, and repeat
to build up a quotient (actually decoded message) and remainder (which should
be 0 if there are no errors)" process we've been using in our `cyclic_decode`
function is _the very same_ process you were taught in your elementary school
long division assignments. Just with polynomials instead of numbers, and bits
instead of digits.

The difference is just that our `cyclic_decode` computes the quotient, and a
non-zero remainder causes it to throw an assertion error. In a CRC, the
remainder is what we _want_. Wikipedia gives a [fantastic illustration of how
this works](https://en.wikipedia.org/wiki/Cyclic_redundancy_check#Computation):
First right-pad with enough zeroes to hold the remainder, then do the usual
division process we're used to... easy as that.

There's another, alternative but equivalent way of thinking about it: Instead
of XORing the polynomial into the _data_, then moving along and using any '1's
remaining in the data (which indicate where the data stream isn't at parity
with the polynomials XORed in previously) as indicators of where else to XOR
in the polynomial, some implementations use a shift register (of the same width
as the polynomial) and shift bits out of that. Wherever the bit coming out
of the shift register (representing the XOR of all polynomials up to that
point) disagrees with the data, the polynomial is XORed into the
shift register (instead of into the data). Then the CRC is whatever remains in
the shift register after this process has been repeated for each data bit.

The latter implementation is simpler, because it doesn't use the data as
scratch space. That means it doesn't have to make a copy of the entire data
buffer and doesn't need all of the data available at once (i.e. it can compute
the CRC of a stream). It also only needs as much memory as necessary to hold
the CRC/polynomial. If you'd like to compare, here's a pair of CRC
functions (each behaving exactly the same) in Python using both techniques.

```
def crc_long_division(data, poly, n):
    """
    Compute the CRC-N of 'data' over polynomial 'poly' of bit length N,
    using the long-division method.

    The representation of 'poly' leaves out the highest term which is
    always understood to be there.
    """

    assert poly.bit_length() <= n

    # Pad data for remainder
    data <<= n

    for bit in range(data.bit_length()-1, n-1, -1):
        if data & (1<<bit):
            data ^= poly<<(bit-n)

    return data & ((1<<n) - 1)

def crc_shift_register(data, poly, n):
    """
    Compute the CRC-N of 'data' over polynomial 'poly' of bit length N,
    using a shift register.

    The representation of 'poly' leaves out the highest term which is
    always understood to be there.
    """

    assert poly.bit_length() <= n

    shift_reg = 0

    for i in range(data.bit_length()-1, -1, -1):
        # Get the next bit from 'data'
        bit = (data>>i)&1

        # Shift a bit out of the shift register (right-hand side)
        shift_reg <<= 1
        sr_bit = (shift_reg>>n)&1
        shift_reg &= (1<<n) - 1

        # If these two bits disagree, throw the polynomial into the register
        if bit ^ sr_bit:
            shift_reg ^= poly

    # What's left in the shift register at the end of this process is the CRC
    return shift_reg
```

Again, you can use either of these functions. They behave in the exact same
way, because they actually do the same XORs. The difference is merely in where
they make note of where the polynomials have been XORed in.

With that out of the way, let's get down to figuring out how to figure out the
CRC. I'd like to heavily draw upon [this fantastic article by Gregory
Ewing](http://www.cosc.canterbury.ac.nz/greg.ewing/essays/CRC-Reverse-Engineering.html)
since it explains the sorts of problems we're up against.

Greg points out that a CRC may have a "XorIn" and "XorOut" value - nonzero
values used to initialize the shift register and XOR against the CRC at the end,
respectively. This complicates things for us, because now we can't just
brute-force the polynomial and call it a day. He does, however, point out this
very interesting property of CRCs:

```
Because the whole CRC algorithm is based on exclusive-or operations, CRCs obey
a kind of superposition principle. You can think of the CRC as being made up of
the exclusive-or of a set of component CRCs, each of which depends on just one
bit in the message.
```

This means CRCs are also linear! Nice!!! Greg also points out the secret to
eliminating the XorIn/XorOut components is to exploit this linearity, analyzing
the CRC of the _XOR of two messages_, which is itself given by the XOR of their
CRCs. In other words, `crc(msg1 ^ msg2) = crc(msg1) ^ crc(msg2)`. Well, we
still have my button-mashing log, so we've got plenty of `msg` and `crc(msg)`
values to work with.

So, since we want a bunch of one-bit messages to work with, let's write a
script to harvest them from the button-mashing log... On to
`find_crc_messages.py`!

...

Running this script gives us a bunch of great candidates. In particular, every
one of the button bits has its contribution to the final CRC value printed out,
and best of all these candidates are all free of any XorIn/XorOut influence!

Greg predicts that in long runs like this, we should see consecutive CRC values
differing by either:
1. A bit-shift in which a zero bit is shifted out.
2. A bit-shift in which a one is shifted out XORed with the polynomial.

While neither of these happens in our candidates, we do see this suspicious
pattern with CRCs beginning with zero:
```
crc(000000000000000000200) = 045a
crc(000000000000000000400) = 45a0
...
crc(000000000000001000000) = 06e6
crc(000000000000002000000) = 6e60
...
crc(000000100000000000000) = 0f6d
crc(000000200000000000000) = f6d0
```

Because we're shifting not by _one_ bit but by _four_, there's some
interleaving being applied to the raw message prior to CRC!

I haven't the foggiest idea _why_ anyone would want to interleave their CRC.
Maybe Nintendo interleaves the message first, then computes the CRC, then feeds
it to the cyclic encoder?
Is there any kind of (perceived) benefit to doing this? Beats me.

Either way, to get the polynomial, we need to interleave our messages before
they hit the CRC. I have a line commented out in the `find_crc_messages.py`
script which applies an 84-bit version of the interleaving to `msg_difference`;
go uncomment that now and rerun the script.

The output only finds a couple of contiguous messages, but it's still enough
for our purposes:
```
crc(000000000100000000000) = 1a84
crc(000000000200000000000) = 3508

crc(000000001000000000000) = b861
crc(000000002000000000000) = 60e3

crc(000000010000000000000) = 377b
crc(000000020000000000000) = 6ef6
...
crc(020000000000000000000) = 390d
crc(040000000000000000000) = 721a

crc(200000000000000000000) = a0b3
crc(400000000000000000000) = 5147
```

This works _exactly_ like what Greg encountered: If the highest bit is 0, then
an extra shift-xor operation would just left-shift one place, since it would
shift-out a '0' which doesn't disagree with the padding '0' bits in our (sparse)
messages.

```
>>> hex(0x1a84<<1)
'0x3508'
>>> hex(0x377b<<1)
'0x6ef6'
>>> hex(0x390d<<1)
'0x721a
```

But if the highest bit is a '1', oh ho ho, a '1' gets shifted out and
that prompts the polynomial to get XORed in:

```
>>> hex((0xb861<<1)&0xFFFF ^ 0x60e3)
'0x1021'
>>> hex((0xa0b3<<1)&0xFFFF ^ 0x5147)
'0x1021'
```

`0x1021` corresponds to the polynomial:
`g(x) = x^16 + x^12 + x^5 + 1`

...which is the **CRC-CCITT** polynomial!

We have two final steps:

The first is we need to figure out how many padding bits after the end of the
CRC input are applied before the CRC value is captured. We can do that just by
playing with 1-bit-set CRCs ourselves and comparing them to Nintendo's:
```
>>> hex(crc_shift_register(0x000000000100000000000, 0x1021, 16))
'0x1a84'
```

... well that was easy. That means thare are **no extra padding bits appended
to the interleaved message before going to CRC**.

The second step is figuring out the XorIn/XorOut. Since the message size is
fixed, the distinction doesn't actually matter - either would result in a fixed
XOR at the end of the message. All we have to do here is get a genuine message
(with its CRC) _interleave it_, compute the CRC using our plain CRC function,
and see how our bits differ from those transmitted. The script has a
commented-out for loop to do just that (as long as you still have the
re-interleave line uncommented), giving an output like:
```
crc(7030919fa83d4c0c46e2e) = 2c63
crc(6030819efc3c084c06266) = 4295
crc(0730819bcc2d48080c24e) = f941
```

Using our own CRC function tells us the XorOut:
```
>>> hex(crc_shift_register(0x7030919fa83d4c0c46e2e, 0x1021, 16) ^ 0x2c63)
'0xce98'
>>> hex(crc_shift_register(0x6030819efc3c084c06266, 0x1021, 16) ^ 0x4295)
'0xce98'
>>> hex(crc_shift_register(0x0730819bcc2d48080c24e, 0x1021, 16) ^ 0xf941)
'0xce98'
```

There you go. **Before transmitting the CRC, XOR it against 0xce98**. Nintendo
began design on the GameCube in C.E. '98, maybe that's when the WaveBird
protocol was developed too?

Impersonating a WaveBird
------------------------

Now it's time to put all of this into practice. We ended the last chapter by
developing a script that took a complete, framed WaveBird message and generated
a 1-second .iq file ready for playback on a HackRF. This time, we're going to
write a script that takes _button states and axes on the command line_ and
generates the message bits.

That script is `generate_message.py`.

To test it, let's try generating the same Z-pressed message we've been using.

```
./generate_message.py -z --jx 0.09 --jy 0.04 --cx 0.055 --cy 0.015 --laxis 0.105 --raxis 0.095
faaaaaaa123444426ac6ec4b02f1e20928d197906116382110
```

Very nice! This script can be combined with `encode_wavebird.py` to generate a
.iq file encoding any arbitrary controller state directly, thoroughly
demonstrating that we've fully cracked the protocol.

What we just did
----------------

This is probably the most wild chapter in this whole adventure, but it's also
arguably the most pragmatic. The codes we learned about all operate on what
mathematicians call _Galois field 2_, which is a fancy way of saying "binary"

We also, indirectly, learned a ton about information theory, mainly in how it
can be used to generate redundant information causing the message _size_ (how
many bits are written) to exceed its _entropy_ (how many bits are strictly
necessary for conveying that amount of information). Similar disciplines
involving entropy are _compression theory_ (where a compression algorithm tries
to shrink the message's size to match its entropy), _cryptography_ (where a
good cipher will increase a message's entropy to match its size), and _random
number generation_ (where a good generator produces nearly one bit worth of
entropy for every bit generated).

CRCs, FECs, and interleaving are certainly not only used in the WaveBird. These
sorts of techniques can be found in just about any digital radio protocol and
then some. You can find these sorts of schemes in barcodes, ECC RAM for
servers, modems, you name it. That's kind of the central theme about this
series: while it may be about the WaveBird, the sorts of techniques and ideas
covered are used everywhere in modern technology.

Oh, and of course let's not forget that we've completely cracked the WaveBird
protocol! Now there's just one step left...
