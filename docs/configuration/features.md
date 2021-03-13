---
description: The configuration for the features tab under the plugin's settings
---

# Features

Here's all the details of the additional features of the plugin, so you can effectively configure them.

## Torch

The torch button can be turned on or off to clear up navbar space if you don't want it. It has the same settings as [standard effects](printing-effects.md) but with some added extras for a manual trigger.

Using @ commands to trigger the torch can enable cool integrations with other software, such as OctoLapse.

#### Toggle Mode

The torch button or [@ command](../documentation/host-commands.md) turns the torch on permanently, until it is turned off. This blocks any other effects.

#### Timed Mode

The torch button starts a timer to turn off after configurable length of time.

## Active Times

The LED strip will turn on at the start time, off at the end time. Potentially useful if you don't want them on overnight.

{% hint style="warning" %}
Make sure your system time is set on the server. If you want to change this run `sudo raspi-config` on the Pi.
{% endhint %}

{% hint style="warning" %}
This currently does not support the end time being later than the start time, since it will end up with all the LEDs being off.
{% endhint %}

## M150 Intercept

Enable intercepting and using M150 commands. If not checked, these commands will be sent to the printer.

For documentation of the command, please see the [M150 Intercept documentation page.](../documentation/m150-intercept.md)

## Debug Logging

Debug logging logs a lot more information about the effect runner process. This will help massively when reporting issues on Github, so please enable it when reporting issues!





