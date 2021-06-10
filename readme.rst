
Flake8-Typechecking_Import
==========================

A plugin for flake8 that checks your code for imports that are
only used in annotations. These imports can then be moved under an
``if typing.TYPE_CHECKING:`` block to prevent them being imported at
runtime. This can minimise the number of runtime dependencies that your
modules have and perhaps also reduce the likelyhood of a circular import.

For example:

.. code:: python

    import dataclasses
    import datetime

    @dataclasses.dataclass
    class Person:
        name: str
        birthday: datetime.date

The above code will emit a lint (code: TCI100) telling you that it can
be converted to this:

.. code:: python

    import dataclasses
    import typing

    if typing.TYPE_CHECKING:
        import datetime

    @dataclasses.dataclass
    class Person:
        name: str
        birthday: datetime.date

You can install the latest version from pypi using pip like so::

    pip install flake8-typechecking_import
