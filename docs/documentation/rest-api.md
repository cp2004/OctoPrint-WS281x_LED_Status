---
description: >-
  Documentation for the plugin's API, which can be used to create custom
  controls etc. in other services.
---

# REST API

The plugin implements a [SimpleAPI as provided by OctoPrint](https://docs.octoprint.org/en/devel/plugins/mixins.html#simpleapiplugin), which enables external access to the plugin's functionality.

It has a single endpoint, supporting a get request and posting a command.

{% swagger baseUrl="http://octopi.local" path="/api/plugin/ws281x_led_status" method="get" summary="SimpleAPI Get" %}
{% swagger-description %}
Get current state of the plugin, which includes the light status and the torch status.
{% endswagger-description %}

{% swagger-parameter name="X-Api-Key" type="string" required="true" in="header" %}
A valid OctoPrint API key.
{% endswagger-parameter %}

{% swagger-response status="200" description="" %}
```javascript
{
  "lights_on": false,
  "torch_on": false
}
```
{% endswagger-response %}
{% endswagger %}

{% swagger baseUrl="http://octopi.local" path="/api/plugin/ws281x_led_status" method="post" summary="SimpleAPI Command" %}
{% swagger-description %}
Send commands to the plugin, to make it do something.
{% endswagger-description %}

{% swagger-parameter name="X-Api-Key" type="string" required="true" in="header" %}
A valid OctoPrint API key
{% endswagger-parameter %}

{% swagger-parameter name="command" type="string" required="true" in="body" %}
The command to be sent to the plugin. See commands below.
{% endswagger-parameter %}

{% swagger-response status="200" description="" %}
```javascript
{
  "lights_on": false,
  "torch_on": false
}
```
{% endswagger-response %}
{% endswagger %}

{% hint style="info" %}
See also the OctoPrint [SimpleApi docs](https://docs.octoprint.org/en/devel/plugins/mixins.html#octoprint.plugin.SimpleApiPlugin) for details about how the request should be structured.
{% endhint %}

## Commands

| Command          | Parameters | Explanation                                                                                            |
| ---------------- | ---------- | ------------------------------------------------------------------------------------------------------ |
| `lights_on`      | None       | Turn the LEDs on                                                                                       |
| `lights_off`     | None       | Turn the LEDs off                                                                                      |
| `lights_toggle`  | None       | Toggle the LED state                                                                                   |
| `torch_on`       | None       | Turn the torch mode on                                                                                 |
| `torch_off`      | None       | Turn the torch mode off. Only available if torch mode is configured as toggle.                         |
| `test_os_config` | None       | Begin an OS configuration test. Asynchronous, data is returned on the socket                           |
| `test_led`       | `color`    | Set the LEDs to the configured HTML RGB colour, color should be a full 7 character hex (eg. `#ff00ff`) |
