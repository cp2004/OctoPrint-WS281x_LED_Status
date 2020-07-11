# OctoPrint-RGB LED Status (WIP: May not work perfectly!)

Add an WS2811 or similar LED strip to your printer for a quick status update.

## Features
Supports WS281x strips, for specific supported types see \*\*LINK\*\*

Reacts to printing states; including connected, success, paused and cancelled

Show your heating or print progress on the strip

Easy to use settings interface

## Effects
Currently only supporting solid colour or colour wipe, more soon!

## Setup

Install via the bundled [Plugin Manager](https://docs.octoprint.org/en/master/bundledplugins/pluginmanager.html)
or manually using this URL:

    https://github.com/cp2004/OctoPrint-RGB_LED_Status/archive/master.zip

##Setting up SPI:

_Coming soon via configuration wizard!_

Run the following commands to enable SPI, increase buffer size and make sure the clock is set right.

2. Check your user (pi) is in the `gpio` group
   
   Run `groups pi`, look for `gpio
   If not, run `sudo adduser pi gpio`

1. `sudo nano /boot/config.txt`

    Add `core_freq=250` **or** `core_freq=500` & `core_freq_min=500` (Pi4)
    
    Add `dtparam=spi=on`

2. `sudo nano /boot/cmdline.txt`

    Add `spidev.bufsiz=32768` to the end of the file

## Configuration

**TODO:** Describe your plugin's configuration options (if any).
