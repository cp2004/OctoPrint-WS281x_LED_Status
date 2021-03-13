---
description: >-
  How to setup and configure the Raspberry Pi's SPI interface for use with
  WS281x LEDs.
---

# SPI Setup

The plugin uses the Raspberry Pi's SPI interface to push data to the LED strip, rather than PWM since it doesn't need to be run as root to use SPI.

As a result of this, there are a couple of OS level configuration items that need to be handled. Luckily for you, the plugin makes this very easy for you to do by providing a UI to run the commands.

## Initial Setup Wizard

{% hint style="info" %}
**Note:** You may need to reload the web UI after installing the plugin, to get the wizard to show up. **It will not display if all settings are correct** or you have dismissed the wizard once already.
{% endhint %}

The setup wizard requires root access, and therefore the password for the Pi user if you have not configured passwordless `sudo`, as is default on OctoPi. This password is not stored, and is only used for the steps below.

* **Add the `pi` user to the `gpio` group.** 

  Already configured on newer images. Means the `pi` users can access the GPIO pins.

  * Runs `sudo adduser pi gpio`

* **Enable SPI.**  The plugin uses SPI to drive the LEDs, which is disabled by default and needs to be turned on.
  * Adds `dtparam=spi=on` to `/boot/config.txt`
* **Increase SPI buffer size.**  Whilst the plugin will work without this, it will only work well with a handful of LEDs.
  * Adds `spidev.bufsize=32768` to the end of `/boot/cmdline.txt`
* **Set compatible clock frequency** _Raspberry Pi 3 or earlier only, not required for a Pi 4_  The Pi 3's default internal clock frequency is not compatible with SPI, so it needs to be set to 250 to be compatible.
  * Adds `core_freq=250` to `/boot/config.txt`
* **Set a minimum clock frequency** _Raspberry Pi 4 only_  On a Raspberry Pi 4, the clock frequency is dynamic and can change when the pi is 'idle' vs. 'working', which causes LEDs to flicker, change colour, or stop working completely. By setting a minimum the same as the max, we stop this dynamic clocking.
  * Adds `core_freq_min=500` to `/boot/config.txt`

{% hint style="success" %}
**WS281x LED Status OS configuration complete!**   
You will need to reboot your Pi for these changes to take effect.
{% endhint %}

## Final stage: Initial Configuration

{% page-ref page="initial-configuration.md" %}



