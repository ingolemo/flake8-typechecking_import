#!/usr/bin/env sh

export MYPYPATH="$(pwd)/stubs"
module_name='flake8_typechecking_import'

mypy --strict -m "$module_name" || exit 1
flake8 --max-complexity 10 "$module_name".py
black --check stubs "$module_name".py || exit 1

export PATH="$(pwd)/venv/bin:$PATH"
python -m pip install flit || exit 1
python -m flit install || exit 1
pytest
