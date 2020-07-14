---
layout: plugin

id: rgb_led_status
title: OctoPrint-RGB LED Status
description: Add some RGB LEDs to your printer for a quick status update
author: Charlie Powell
license: AGPLv3

date: 2020-07-14

homepage: https://github.com/cp2004/OctoPrint-RGB_LED_Status
source: https://github.com/cp2004/OctoPrint-RGB_LED_Status
archive: https://github.com/cp2004/OctoPrint-RGB_LED_Status/archive/master.zip

follow_dependency_links: false

tags:
- rgb led
- status
- progress
- neopixel
- ws281x
- ws2811
- ws2812

screenshots:
- url: /assets/img/plugins/rgb_led_status/setup_wizard.jpg
  alt: setup-wizard-screenshot
  caption: Setup Wizard Screenshot
- url: /assets/img/plugins/rgb_led_status/settings_overview.png
  alt: settings-overview-screenshot
  caption: Settings Overview Screenshot
- url: /assets/img/plugins/rgb_led_status/settings_printing.png
  alt: settings-printing-screenshot
  caption: Printing Settings Screenshot

featuredimage: /assets/img/plugins/rgb_led_status/settings_overview.jpg

compatibility:

  octoprint:
  - 1.4.0

  os:
  - linux

  python: ">=3,<4"

---

Supporting effects for various printing states as well as print and heating progress,
you will always know what your printer is doing without needing to look at the web interface all the time.

This plugin currently only supports Python 3, if you would like to upgrade your install to Python 3 I've got a handy script here [OctoPrint-Upgrade-To-Py3](https://github.com/cp2004/Octoprint-Upgrade-To-Py3)

### Setting up SPI
[See here](https://github.com/cp2004/OctoPrint-RGB_LED_Status/wiki/SPI-Setup-Running-without-root) for details of how to setup SPI so you can use your LEDs. There is also a configuration wizard that will do this for you on the first install, if you ask it nicely.

### Wiring your LEDs
[See here](https://github.com/cp2004/OctoPrint-RGB_LED_Status/wiki/Wiring-LEDS-to-your-Raspberry-Pi) for details of how to wire your LED strips to a Raspberry Pi.

### Configuration options
[See here](https://github.com/cp2004/OctoPrint-RGB_LED_Status/wiki/Configuration-options) for details of the various configuration options available for the plugin, and have a look at the screenshots below
