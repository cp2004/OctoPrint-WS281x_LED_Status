---
description: Detailed descriptions of the LED Strip Configuration dialog.
---

# LED Strip Configuration

This documentation aims to explain all of the settings in the LED Strip Configuration dialog, so you can make the most use of them.

| Setting           | Value Type | Explanation                                                                                                                                                                                                                                 |
| ----------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Strip Type        | Selection  | The type of strip you have connected, for a complete list see supported hardware                                                                                                                                                            |
| Max Brightness    | Percentage | The maximum brightness the strip should reach in any effect.                                                                                                                                                                                |
| Number of LEDs    | Number     | I hope this one is obvious enough 🙂                                                                                                                                                                                                        |
| GPIO Pin          | Number     | The pin that the LEDs are connected to. This should be **BCM** [**GPIO 10**](https://pinout.xyz/pinout/pin19\_gpio10) for normal operation.[ See the details below for other GPIO pin options](led-strip-configuration.md#gpio-pin-options) |
| Frequency         | Number     | Frequency to drive the LEDs at. This should be 800 000 in normal use, some older strips may require different values.                                                                                                                       |
| DMA Channel       | Number     | <p><em>(Not available in the UI)</em></p><p><strong>Do not change the DMA channel if you do not know what you are doing.</strong></p><p>This should be 10 in normal use, other values can cause severe problems.</p>                        |
| Invert Pin output | Checkbox   | Invert the signal from the Raspberry Pi. Useful if your setup uses a level shifter that inverts the signal, it can be inverted again to make it the right way around in the end.                                                            |
| PWM Channel       | Number     | <p><em>(Not available in the UI)</em></p><p>Internal PWM Channel. Irrelevant to the plugin since it uses SPI in most cases.</p>                                                                                                             |

{% hint style="warning" %}
DMA Channel and PWM channel will remain available for editing using config.yaml, just in case you need to change this. You probably won't.
{% endhint %}

### GPIO Pin Options

#### What other pins work?

To run this without root access, you must use an SPI pin. WS281x LEDs require specific timing pulses, and not every pin can produce these.

On all Pi's, the default, **GPIO 10** can be used.

On all Pi's **except** the original Pi 1 model A and Pi 1 model B, **GPIO 20** can be used. This requires adding `dtoverlay=spi1-3cs` to the `/boot/config.txt` file to enable SPI1

Other SPI interfaces are available, specific to certain Raspberry Pi models. More details on them can be found on the[ Raspberry Pi Documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#serial-peripheral-interface-spi) which contains detailed information. It is unknown if they all work with WS281x LEDs.

#### Can I use a PWM pin?

Using a PWM pin to drive WS281x LEDs on a Raspberry Pi requires root access. This is out of my control. It is **not recommended** to run OctoPrint (or any web server) with root privileges due to **security reasons**. So while yes, you can use PWM you are on your own to configure OctoPrint to run as root.

#### What about some other GPIO pin?

If it's not an SPI capable pin, or a PWM capable pin then no. This is a hardware limitation of the Raspberry Pi.



