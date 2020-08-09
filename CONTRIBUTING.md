### Hey there! So you've decided to contribute to the plugin. Here's what you need to know.

Please take note of the few things below for contributing to the plugin, it's not extensive and designed to make contributions as smooth as possible

* Please only create pull requests against:
  * `maintenance` for bug fixes or improvements
  * `devel` for new features
  * Never `master`, as this is downloaded by users so must remain untouched until release. (EXCEPTION: Documentation, like this)
* If your changes are large or disruptive, please open an issue first to dicuss. There may be things in the pipeline that would conflict
* Read the detail below so you understand how the plugin works!

### How does it work?

This plugin is currently written with 2 layers:
* The OctoPrint plugin class,
* The effect runner class.

When a user starts the plugin, OctoPrint loads the plugin class. This spins off a new process of the effect runner class, which handles driving the LEDs

Operating flow goes a bit like this:

* Event recieved by the plugin class (This may be an OctoPrint event, gcode command or pressing the on/off button.)
* Evaluated, and decide what to do happens plugin side. Message constructed
* Message put in a queue through to the effect runner class. Any active effect is stopped immediately and message is read
* Analyse message, and decide what effect to run

All effects are kept in the sub-module `effects`, while there are useful functions that can be called cross module in the `util.py` file
