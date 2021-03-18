---
description: >-
  Documentation for the plugin's API, which can be used to create custom
  controls etc. in other services.
---

# REST API

The plugin implements a [SimpleAPI as provided by OctoPrint](https://docs.octoprint.org/en/devel/plugins/mixins.html#simpleapiplugin), which enables external access to the plugin's functionality.

It has a single endpoint, supporting a get request and posting a command.

{% api-method method="get" host="http://octopi.local" path="/api/plugin/ws281x\_led\_status" %}
{% api-method-summary %}
SimpleAPI Get
{% endapi-method-summary %}

{% api-method-description %}
Get current state of the plugin, which includes the light status and the torch status.
{% endapi-method-description %}

{% api-method-spec %}
{% api-method-request %}
{% api-method-headers %}
{% api-method-parameter name="X-Api-Key" type="string" required=true %}
A valid OctoPrint API key.
{% endapi-method-parameter %}
{% endapi-method-headers %}
{% endapi-method-request %}

{% api-method-response %}
{% api-method-response-example httpCode=200 %}
{% api-method-response-example-description %}
Details of the plugin's current state
{% endapi-method-response-example-description %}

```javascript
{
  "lights_on": false,
  "torch_on": false
}
```
{% endapi-method-response-example %}
{% endapi-method-response %}
{% endapi-method-spec %}
{% endapi-method %}

{% api-method method="post" host="http://octopi.local" path="/api/plugin/ws281x\_led\_status" %}
{% api-method-summary %}
SimpleAPI Command
{% endapi-method-summary %}

{% api-method-description %}
Send commands to the plugin, to make it do something.
{% endapi-method-description %}

{% api-method-spec %}
{% api-method-request %}
{% api-method-headers %}
{% api-method-parameter name="X-Api-Key" type="string" required=true %}
A valid OctoPrint API key
{% endapi-method-parameter %}
{% endapi-method-headers %}

{% api-method-body-parameters %}
{% api-method-parameter name="command" type="string" required=true %}
The command to be sent to the plugin. See commands below.
{% endapi-method-parameter %}
{% endapi-method-body-parameters %}
{% endapi-method-request %}

{% api-method-response %}
{% api-method-response-example httpCode=200 %}
{% api-method-response-example-description %}

{% endapi-method-response-example-description %}

```javascript
{
  "lights_on": false,
  "torch_on": false
}
```
{% endapi-method-response-example %}
{% endapi-method-response %}
{% endapi-method-spec %}
{% endapi-method %}

{% hint style="info" %}
See also the [SimpleApi docs](https://docs.octoprint.org/en/devel/plugins/mixins.html#octoprint.plugin.SimpleApiPlugin) for details about how the request should be structured.
{% endhint %}

## Commands

| Command | Parameters | Explanation |
| :--- | :--- | :--- |
| `lights_on` | None | Turn the LEDs on |
| `lights_off` | None | Turn the LEDs off |
| `torch_on` | None | Turn the torch mode on |
| `torch_off` | None | Turn the torch mode off. Only available if torch mode is configured as toggle. |
| `test_os_config` | None | Begin an OS configuration test. Asynchronous, data is returned on the socket |
| `test_led` | `color` | Set the LEDs to the configured HTML RGB colour, color should be a full 7 character hex \(eg. `#ff00ff`\) |

{% hint style="info" %}
There are also API commands available for OS configuration options. However, it is not recommended that these are used by anything other than the plugin itself, so they are undocumented. They may be restricted further in the future.
{% endhint %}

