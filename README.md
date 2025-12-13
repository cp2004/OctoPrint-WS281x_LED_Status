# OctoPrint WS281x LED Status

Add some RGB LEDs to your 3D printer for a quick status update!

![GitHub issues](https://img.shields.io/github/issues/cp2004/OctoPrint-WS281x_LED_Status?style=flat-square)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/cp2004/OctoPrint-WS281x_LED_Status?label=latest%20release&sort=semver&style=flat-square)
![GitHub release installs (latest by date)](https://img.shields.io/github/downloads/cp2004/OctoPrint-WS281x_LED_Status/latest/total?label=New%20installs%40latest&style=flat-square)
![GitHub Repo stars](https://img.shields.io/github/stars/cp2004/OctoPrint-WS281x_LED_Status?style=flat-square)
![GitHub](https://img.shields.io/github/license/cp2004/OctoPrint-WS281x_LED_Status?style=flat-square)
![GitHub Sponsors](https://img.shields.io/github/sponsors/cp2004?style=flat-square)

![rainbow effect](/assets/rainbow.gif)

A highly configurable yet easy to use plugin for attaching WS2811, WS2812 and SK6812 LEDs to your Raspberry Pi (including Raspberry Pi 5!) for a printer status update!

With lots of options effects and integrations to choose from, you can customise the plugin to do things _exactly_ as you want them.

Most prominent features include:

-   **Raspberry Pi 5 support** with multiple LED control backends to choose from
-   Printer status effects
-   Tracking heating, printing and cooling progress
-   Intercepting M150 commands & controlling with @ commands
-   Easy controls for turning lights on and off from the navbar
-   Theme-friendly torch button to temporarily light up your printer
-   Timers to turn the LEDs off at certain times of day or after a print is done.
-   Custom Triggers - add your own events, @ commands or gcode matching to trigger effects
-   Powerful integration with OctoApp for Android
-   ...and more!

You can take a look at the [documentation](https://cp2004.gitbook.io/ws281x-led-status/) for more information about all that the plugin has to offer.

![rainbow effect](/assets/color_wipe.gif)

## Setup

Setting up the plugin couldn't be easier! There are 3 main steps, with configuration made easy with the setup wizard.

-   Wiring your LEDs
-   Choosing and configuring an LED control backend (rpi_ws281x for Pi 3/4, Adafruit CircuitPython for Pi 5)
-   Configuring plugin settings

Follow the detailed [setup guide](https://cp2004.gitbook.io/ws281x-led-status/guides/setup-guide-1) in the documentation to get up and running.

**Note for Raspberry Pi 5 users:** This plugin now supports Pi 5 using the Adafruit CircuitPython NeoPixel (PWM) backend. Requires kernel 6.12+ for PIO support. See the documentation for setup instructions specific to Pi 5.

## Raspberry Pi 5 Support

This plugin now supports **all Raspberry Pi models including Pi 5** through a flexible LED backend system:

- **Pi 1-4, Zero**: Use the `rpi_ws281x` backend (default, fully backward compatible)
- **Pi 5**: Use the `Adafruit CircuitPython NeoPixel (PWM)` backend

**Key features:**
- Multiple backend support with easy selection in plugin settings
- Pi 5 backend supports any GPIO pin (not limited to specific pins)
- Simplified OS configuration for Pi 5 (no SPI setup needed, but PIO support required)
- All plugin features work identically with both backends
- Automatic dependency installation via OctoPrint Plugin Manager

**Quick setup for Pi 5:**
1. Ensure your Raspberry Pi OS has kernel 6.12+ for PIO support
2. Install plugin normally through Plugin Manager
3. In plugin settings, select "Adafruit CircuitPython NeoPixel (PWM)" backend
4. Follow the setup wizard to configure PIO device access (adds user to gpio group and sets udev rules)
5. Configure your GPIO pin (default: 18) and pixel order (usually GRB)
6. Reboot and you're ready!

## Getting help

Please read the [Get Help Guide](https://cp2004.gitbook.io/ws281x-led-status/guides/get-help-guide) as well as the [rest of the documentation](https://cp2004.gitbook.io/ws281x-led-status/), to see if your question has been answered there. Still got questions? Get in touch:

-   On the [OctoPrint Discord](https://discord.octoprint.org)
-   On the [Community Forums](https://community.octoprint.org)
-   Open an issue with the [question template](https://github.com/cp2004/OctoPrint-WS281x_LED_Status/issues/new?assignees=&labels=type%3A+question&template=question.md&title=)

## Reporting problems

Whilst I don't like bugs, I want to hear about them! Let me know by [opening an issue](https://github.com/cp2004/OctoPrint-WS281x_LED_Status/issues/new?assignees=&labels=type%3A+potential+bug&template=bug_report.md&title=%5BBug%5D)

## Contributing

I accept many forms of contribution, from fixing bugs, documentation and new features.
Please see the [Contributing Guidelines](https://github.com/cp2004/OctoPrint-WS281x_LED_Status/blob/master/CONTRIBUTING.md) for more details or get
in touch if you don't know where to start.

## Sponsors

-   [@KenLucke](https://github.com/KenLucke)
-   [@iFrostizz](https://github.com/iFrostizz)
-   [@CmdrCody51](https://github.com/CmdrCody51)

As well as 5 others supporting me regularly through [GitHub Sponsors](https://github.com/sponsors/cp2004)!

## Supporting my efforts

I created this project in my spare time, so if you have found it useful or enjoyed using it then please consider [supporting it's development!](https://github.com/sponsors/cp2004). You can sponsor monthly or one time, for any amount you choose.

## Thanks

This was my first plugin and is still my favourite, so I have to say thanks for helping me develop it:

[jneilliii](https://github.com/jneilliii) for always answering my questions on discord, and making great plugins I could use as examples.

Andreas C. for jumping at the opportunity to beta-test, and providing great feedback as I was creating this!

And, of course, [Gina Häußge](https://github.com/foosel) for creating OctoPrint and such a great community around it.

# 💡
