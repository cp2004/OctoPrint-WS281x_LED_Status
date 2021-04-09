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

The plugin needs to be able to access 3 files to run. These are:

* `/boot/config.txt`
* `/boot/commandline.txt`
* `/proc/device-tree/model`

It also needs access to the underlying hardware to drive the LEDs. To do this it will need to run privileged with docker.

{% hint style="info" %}
This guide assumes you are using the official [OctoPrint container](https://github.com/OctoPrint/octoprint-docker) and it's `docker-compose.yml` file.
{% endhint %}

Add the following mappings to `docker-compose.yml` under the `volumes:` section of the OctoPrint service

```yaml
volumes:
 - octoprint:/octoprint
 - /boot/config.txt:/boot/config.txt
 - /boot/cmdline.txt:/boot/cmdline.txt
```

To enable access to the hardware to drive the LEDs, the container must be run privileged:

```yaml
privileged: true
```

The final file should look something like this Gist: [https://gist.github.com/cp2004/5e32b021fca66e7167039a1737fd7f21](https://gist.github.com/cp2004/5e32b021fca66e7167039a1737fd7f21)

{% hint style="warning" %}
Version 0.6.0 of the plugin **requires these files to exist** on the system for the UI to work. When these don't exist, it crashes the web UI.

Even if your system doesn't use these files, they must exist - just skip the wizard and it will not add anything to them

You may still need to use the [SPI setup guide](setup-guide-1/spi-setup.md), adjusting the paths.
{% endhint %}

