# pretix ticket request

This is a plugin for [pretix](https://github.com/pretix/pretix).

## Development setup

1. Make sure that you have a working [pretix development setup](https://docs.pretix.eu/en/latest/development/setup.html).

2. Clone this repository, eg to `local/pretix-ticket-request`.

3. Activate the virtual environment you use for pretix development. Run `source source env/bin/activate` in the pretix folder.

4. Execute `python setup.py develop` within this directory to register this application with pretix's plugin registry.

5. Execute `make` within this directory to compile translations.

6. Restart your local pretix server. You can now use the plugin from this repository for your events by enabling it in
   the 'plugins' tab in the settings.

## License

Copyright 2019 Orlando Del Aguila

Released under the terms of the Apache License 2.0
