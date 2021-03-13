---
description: This page lists the hardware that is officially supported to use this plugin
---

# Supported Hardware

## LED Strips

The 3 types of LED strips that the plugin supports are:

* WS2811 \(including B variants\)
* WS2812 \(including B variants\)
* SK6812 RGB
* SK6812 RGBW

Please note as well that 'NeoPixels' are an Adafruit brand name, I find that they are much cheaper direct from China with just as good results, they are the same thing.

{% hint style="info" %}
At this time, only the RGB LEDs are used. Thanks to [a PR from @samwiseg0](https://github.com/cp2004/OctoPrint-WS281x_LED_Status/pull/93) this is coming soon!
{% endhint %}

## Power Supplies

There are no officially-supported models for power supplies, since they are all the same. However, please make sure you are using **an external power supply** and not using the RPi GPIO pins to power the LEDs. They cannot provide the power drawn by a strip of WS281x LEDs.

Don't use tiny wires to connect the LEDs - these can heat up and melt if they are too thin.

## Level Shifting

I have had good results with a 74ACHT125 level shifter, which is recommended by Adafruit for their Neopixels. Please note that while WS281x LEDs work without level shifting, you may need to keep the wires as short as possible - **especially** when using 12V LEDs.

## On to wiring it all up!

{% page-ref page="wiring-your-leds.md" %}

