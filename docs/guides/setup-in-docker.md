---
description: >-
  Using OctoPrint in a docker container? You need to do some slightly different
  config.
---

# Setup in Docker

{% hint style="warning" %}
This step is **not required** if you are not using a docker container. The standard setup guide can be found [here](setup-guide-1/)

You will still need to follow the full setup guide, this is **additional.**
{% endhint %}

{% hint style="info" %}
This guide assumes you are using the official [OctoPrint container](https://github.com/OctoPrint/octoprint-docker) and it's `docker-compose.yml` file.
{% endhint %}

The plugin needs access to two things for driving LEDs:

* `/proc/device-tree/model`
* The underlying hardware of the Raspberry Pi.

To enable access to the hardware to drive the LEDs, the container must be run privileged. So set this under `services: octoprint:` 

```yaml
privileged: true
```

The final file should look something like this Gist: [https://gist.github.com/cp2004/5e32b021fca66e7167039a1737fd7f21](https://gist.github.com/cp2004/5e32b021fca66e7167039a1737fd7f21)

{% hint style="warning" %}
The plugin's [OS configuration test](../utilities.md#os-configuration-test) will look for `/boot/config.txt` and  `/boot/cmdline.txt` files to set the options there. These will not be available to OctoPrint in docker, so you must either map them or adjust the content manually as per the [SPI Setup Guide](setup-guide-1/spi-setup.md)
{% endhint %}

