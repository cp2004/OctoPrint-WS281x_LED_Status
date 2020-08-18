# OctoPrint-WS281x LED Status

Add an WS2811 or similar LED strip to your printer for a quick status update.

_Based on the concepts behind work by [Eric Higdon](https://github.com/EricHigdon/OctoPrint-RGB_status), completely re-written for higher customizablility and new effects._

## Features
* Supports WS281x strips, for specific supported types see ['Supported hardware'](https://github.com/cp2004/OctoPrint-WS281x_LED_Status/wiki/Supported-hardware)

* Reacts to printing states; including connected, success, paused and cancelled

* Show your heating or print progress on the strip

* Set up a timer to turn the strip on and off

* Toggle the lights on and off from the navbar

* Control your strip from gcode scripts using M150 or host @ commands *(New in 0.4.0)*

* Easy to use but highly customizeable settings interface, you can turn anything you want on or off.

## Effects
Supporting effects inculding a color wipe, rainbow, bounce, pulse and more! You can see them all on [this wiki page](https://github.com/cp2004/OctoPrint-WS281x_LED_Status/wiki/Configuration-options#effects)

## Support My Work!
If you use this plugin and appreciate the work that has gone in to making it as good as it can be, then you can support development!

[Sponsor through GitHub here](https://github.com/sponsors/cp2004), to make your contribution.

## Supporters
<a href="https://www.jetbrains.com/?from=cp2004"><img align="left" width="100" height="100" src="jetbrains-variant-2.png" alt="JetBrains Logo"></a> Thanks to JetBrains for supporting an open source license for their brilliant IDEs!

See the sponsors link above for details of how to get your name on the list here!


.
## Setup

Install via the bundled [Plugin Manager](https://docs.octoprint.org/en/master/bundledplugins/pluginmanager.html)
or manually using this URL:

    https://github.com/cp2004/OctoPrint-WS281x_LED_Status/archive/master.zip

Once you have installed and enabled the plugin, OctoPrint will prompt you to restart the server. Once it is back up, please note **you may have to refresh the page in order for the wizard dialog to show up.**

### Setting up SPI:

Please see the [page on the wiki](https://github.com/cp2004/OctoPrint-WS281x_LED_Status/wiki/SPI-Setup-Running-without-root) for details of how to do this. There is also a configuration wizard that will sort this out for you.

## Thanks
[jneilliii](https://github.com/jneilliii) for always answering my questions on discord, and making great plugins I could use as examples.

Andreas C. for jumping at the opportunity to beta-test, and providing great feedback!

And, of course, [Gina Häußge](https://github.com/foosel) for creating OctoPrint
