---
description: There are various utilities available to help with using the plugin.
---

# Utilities

{% hint style="info" %}
**These utilities are provided for convenience,** I make no claim they are 100% accurate.
{% endhint %}

## LED Strip Test

{% hint style="warning" %}
**Requires M150 intercept to be enabled & printer to be connected.** This is due to a small shortcut, which is adjusted in a future version.
{% endhint %}

Press the 4 buttons to check that each segment of your LEDs are working. Useful if the colours are showing wrong, some LEDs don't work or anything hardware related. Each button sets that colour to maximum intensity, to isolate the individual colours.

You can also set a specific colour to test using the colour input and hitting the button.

## OS Configuration Test

The popup box will run a configuration test on your OS. It tests for the same things that the [initial setup wizard does](guides/setup-guide-1/spi-setup.md#initial-setup-wizard), to allow you to verify everything is OK down the line.

At any time, you can run a test of the above settings, using the configuration test dialog. When you run the test, it will tell you if all of the steps are filled in correctly, and if they are not, prompt you to fix it with a click of a button.

This data is also logged to `octoprint.log` on startup, to help me with diagnosing issues reported to rule out this configuration being the problem.

## Power Calculation

Calculates the approximate power consumption of the LED strip. Useful to work out if your power supply is up-to-the task.

The nominal value included by default is 40mA, since this is what I have found to be most common. Brighter LEDs take more power, so adjust to what you think is right for your strips.

{% hint style="warning" %}
Using 12V LEDs? The default value is probably way off, adjust this first!
{% endhint %}

