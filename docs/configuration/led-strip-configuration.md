---
description: Detailed descriptions of the LED Strip Configuration dialog.
---

# LED Strip Configuration

This documentation aims to explain all of the settings in the LED Strip Configuration dialog, so you can make the most use of them.

| Setting | Value Type | Explanation |
| :--- | :--- | :--- |
| Strip Type | Selection | The type of strip you have connected, for a complete list see supported hardware |
| Max Brightness | Percentage | The maximum brightness the strip should reach in any effect. |
| Number of LEDs | Number | I hope this one is obvious enough |
| GPIO Pin | Number | The pin that the LEDs are connected to. This should be BCM [GPIO 10](https://pinout.xyz/pinout/pin19_gpio10) for normal operation, other pins are available when OctoPrint is run as root and can use PWM - though this is explicitly **not recommended** for security reasons. |
| Frequency | Number | Frequency to drive the LEDs at. This should be 800 000 in normal use, some older strips may require different values. |
| DMA Channel | Number | **Do not change the DMA channel if you do not know what you are doing.** This should be 10 in normal use, other values can cause severe problems. |
| Invert Pin output | Checkbox | Invert the signal from the Raspberry Pi. Useful if your setup uses a level shifter that inverts the signal, it can be inverted again to make it the right way around in the end. |
| PWM Channel | Number | _\(To be removed from the UI in a future version\)_ Internal PWM Channel. Irrelevant to the plugin since it uses SPI in most cases. Will still be available via `config.yaml` manual editing. |

{% hint style="warning" %}
Some of the settings above will be moved to an 'advanced' section of the strip editor in a future version, since they do not need to be changed in normal usage.
{% endhint %}



