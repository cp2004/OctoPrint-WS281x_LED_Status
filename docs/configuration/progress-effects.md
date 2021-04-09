---
description: 'Progress can be tracked as well, to display more detailed status'
---

# Progress Effects

Each progress effect has some standard options, to customise them. Individual effects have additional options, listed alongside them.

## Standard Options

* Enabled
* Progress Colour The colour to indicate the progress of whatever event is happening.
* Base Colour

  The base/background colour of the progress indication.

In addition, there are two global options:

* Reverse the direction of the progress bar
* Base temperature Heating/cooling progress bar will make '0' the temperature specified. Suggested value is just below room temperature, so that the progress bar starts closer to the end of the strip.

## Events

### Printing Progress

Matches the progress bar in OctoPrint's UI, on your LED strip.

### Heating Progress

Triggered when a blocking heating command \(`M109` or `M190`\) sent to the printer.

Additional options:

* Index of tool to track Leave this at 0 for single extruder printers, for multiple extruder printers you can choose a single tool to track.
* Enable tracking tool heating
* Enable tracking bed heating

### Cooling Progress

Triggered on print success, this will display the progress of the printer while it is still cooling.

Additional options:

* Track cooling on bed or tool Select one, since they usually cool down at the same time.
* Cooling temperature threshold The temperature when cooling tracking should stop

{% hint style="warning" %}
Don't set cooling tracking below room temperature, or this effect will never end!
{% endhint %}

