---
description: WS281x LED Status will intercept M150 commands to control the LEDs.
---

# M150 Intercept

Commands should be formatted as such:

`M150 [P{intensity}] [R{intensity}] [G{intensity}] [B{intensity}] [W{intensity}]`

| Parameter | Explanation |
| :--- | :--- |
| `P` | Brightness, max 255. If not included, defaults to maximum brightness in the settings |
| `R` | Red intensity, max 255. |
| `G` | Green intensity, max 255. Can also be `U` for Marlin compatibility. |
| `B` | Blue intensity, max 255. |
| `W` | White intensity, max 255. |

All of the parameters are optional, and can be included in any order. If an option is not included, its value is 0 - as a result sending an empty `M150` command will turn the LEDs off.

{% hint style="warning" %}
It's not recommended to send an empty `M150`, and instead use [@ commands](host-commands.md) to turn the LEDs on and off.
{% endhint %}

Examples:

```text
M150 R255 G255  # Sets LEDs to yellow
M150 G238 B255  # Sets to light-ish blue
M150 W100       # Sets to white, at 100 intensity
M150 R255 P200  # Sets LEDs to red, at 200 brightness
```

