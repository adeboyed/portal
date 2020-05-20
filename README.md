# Portal

[![GitHub license](https://img.shields.io/badge/license-Apache-blue.svg)](https://github.com/adeboyed/portal/blob/master/LICENSE)


`portal` is a command line tool for running commands with no dependencies.
Instead of installing a language stack, dependencies, libraries and more, use docker containers to run commands as if they were installed on your local machine.
It removes a lot of the bookeeping required to transfer data and files to and from the docker container.

## Example
Next time you want to want to run a simple


    portal [COMMAND] [COMMAND OPTIONS]

e.g. for http-server

    portal http-server public

## Installation

Portal requires Python 3+ to run and Docker to be installed.

### Simple Installation

    pip install -r requirements.txt # Install required pip dependencies
    make
    make install

### Developer Installation

If you need to make changes/test out a new command, you can use `portal` directly as a Python module

    pip install -r requirements.txt # Install required pip dependencies
    python -m portalcli


## Supported Commands

- http-server
- cwebp
- httpie
- gollum
- shellcheck
- openapi-generator-cli
- [And more!](./wiki/COMMANDS.md)


## Documentation

- [List of supported commands](./wiki/COMMANDS.md)
- [How to add a new command](./wiki/ADD_NEW_COMMAND.md)


## License

Portal is [Apache licensed](./LICENSE).
