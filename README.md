# btclib_node

[btclib_node](https://github.com/btclib-org/btclib_node) is a bitcoin node with its consensus and network code written in python, using the [btclib](https://github.com/btclib-org/btclib) bitcoin library.

**btclib_node** succeded in downloading and validating the entire bitcoin blokchain, starting from version 0.1.0 and, as far as I can tell, is the first python implementatin that was able to do so

## Test, develop, and contribute

The project uses [hatch](https://hatch.pypa.io/latest/) as a project manager.

Some additional tools are required to develop and test btclib_node, they can be installed using poetry:

    poetry install

To test:

    pytest

To measure the code coverage provided by tests:

    pytest --cov-report term-missing:skip-covered --cov=btclib_node

To format the code

    isort . && black .
