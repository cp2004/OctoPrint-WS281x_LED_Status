---
description: There are various utilities available to help with using the plugin.
---

# Utilities

{% hint style="info" %}
**These utilities are mostly provided for convenience,** I make no claim they are 100% accurate.
{% endhint %}

## LED Strip Test

### Solid colour buttons

These are helpful to test the individual colours of the LED strip, to make sure the hardware and software are configured correctly. Helpful to identify if you might have selected the wrong colour order in the LED strip configuration. Each button sets that colour to maximum intensity, to isolate the individual colours.

You can also set a custom colour to be sent to the LEDs.

### Effect test

This section allows for testing a configuration for an effect instantly, without needing to wait for the relevant event to occur. Configure the effect, colour and delay and then press 'Test'!

## OS Configuration Test

The popup box will run a configuration test on your OS. It tests for the same things that the [initial setup wizard does](guides/setup-guide-1/spi-setup.md#initial-setup-wizard), to allow you to verify everything is OK down the line.

At any time, you can run a test of the above settings, using the configuration test dialog. When you run the test, it will tell you if all of the steps are filled in correctly, and if they are not, prompt you to fix it with a click of a button.

This data is also logged to `octoprint.log` on startup, to help me with diagnosing issues reported to rule out this configuration being the problem.

## Power Calculation

Calculates the approximate power consumption of the LED strip. Useful to work out if your power supply is up-to-the task.

The nominal value included by default is 40mA, since this is what I have found to be most common. Brighter LEDs take more power, so adjust to what you think is right for your strips.
