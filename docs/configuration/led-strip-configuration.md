---
description: Detailed descriptions of the LED Strip Configuration dialog.
---

# LED Strip Configuration

This documentation aims to explain all of the settings in the LED Strip Configuration dialog, so you can make the most use of them.

<table>
  <thead>
    <tr>
      <th style="text-align:left">Setting</th>
      <th style="text-align:left">Value Type</th>
      <th style="text-align:left">Explanation</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="text-align:left">Strip Type</td>
      <td style="text-align:left">Selection</td>
      <td style="text-align:left">The type of strip you have connected, for a complete list see supported
        hardware</td>
    </tr>
    <tr>
      <td style="text-align:left">Max Brightness</td>
      <td style="text-align:left">Percentage</td>
      <td style="text-align:left">The maximum brightness the strip should reach in any effect.</td>
    </tr>
    <tr>
      <td style="text-align:left">Number of LEDs</td>
      <td style="text-align:left">Number</td>
      <td style="text-align:left">I hope this one is obvious enough &#x1F642;</td>
    </tr>
    <tr>
      <td style="text-align:left">GPIO Pin</td>
      <td style="text-align:left">Number</td>
      <td style="text-align:left">The pin that the LEDs are connected to. This should be BCM <a href="https://pinout.xyz/pinout/pin19_gpio10">GPIO 10</a> for
        normal operation, other pins are available when OctoPrint is run as root
        and can use PWM - though this is explicitly <b>not recommended </b>for security
        reasons.</td>
    </tr>
    <tr>
      <td style="text-align:left">Frequency</td>
      <td style="text-align:left">Number</td>
      <td style="text-align:left">Frequency to drive the LEDs at. This should be 800 000 in normal use,
        some older strips may require different values.</td>
    </tr>
    <tr>
      <td style="text-align:left">DMA Channel</td>
      <td style="text-align:left">Number</td>
      <td style="text-align:left">
        <p><em>(To be removed from the UI in a future version)</em>
        </p>
        <p><b>Do not change the DMA channel if you do not know what you are doing.</b> 
        </p>
        <p>This should be 10 in normal use, other values can cause severe problems.</p>
      </td>
    </tr>
    <tr>
      <td style="text-align:left">Invert Pin output</td>
      <td style="text-align:left">Checkbox</td>
      <td style="text-align:left">Invert the signal from the Raspberry Pi. Useful if your setup uses a level
        shifter that inverts the signal, it can be inverted again to make it the
        right way around in the end.</td>
    </tr>
    <tr>
      <td style="text-align:left">PWM Channel</td>
      <td style="text-align:left">Number</td>
      <td style="text-align:left">
        <p><em>(To be removed from the UI in a future version)</em> 
        </p>
        <p>Internal PWM Channel. Irrelevant to the plugin since it uses SPI in most
          cases.</p>
      </td>
    </tr>
  </tbody>
</table>

{% hint style="warning" %}
DMA Channel and PWM channel will remain available for editing using config.yaml, just in case you need to change this. You probably won't.
{% endhint %}



