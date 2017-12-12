Reverse-engineering Nintendo's _WaveBird_ wireless controller
=============================================================

Hello and welcome! In this tutorial, we will be looking at the wireless
protocol used by the _WaveBird_, the official wireless controller for the
Nintendo GameCube. This repository contains not only the first (to my knowledge)
public specs on the protocol, but also detailed information on how it was
reverse-engineered. Join me as we explore the art of wireless engineering,
study several tricks used to fight interference, learn a little about the
history of digital radio, and get a glimpse into the world of
reverse-engineering - all without picking up a screwdriver!

Sound good? Great! Head over to **Chapter 0: Observations** and let's get
started!

About the author
----------------

Hey there! I'm Sam Edwards; a network/game engineer by trade, but I try to
dabble in just about everything. I decided to take a look into my Nintendo
WaveBird controller as an exercise in learning more about digital radio, but
when I couldn't find any good resources online that were beginner-friendly
enough, I figured I could use this experience as a teaching device and maybe
help demystify the magic of digital radio for everyone else.

Intended audience for this tutorial
-----------------------------------

While this tutorial is written with aspiring reverse-engineers (in general) and
those wanting to learn more about digital radio (in particular) in mind, I
welcome anyone who finds this stuff fascinating to get involved and learn a
thing or two about wireless.

Questions?
----------

My goal for this tutorial is that you won't have any - so if you do, file them
as issues and I'll try to phrase things a little bit better! :)

Want to contribute?
-------------------

Great! I welcome pull requests. Just keep in mind that the whole point here is
to be a clear and informative tutorial not just on _WaveBird_ in particular,
but on reverse-engineering in general. This means that _beginner-friendliness
is more important than 100% correctness_. We want to make sure
acronyms/initialisms are fully defined and explained, and topics not central to
the subject at hand should be explained only as much as necessary.

Disclaimer
----------

It's important to note here that **at no point in this project have I
physically opened any Nintendo product, examined any circuit boards, dumped any
firmware, disassembled/decompiled any copyrighted software, or worked to
circumvent any copy protection**. I am also not encouraging any of my readers
to do the same - taking apart another company's intellectual property may void
your warranty (at best) and could be a violation of their rights (at worst)
resulting in legal action taken against you personally.

I encourage everyone reading this to stay safe and know their local laws!
