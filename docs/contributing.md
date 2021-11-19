# Contributing

## Development Environment Setup

*These instructions assume that a working Python interpreter (version >=3.8)
is already installed on the system.*

Clone the repository to a local working directory:

    git clone https://github.com/tellor-io/telliot-feed-examples.git

Create and activate a [virtual environment](https://docs.python.org/3/library/venv.html).  In this example, the virtual environment is 
located in a subfolder called `tenv`:

=== "Linux"

    ```
    python3 -m venv tenv
    source tenv/bin/activate
    ```

=== "Windows"

    ```
    py -m venv tenv
    tenv\Scripts\activate
    ```

Install the project using using an [editable installation](https://pip.pypa.io/en/stable/reference/pip_install/#editable-installs).

    pip install -e .
    pip install -r requirements-dev.txt


## Test Environment

Verify the development environment by running `pytest` and ensure that all tests pass.

    pytest

## Making Contributions

Once your dev environment is set up, make desired changes, create new tests for those changes,
and conform to the style & typing format of the project. To do so, in the project home directory:

Run all unit tests:

    pytest

Check code typing:

    tox -e typing

Check style (you may need run this step several times):

    tox -e style

Once all those pass, you're ready to make a pull request to the project's main branch.

Link any related issues, tag desired reviewers, and watch the [#telliot-feed-examples](https://discord.gg/URXVQdGjAT) channel in the
community discord for updates.


