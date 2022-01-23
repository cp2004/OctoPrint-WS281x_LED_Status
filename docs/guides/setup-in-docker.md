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

The plugin needs access to the underlying hardware to drive the LEDs. To do this it will need to run privileged with docker.

{% hint style="info" %}
This guide assumes you are using the official [OctoPrint container](https://github.com/OctoPrint/octoprint-docker) and it's `docker-compose.yml` file.
{% endhint %}

Add the following mappings to `docker-compose.yml` under the `volumes:` section of the OctoPrint service

```yaml
volumes:
 - octoprint:/octoprint
```

To enable access to the hardware to drive the LEDs, the container must be run privileged:

```yaml
privileged: true
```

The final file should look something like this Gist:

{% embed url="https://gist.github.com/cp2004/5e32b021fca66e7167039a1737fd7f21" %}

{% hint style="warning" %}
The OS configuration test dialog will not pick up changes to enable SPI or set the correct core frequency without also adding these mappings to the container. You still need to configure SPI manually, as set out in the [SPI Setup section](setup-guide-1/spi-setup.md)
{% endhint %}
