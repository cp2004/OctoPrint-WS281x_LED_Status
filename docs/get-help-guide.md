---
description: Need help using the plugin? Read this page first.
---

# Get Help Guide

Please select the area that most describes what you need help with:

* Configuration of the plugin
* Connecting LEDs and getting them to work
* Reporting a bug in the plugin

### Configuration of the plugin

There's a lot of documentation here, that describes in detail the configuration options and the features of the plugin. Be sure to read the pages under the configuration section, such as [LED Strip Configuration](configuration/led-strip-configuration.md)

{% hint style="info" %}
**Still struggling?** Please seek help on the [OctoPrint community forums](https://community.octoprint.org), or the [Discord Server](https://discord.octoprint.org). I'm often there, or there are other users of the plugin who can help out.
{% endhint %}

### Connecting LEDs and making them work

Probably the step that has the most problems, you're not alone here.

Please double check that you have wired the LEDs exactly as shown in the [Wiring Guide](guides/setup-guide-1/wiring-your-leds.md) and double check all connections.

Next up is the [troubleshooting guide](troubleshooting-guide.md), where there's a list of common problems identified with solutions. Please check there and make sure your problem isn't listed, or try some of the recommended solutions.

{% hint style="info" %}
**Still won't work?**

Before asking for help, please ensure that your LED strip works with other devices if possible. The best thing to check is with an Arduino, since these work more reliably than Raspberry Pi & Python. 

You can seek support on the [OctoPrint community forums](https://community.octoprint.org), or the[ Discord Server](https://discord.octoprint.org) as well as opening a ['Get Help'](https://github.com/cp2004/OctoPrint-WS281x_LED_Status/issues/new?assignees=&labels=question&template=question.md&title=) issue. Please note that at some point these may be disabled if the load gets too high.
{% endhint %}

### Reporting a bug with the plugin

Really? You found a bug? Ok then, best make sure it is fixed.

Please open a bug report issue providing as much information as possible, including:

* **\(Always\)** `octoprint.log` file
* **\(Always\)**`plugin_ws281x_led_status_debug.log` file, preferably with [debug logging](configuration/features.md#debug-logging) enabled.
* Clear, easy steps to reproduce.
* The hardware you are using \(if relevant\)
* Screenshots/video showing the problems \(if necessary - these can help quite a lot\)

Please use the [bug report template!](https://github.com/cp2004/OctoPrint-WS281x_LED_Status/issues/new?assignees=&labels=&template=bug_report.md&title=%5BBug%5D)



