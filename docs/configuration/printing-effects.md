---
description: >-
  The core of the plugin, the most used feature to find the status of your
  printer.
---

# Printing Effects

The plugin reacts to several events to display printing effects. For each of these effects, they have similar settings:

* **Enable** Whether the effect will run or not
* **Effect** One of the available [effects](printing-effects.md#effects)
* **Colour**  The primary colour to run the effect. Note this is ignored in some effects.
* **Delay** The length of time to wait between each frame of the effect.

Some events also have some specific settings, these are detailed alongside them.

## Events

* Startup
* Printer Connected/Idle
* Printer Disconnected
* Print Success
  * This effect has configurable 'Return to idle' time in seconds. Set to 0 to disable returning to idle.
* Print Paused
* Print Failed
* Printing
  * This effect will override the print progress effect.

## Effects

All the standard effects available, with fancy visualisations!

### Solid Colour

Sets all LEDs to one colour, forever.

![](../.gitbook/assets/solid_colour%20%286%29.gif)

### Colour Wipe

Wipes colour across the strip pixel by pixel, then clears it pixel by pixel.

![](../.gitbook/assets/color_wipe%20%285%29.gif)

### Colour Wipe V2

Wipes colour pixel by pixel, as above, but to clear it turns around and heads backwards.

![](../.gitbook/assets/color_wipe_2.gif)

### Pulse

Fades brightness up and down. Looks better in real life than the visualisation below!

![](../.gitbook/assets/pulse%20%287%29.gif)

### Bounce

Sends a pulse of light bouncing from one side of your strip to the other.

![](../.gitbook/assets/bounce%20%283%29.gif)

### Solo Bounce

Sends just a single pixel from one side to the other, bouncing about.

![](../.gitbook/assets/solo_bounce.gif)

### Rainbow

Cycles all the LEDs through the rainbow together.

![](../.gitbook/assets/rainbow%20%281%29.gif)

### Rainbow Cycle

Rainbow that cycles across the strip, so a full rainbow is across the whole strip at once.

![](../.gitbook/assets/rainbow_cycle.gif)

### Crossover

Two pixels bouncing in opposite directions, crossing over in the middle.

![](../.gitbook/assets/crossover.gif)

### Random

Sets all LEDs to a random colour, then changes a random pixel, to a new random colour

![](../.gitbook/assets/random%20%287%29.gif)

### Bouncy Balls

A physics based effect, simulating 2 balls bouncing up and down. Looks great on longer strips \(and shorter ones too...!\).

Unfortunately creating the simulation for this effect didn't work, so is unavailable for now. Sorry!

