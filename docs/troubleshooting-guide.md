---
description: >-
  This page aims to list common problems people have with the plugin. Please
  read it before opening issues.
---

# Troubleshooting Guide

This is going to be an ever-evolving page, as I learn of common issues people identify when setting up the plugin.

{% hint style="success" %}
Got something to contribute? You can send a PR to edit this page, just click the 'Edit on Github' button. All contributions are welcome!
{% endhint %}

## LEDs flicker and change colour loads

Check you have a common ground between an external power supply, and the Pi. See more \(including an example video\) in the [issue opened here](https://github.com/cp2004/OctoPrint-WS281x_LED_Status/issues/25)

## The colours of my LEDs are wrong

Make sure you have the correct order of RGB strip selected in the strip settings. You can use the LED Strip test to help debug this issue quickly.

## Can't find the plugin after installed

Make sure you restart the OctoPrint server, and reload the web interface. You should see the wizard pop up, or the light/torch icon in the navbar.

[Initial report](https://github.com/cp2004/OctoPrint-WS281x_LED_Status/issues/12)

## I restored an OctoPrint backup to a new install, but the LEDs no longer work?

It is likely that the OS level config is incorrect. To fix this, please head to the OS Configuration Test section \(under 'Utilities'\) to run a test and fix the configuration.[ See the OS Configuration Test docs.](utilities.md#os-configuration-test)

## Unable to initialize SPI

If you get the error:

```text
ws2811_init failed with code -13 (Unable to initialize SPI)
```

From the `plugin_ws281x_led_status_debug.log` then it likely means that you have some extra peripherals attached to your Pi, that are taking up the SPI channels, therefore conflicting with the plugin's use of SPI.

[**Specific to this Elecrow 5 inch HDMI touchscreen**](https://www.elecrow.com/wiki/index.php?title=RC050_5_inch_HDMI_800_x_480_Capacitive_Touch_LCD_Display_for_Raspberry_Pi/_PC/_SONY_PS4)

A user reported that SPI failed to initialise with the above screen, however commenting out the lines the guide asked you to enter meant that both the screen and LEDs could work at the same time.

## No LED output on a Raspberry Pi 4B \(rev 1.4\), and the log says 'Unsupported board'

The dependency that this plugin relies on was not updated to add support for these boards as of the last release of the plugin. Please see [this issue](https://github.com/cp2004/OctoPrint-WS281x_LED_Status/issues/73) for instructions of how to fix it.

## Little/no LED output when not using a level shifter

Some strips do not like 3.3V signals, and if you do use 3.3v \(**without a level shifter**\) then please keep the wires to the LEDs fairly short to avoid voltage drop.

## Random flickering of LEDs, unstable signal

Adding a 470Ω resistor in the signal line can help. Some guides recommend this, in my experience it is not always required. Worth a try if you have unstable signal to the LEDs. [Link to issue](https://github.com/cp2004/OctoPrint-WS281x_LED_Status/issues/72#issuecomment-775382060).

## After booting the Pi & OctoPrint, LEDs turn solid white and do not recover

Current theory behind this issue is bad power supply to the Raspberry Pi, which will create a throttled and unstable system. This can impact the precise timing the LEDs require and means they only display white.

To fix the issue, please use an adequate power supply with your Raspberry Pi. See the [Raspberry Pi documentation](https://www.raspberrypi.org/documentation/hardware/raspberrypi/power/README.md) for details on the specification for power supplies for different models.

## More unstable signal fixes

Mixed reports that using a sacrificial LED on a short wire \(to avoid voltage drop\) can be beneficial for the LED strip. See [this Hackaday article](https://hackaday.com/2017/01/20/cheating-at-5v-ws2812-control-to-use-a-3-3v-data-line/) for more details. This solution is untested, only linked because it might be useful.

