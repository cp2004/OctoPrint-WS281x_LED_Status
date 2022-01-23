---
description: Describes how to use the torch effect to simulate a flash for OctoLapse.
---

# OctoLapse Timelapse Flash

**Using WS281x LEDs to create a flash for a timelapse**

By using the power of [@ commands](../documentation/host-commands.md) it is very easy to make your LEDs react to other plugins that use GCODE scripts. For example, to make the LEDs flash for the timelapse, to light it up, you can use the following settings:

* Enable **'Torch mode is a toggle'** in the WS281x LED Status settings, and set the torch effect to solid colour & bright white (and colour will do, but white is the most common!)
* **OctoLapse** Custom Camera Gcode Scripts
  *   **Before snapshot**:

      ```
      @WS LIGHTS_ON
      @WS TORCH_ON
      ```
  *   **After Snapshot**

      ```
      @WS TORCH_OFF
      @WS LIGHTS_OFF; (Optional) Turn the lights off afterwards
      ```

That's it! You can run OctoLapse in test mode to test it out.
