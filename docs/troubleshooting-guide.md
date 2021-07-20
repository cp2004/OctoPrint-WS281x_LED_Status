---
description: >-
  This page aims to list common problems people have with the plugin. Please
  read it before opening issues.
---

# Troubleshooting Guide

This is going to be an ever-evolving page, as I learn of common issues people identify when setting up the plugin.

{% hint style="success" %}
Got something to contribute? You can send a PR to edit this page, just click the 'Edit on GitHub' button. All contributions are welcome, and you will help someone else out!
{% endhint %}

## What type of issue are you facing?

These questions aim for self-diagnosis - there is no guarantee that your problem will be listed!

* [No LED output at all](troubleshooting-guide.md#no-led-output-at-all)
* [Unstable LED output, flickering, random colours](troubleshooting-guide.md#unstable-led-output-flickering-and-changing-colours)
* [Stable LEDs but colours are wrong](troubleshooting-guide.md#stable-led-output-but-the-colours-are-wrong)
* [OctoPrint plugin issues - plugin not loading or similar](troubleshooting-guide.md#generic-plugin-issues)

## No LED Output at all

First things first, make sure that your OS configuration test passes - the LEDs do not usually work without these tests passing.

### I restored an OctoPrint backup to a new install, but the LEDs no longer work?

It is likely that the OS level config is incorrect. To fix this, please head to the OS Configuration Test section \(under 'Utilities'\) to run a test and fix the configuration.[ See the OS Configuration Test docs.](utilities.md#os-configuration-test)

### No LED output on a new Raspberry Pi log has 'Unsupported board' errors

The dependency the plugin relies on needs to be updated for every new Raspberry Pi board. This often happens quickly, but your install may be outdated. You can manually upgrade the dependency to the latest version:

```text
pip install -U rpi-ws281x
```

{% hint style="warning" %}
**This needs to be done from within your OctoPrint install's virtual environment.** On OctoPi, this would be `~/oprint/bin/pip.`
{% endhint %}

### Little/no LED output when not using a level shifter

Some strips do not like 3.3V signals, and if you do use 3.3v \(**without a level shifter**\) then please keep the wires to the LEDs fairly short to avoid voltage drop. Alternatively, use a level shifter if it seems that you are suffering from this issue.

### No LED output when using a GPIO touchscreen

Some GPIO touchscreens \(and _possibly_  some others?\) use SPI to process data. This conflicts with this plugin's use of SPI to drive the LEDs and as a result you may not be able to use both.

Errors in the log file are similar to this: 

```text
ws2811_init failed with code -13 (Unable to initialize SPI)
```

Unfortunately, there is nothing you can do about this. If you know what you are doing, you may be able to run the LEDs using PWM but please note that this requires root access to the Raspberry Pi and for security reasons this is not recommended for OctoPrint.

## Unstable LED output, flickering and changing colours.

### LEDs flicker and change colour loads

You need a common ground between the LEDs, power supply and the Pi - this is the number one cause of flickering. Please check the [wiring guide](guides/setup-guide-1/wiring-your-leds.md) to see how it should be done. You can also see the [example video in this issue](https://github.com/cp2004/OctoPrint-WS281x_LED_Status/issues/25).

### Random flickering of LEDs, unstable signal

Adding a 470Ω resistor in the signal line can help. Some guides recommend this, in my experience it is not always required. Worth a try if you have unstable signal to the LEDs. [Link to the relevant issue report. ](https://github.com/cp2004/OctoPrint-WS281x_LED_Status/issues/72#issuecomment-775382060)

### More unstable signal fixes

Mixed reports that using a sacrificial LED on a short wire \(to avoid voltage drop\) can be beneficial for the LED strip. See [this Hackaday article](https://hackaday.com/2017/01/20/cheating-at-5v-ws2812-control-to-use-a-3-3v-data-line/) for more details. This solution is untested, only linked because it might be useful. Support for skipping the first LED on the animations is in the next release of the plugin.

## Stable LED output but the colours are wrong

### The colours of my LEDs are wrong

Make sure you have the correct order of RGB strip selected in the strip settings. You can use the LED Strip test to help debug this issue quickly. The colour order and strip type you were sold is not necessarily what works, do not hesitate to change the strip type settings until it works!

### After booting the Pi & OctoPrint, LEDs turn solid white and do not recover

My current theory behind this issue is bad power supply to the Raspberry Pi, which will create a throttled and unstable system. This can impact the precise timing the LEDs require and means they only display white.

To fix the issue, please use an adequate power supply with your Raspberry Pi. See the [Raspberry Pi documentation](https://www.raspberrypi.org/documentation/hardware/raspberrypi/power/README.md) for details on the specification for power supplies for different models.

## Generic plugin issues

### Can't find the plugin after installation

Make sure you restart the OctoPrint server, and reload the web interface. You should see the wizard pop up, or the light/torch icon in the navbar. I have had some reports of caching meaning the configuration wizard does not show.

### Plugin does not load on my device

This plugin **requires** a Raspberry Pi to run. It should run on any Linux-based OS on any Raspberry Pi, and it has detection mechanisms in place and will not load if the device it is installed on is not a Pi. This is logged, so you will see an explanation in the octoprint.log file if this is the case.

**If you are using docker**, then make sure you have followed the [Setup In Docker](guides/setup-in-docker.md) page to get the plugin to run.

