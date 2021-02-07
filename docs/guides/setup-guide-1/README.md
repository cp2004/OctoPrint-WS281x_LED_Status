---
description: How to setup WS281x LED Status on your Raspberry Pi running OctoPrint.
---

# Setup Guide

I've tried to make this setup process as simple as possible, while it was already easy it is even easier with this guide.

## Installation

Install the plugin via OctoPrint's bundled [plugin manager](https://docs.octoprint.org/en/master/bundledplugins/pluginmanager.html) or manually using this URL:

```
https://github.com/cp2004/OctoPrint-WS281x_LED_Status/releases/latest/download/release.zip
```

Once you have installed and enabled the plugin, OctoPrint will prompt you to restart the server.

{% hint style="info" %}
 Once the server is back up, you may have to refresh the page for in order for the wizard dialog to show up.
{% endhint %}

{% hint style="warning" %}
Using the OctoPrint Docker container? There's some [additional steps you have to follow ](../setup-in-docker.md)for this to work.
{% endhint %}

### Check you have the right hardware:

{% page-ref page="supported-hardware.md" %}

### Next up: Wiring your LEDs

{% page-ref page="wiring-your-leds.md" %}



