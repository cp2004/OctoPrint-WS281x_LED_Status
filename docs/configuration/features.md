---
description: The configuration for the features tab under the plugin's settings
---

# Features

Here's all the details of the additional features of the plugin, so you can effectively configure them.

## Torch

The torch button can be turned on or off to clear up navbar space if you don't want it. It has the same settings as [standard effects](printing-effects.md) but with some added extras for a manual trigger.

Using @ commands to trigger the torch can enable cool integrations with other software, such as OctoLapse.

### Toggle Mode

The torch button or [@ command](../documentation/host-commands.md) turns the torch on permanently, until it is turned off. This blocks any other effects.

### Timed Mode

The torch button starts a timer to turn off after configurable length of time.

### Auto activate when viewing webcam

The torch will turn on when the control tab is focused in OctoPrint's UI, and turn off when you click off to another tab.

{% hint style="info" %}
This may not work with plugins that change the default webcam stream location (such as UI customizer) or with some 3rd party apps. OctoApp for Android does support this \
however, see more in the [3rd Party Apps page](../3rd-party-apps-and-integrations.md#octoapp)
{% endhint %}

### Override active times

Allow the torch mode to be enabled regardless of the active times configuration.

## Active Times

The LED strip will turn on at the start time, off at the end time. Potentially useful if you don't want them on overnight.

{% hint style="warning" %}
Make sure your system time is set on the server. If you want to change this run `sudo raspi-config` on the Pi.
{% endhint %}

## M150 Intercept

Enable intercepting and using M150 commands. If not checked, these commands will be sent to the printer.

For documentation of the command, please see the [M150 Intercept documentation page.](../documentation/m150-intercept.md)

## @ Command Reaction

Enable reacting to Host @ Commands.

For documentation of the available commands, please see the [Host @ Commands documentation page](../documentation/host-commands.md)

## Debug Logging

Debug logging logs a lot more information about the effect runner process. This will help massively when reporting issues on GitHub, so please enable it when reporting issues!
