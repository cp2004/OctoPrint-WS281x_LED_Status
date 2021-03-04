---
description: Detailed descriptions of the LED Strip Configuration dialog.
---

# LED Strip Configuration

This documentation aims to explain all of the settings in the LED Strip Configuration dialog, so you can make the most use of them.

### **Strip Settings**

| Setting | Value Type | Explanation |
| :--- | :--- | :--- |
| Strip Type | Selection | The type of strip you have connected, for a complete list see [supported hardware](../guides/setup-guide-1/supported-hardware.md#led-strips) |
| Number of LEDs | Number | I hope this one is obvious enough 🙂 |
| Max Brightness | Percentage | The maximum brightness the strip should reach in any effect. |
| GPIO Pin | Number | The pin that the LEDs are connected to. This should be BCM [GPIO 10](https://pinout.xyz/pinout/pin19_gpio10) for normal operation, other pins are available when OctoPrint is run as root and can use PWM - though this is explicitly **not recommended** for security reasons. |

### Colour Correction Settings

Colour correction settings allow you to adjust the colours globally on your LED strip. If your LEDs are off colour, you can adjust them here.

| Setting | Value Type | Explanation |
| :--- | :--- | :--- |
| Red correction | Percentage | The amount of red that should be used in the colour. |
| Blue correction | Percentage | See 'Red correction', but for blue |
| Green correction | Percentage | See 'Red correction', but for green |
| Use dedicated white | Checkbox | If you have an RGBW strip, check this to use the dedicated RGBW LEDs when the colour is 100% white. |
| White brightness | Percentage | The brightness of the dedicated white LEDs to use. |

### Advanced Settings

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
      <td style="text-align:left">Frequency</td>
      <td style="text-align:left">Number</td>
      <td style="text-align:left">Frequency to drive the LEDs at. This should be 800 000 in normal use,
        some older strips may require different values.</td>
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

### Manually editable settings

{% hint style="warning" %}
These settings should not be edited in standard use of the plugin. They are available \*just in case\* you need to edit them. Do not touch if you do not know what you are doing, serious issues with your Pi may occur if these are set wrong.
{% endhint %}

| Setting key | Value Type |
| :--- | :--- |
| `dma` | Should always be 10, the DMA channel that the LEDs will use. |
| `channel` | PWM channel to use for the LEDs. Since the plugin uses SPI in normal operation, this is not exposed in the UI. |

These settings can be edited from [`config.yaml`](https://docs.octoprint.org/en/devel/configuration/config_yaml.html), in the following format:

```yaml
plugins:
    ws281x_led_status:
        strip:
            dma: 10
            channel: 0
```

