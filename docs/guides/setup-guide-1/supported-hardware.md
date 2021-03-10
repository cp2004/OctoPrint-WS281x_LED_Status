---
description: This page lists the hardware that is officially supported to use this plugin
---

# Supported Hardware

## LED Strips

The 4 types of LED strips that the plugin supports are:

* WS2811 \(including B variants\)
* WS2812 \(including B variants\)
* SK6812 RGB
* SK6812 RGBW

Please note as well that 'NeoPixels' are an Adafruit brand name for WS281x type LEDs. I find they are much cheaper when bought unbranded, with just as good results.

{% hint style="info" %}
WS2813 LEDs are also reported to work using the WS2812 settings. Wiring is similar, the `BI` pin should be grounded and is not used.
{% endhint %}

## Power Supplies

There are no officially-supported models for power supplies, since they are all the same. However, please make sure you are using **an external power supply** and not using the RPi GPIO pins to power the LEDs. They cannot provide the power drawn by a strip of WS281x LEDs.

Don't use tiny wires to connect the LEDs - these can heat up and melt if they are too thin.

## Level Shifting

I have had good results with a 74ACHT125 level shifter, which is recommended by Adafruit for their NeoPixels. Please note that while WS281x LEDs work without level shifting, you may need to keep the wires as short as possible - **especially** when using 12V LEDs.

## On to wiring it all up!

{% page-ref page="wiring-your-leds.md" %}

