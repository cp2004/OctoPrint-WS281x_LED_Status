# OctoPrint-WS281x LED Status (WIP: May not work perfectly!)

Add an WS2811 or similar LED strip to your printer for a quick status update.

_Based on the concepts of work [Eric Higdon](https://github.com/EricHigdon/OctoPrint-RGB_status), completely re-written for higher customizablility and new effects._

## Known incompatibility with [OctoPrint-TPLinkSmartplug](https://github.com/jneilliii/OctoPrint-TPLinkSmartplug). We are working to fix this.

## Features
Supports WS281x strips, for specific supported types see the wiki

Reacts to printing states; including connected, success, paused and cancelled

Show your heating or print progress on the strip

Set up a timer to turn the strip on and off

Toggle the lights on and off from the navbar

Easy to use but highly customizeable settings interface

## Effects
Supporting effects inculding a color wipe, rainbow, bounce, pulse and more!

## Setup

Install via the bundled [Plugin Manager](https://docs.octoprint.org/en/master/bundledplugins/pluginmanager.html)
or manually using this URL:

    https://github.com/cp2004/OctoPrint-WS281x_LED_Status/archive/master.zip

### Setting up SPI:

Please see the Wiki for details of how to do this. There is also a configuration wizard that will sort this out for you.

## Thanks
[jneilliii](https://github.com/jneilliii) for always answering my questions on discord, and making great plugins I could use as examples.

Andreas C. for jumping at the opportunity to beta-test, and providing great feedback!

And, of course, [Gina Häußge](https://github.com/foosel) for creating OctoPrint
