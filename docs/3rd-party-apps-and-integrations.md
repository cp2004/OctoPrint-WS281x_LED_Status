---
description: 'WS281x LED Status is compatible with 3rd party apps, find out more here!'
---

# 3rd Party Apps and Integrations

## Native Integration

These apps have built in support for WS281x LED Status, allowing you to control your LEDs directly within them. Thank you to their respective developers for implementing support!

### [OctoApp](https://play.google.com/store/apps/details?id=de.crysxd.octoapp&hl=en_GB&gl=US)

OctoApp has built in support for buttons that can turn your LEDs on and off or activate the 'torch' mode. It also has support for the 'automatic torch on when viewing the webcam' feature, so you can see your prints easily. See a quick demo of this in action, check out the video below:

{% embed url="https://www.youtube.com/watch?v=TeuOlUE25gQ" %}

{% hint style="info" %}
App developer interested in creating a native integration? Checkout the [REST API documentation](documentation/rest-api.md) to get started.
{% endhint %}

## Non-native integration

Not all apps can integrate with every plugin, so many of them choose to support [Host @ Commands](documentation/host-commands.md) instead. This allows you, as the user to define custom controls that use these commands as you wish and use them in a variety of 3rd party apps.

Here are some examples of apps that support Host @ Commands:

* [OctoDash](https://unchartedbull.github.io/OctoDash/index.html)
* [OctoLapse](https://plugins.octoprint.org/plugins/octolapse/)
* [PSU Control](https://plugins.octoprint.org/plugins/psucontrol/)

{% hint style="info" %}
Found a cool plugin or other 3rd party software that uses action commands? Please contribute to the list!
{% endhint %}

