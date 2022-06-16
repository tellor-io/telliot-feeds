# Copyright (c) 2021-, Tellor Development Community
# Copyright (c) 2020, Nucleic Development Team.
import os

import pytest

example_folder = os.path.join(os.path.dirname(__file__), "..", "examples")
examples = list()
for (dir_path, _, filenames) in os.walk(example_folder):
    examples += [os.path.join(dir_path, f) for f in filenames]


@pytest.mark.parametrize("path", examples)
def test_example(path):
    """Run all examples"""
    with open(path, "r") as f:
        # If exec gets two separate objects as globals and locals, the code
        # will be executed as if it were embedded in a class definition, which
        # changes name look up rules
        exec(f.read(), locals(), locals())
