# Contribution Guidelines

First, thank you for considering contributing to this project!

The guidelines here aim to make it as smooth as possible for contributors to understand how to contribute, what they can contribute
and how the plugin works.

There's a couple of things to consider before making your contribution:

- Please create pull requests against the `devel` branch unless indicated otherwise.
  There is an exception to this rule: documentation. See more below.

- If your changes are large or disruptive, please open an issue first so that we can discuss. I don't want you to put in a lot
  of work only for it to end up going to waste as there were already different plans.

- Read the additional points below for details on code style, testing and how everything fits together.

### Documentation

Contributing documentation changes is easy, since everything is formatted using markdown. The docs are built from
the `docs` sub folder by GitBook, hosted at https://cp2004.gitbook.io/ws281x-led-status/.

For the documentation for the current release of the plugin, please make it against the branch labelled for the minor version. (Currently `0.7.x`)
This means that I can keep them versioned and not break things between releases.

When contributing additional features or configuration please try to document it where necessary, however do not put
off your contribution because you are struggling to document it!

### Code style

The plugin has a pre-commit setup that runs black, prettier, isort and various other code-mods.

You can either set this up as a file watcher [as in the PyCharm example in OctoPrint's documentation (under pre-commit)](https://docs.octoprint.org/en/master/development/environment.html#pycharm).

You can also run this as a one-off using `pre-commit run --hook-stage manual --all-files`.

### Testing

Running the unit tests is simple, though they require additional dependencies.

If you installed OctoPrint in a development environment, using `pip install octoprint[develop]` or `pip install -e .[develop]` (in the checkout)
these are already there. Otherwise, install them using `pip install pytest mock`

Run it: `pytest` (or `python -m pytest`)

### Anything else?

Nothing else important! Give your PR a suitable description and let me merge it :)
