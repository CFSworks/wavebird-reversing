#!/usr/bin/env python2

from __future__ import division

import sys
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import animation, patches

fig = plt.figure()

visualization = sys.argv[1]

if visualization == 'realsig':
    FRAMES = 60
    plt.title("A real-valued signal as a sum of +freq,-freq complex signals")
    plt.ylim(-1, 1)
    plt.xlim(-1.3333, 1.3333)

    ax = fig.gca()
    ax.grid(True, which='both')
    Q = None

    l, = ax.plot(np.arange(0, 1, 0.01), np.arange(0, 1, 0.01), label='Real-valued signal')
    r = patches.Patch(color='red', label='-frequency half-signal')
    g = patches.Patch(color='green', label='+frequency half-signal')
    plt.legend(handles=[l,r,g])

    def update(i):
        global Q

        theta = math.pi*2*i/FRAMES
        l.set_data(np.cos(theta - np.arange(0, 1, 0.01) * math.pi),
                   np.arange(0, 1, 0.01))

        first_end_x = math.cos(theta) * 0.5
        first_end_y = math.sin(theta) * 0.5
        second_end_x = math.cos(-theta) * 0.5
        second_end_y = math.sin(-theta) * 0.5

        if Q: Q.remove()
        Q = ax.quiver([0, first_end_x], [0, first_end_y],
                      [first_end_x, second_end_x], [first_end_y, second_end_y],
                      units='xy', angles='xy', scale=1,
                      color=('g', 'r'))

elif visualization in ['solarsystem_moon', 'solarsystem_sun',
                       'solarsystem_spinning', 'solarsystem_earthvec',
                       'solarsystem_moonvec', 'solarsystem_complete']:
    FRAMES = 240
    plt.ylim(-1, 1)
    plt.xlim(-1.3333, 1.3333)

    SUN_FREQ = 0
    SUN_PHASOR = 0.1+0.05j
    PLANET_FREQ = 4*math.pi/FRAMES
    PLANET_PHASOR = 0.4+0.6j
    MOON_FREQ = 14*math.pi/FRAMES
    MOON_PHASOR = 0.05-0.13j
    SPIN_FREQ = 0

    ax = fig.gca()
    ax.set_axis_bgcolor('k')
    notch, = ax.plot([0,0,-5,5], [-5,5,0,0], color='w')

    Q = None

    moon = plt.Circle((0,0), 0.01, color='w', label='Moon position')
    ax.add_artist(moon)

    if visualization == 'solarsystem_sun':
        sun = plt.Circle((SUN_PHASOR.imag, SUN_PHASOR.real), 0.05, color='y', label='Average moon position (the sun!)')
        ax.add_artist(sun)
    else:
        sun = None

    if visualization == 'solarsystem_spinning':
        center = plt.Circle((0,0), 0.01, color='r', label='Average moon position - the very center')
        ax.add_artist(center)
        SPIN_FREQ = math.pi*2/FRAMES
    else:
        center = None

    arrow = None
    planet = None
    if visualization == 'solarsystem_earthvec':
        SPIN_FREQ = -PLANET_FREQ
        ax.quiver(0, 0, PLANET_PHASOR.real, PLANET_PHASOR.imag,
                  color='b', units='xy', scale=1)
        arrow = patches.Patch(color='b', label='Average moon position - Earth\'s offset!')
    elif visualization == 'solarsystem_moonvec':
        SPIN_FREQ = -MOON_FREQ
        ax.quiver(0, 0, MOON_PHASOR.real, MOON_PHASOR.imag,
                  color='w', units='xy', scale=1)
        arrow = patches.Patch(color='w', label='Average moon position - Moon\'s offset!')
    
    elif visualization == 'solarsystem_complete':
        sun = plt.Circle((SUN_PHASOR.imag, SUN_PHASOR.real), 0.05, color='y', label='Sun')
        ax.add_artist(sun)
        planet = plt.Circle((PLANET_PHASOR.imag, PLANET_PHASOR.real), 0.02, color='b', label='Earth')
        ax.add_artist(planet)


    plt.legend(handles=filter(bool, [moon,planet,sun,center,arrow])).get_frame().set_facecolor((1,1,1,0.3))

    def update(i):
        global Q

        sun_pos = math.e**(SUN_FREQ*i*1j) * SUN_PHASOR
        planet_pos = math.e**(PLANET_FREQ*i*1j) * PLANET_PHASOR + sun_pos
        moon_pos = math.e**(MOON_FREQ*i*1j) * MOON_PHASOR + planet_pos

        rot = math.e**(SPIN_FREQ*i*1j)
        sun_pos *= rot
        planet_pos *= rot
        moon_pos *= rot
        notch.set_data([-5*rot.real, 5*rot.real, -5*rot.imag,  5*rot.imag],
                       [-5*rot.imag, 5*rot.imag,  5*rot.real, -5*rot.real])

        moon.center = (moon_pos.real, moon_pos.imag) 
        if sun: sun.center = (sun_pos.real, sun_pos.imag)
        if planet: planet.center = (planet_pos.real, planet_pos.imag)

        if visualization == 'solarsystem_complete':
            if Q: Q.remove()
            Q = ax.quiver([sun_pos.real, planet_pos.real],
                          [sun_pos.imag, planet_pos.imag],
                          [planet_pos.real-sun_pos.real, moon_pos.real-planet_pos.real],
                          [planet_pos.imag-sun_pos.imag, moon_pos.imag-planet_pos.imag],
                          units='xy', angles='xy', scale=1,
                          color=('b', 'w'))

ani = animation.FuncAnimation(fig, update, frames=FRAMES, blit=True)
ani.save('../03_complex_signals_and_fourier/img/%s.gif' % visualization, writer='imagemagick', fps=30)
