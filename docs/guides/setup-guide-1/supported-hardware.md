---
description: This page lists the hardware that is officially supported to use this plugin
---

# Supported Hardware

## LED Strips

The 4 types of LED strips that the plugin supports are:

* WS2811 (including B variants)
* WS2812 (including B variants)
* SK6812 RGB
* SK6812 RGBW

Please note as well that 'NeoPixels' are an Adafruit brand name, I find that they are much cheaper direct from China with just as good results, they are the same thing.

{% hint style="info" %}
To get the most of your RGBW strips, you can enable 'Use dedicated white' in the strip settings after it is setup.
{% endhint %}

## Power Supplies

There are no officially-supported models for power supplies, since they are all the same. However, please make sure you are using **an external power supply** and not using the RPi GPIO pins to power the LEDs. They cannot provide the power drawn by a strip of WS281x LEDs.

Don't use tiny wires to connect the LEDs - these can heat up and melt if they are too thin.

## Level Shifting

I have had good results with a 74ACHT125 level shifter, which is recommended by Adafruit for their Neopixels. Please note that while WS281x LEDs work without level shifting, you may need to keep the wires as short as possible - **especially** when using 12V LEDs.

### Raspberry Pi

**All models of Raspberry Pi are supported**, including:
- Raspberry Pi 1, 2, 3, 4
- Raspberry Pi Zero, Zero 2
- **Raspberry Pi 5** (new!)

The plugin now uses a flexible LED backend system to support all hardware versions:
- **Pi 1-4, Zero**: Uses the `rpi_ws281x` backend by default
- **Pi 5**: Uses the `Adafruit CircuitPython NeoPixel (PWM)` backend

You can select your backend in the plugin settings during initial setup. Both backends support all plugin features identically.

{% hint style="info" %}
For Raspberry Pi 5 users: Select the "Adafruit CircuitPython NeoPixel (PWM)" backend in plugin settings. Requires kernel 6.12+ for PIO (Programmable I/O) support. The setup wizard will guide you through configuring PIO device access (user must be in gpio group and udev rules must be set).
{% endhint %}

**Note:** Only Raspberry Pi devices are supported. The plugin **will not load** if it is not running on a Raspberry Pi, even if it does install.

## Got the necessary hardware? Wire it up!
