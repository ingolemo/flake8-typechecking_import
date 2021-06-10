#!/usr/bin/env sh

module_name='flake8_typechecking_import'

test -e ./venv/bin/python || exit 1
export PATH="$(pwd)/venv/bin:$PATH"
python -m pip install flit || exit 1
python -m flit install || exit 1

mypy --strict -m "$module_name" || exit 1
flake8 --max-complexity 10 "$module_name".py
black --check "$module_name".py || exit 1

pytest
