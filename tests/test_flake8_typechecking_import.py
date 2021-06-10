from typing import List, Set
import ast

from flake8_typechecking_import import Plugin


def _results(lines: List[str]) -> Set[str]:
    data = "\n".join(lines)
    tree = ast.parse(data)
    plugin = Plugin(tree)
    return {msg.split(" ")[0] for line, col, msg, _ in plugin.run()}


def test_trivial_case() -> None:
    assert _results([""]) == set()


def test_unused_import() -> None:
    lines = ["import mod"]
    assert _results(lines) == set()
    lines = ["import mod as alias"]
    assert _results(lines) == set()


def test_used_import() -> None:
    lines = ["import mod", "mod"]
    assert _results(lines) == set()
    lines = ["import mod as alias", "alias"]
    assert _results(lines) == set()


def test_annotation() -> None:
    lines = ["import mod", "var: mod"]
    assert _results(lines) == {"TCI100"}
    lines = ["import mod as alias", "var: alias"]
    assert _results(lines) == {"TCI100"}


def test_annotated_assignment() -> None:
    lines = ["import mod", "var: mod = []"]
    assert _results(lines) == {"TCI100"}
    lines = ["import mod as alias", "var: alias = []"]
    assert _results(lines) == {"TCI100"}


def test_annotated_assignment_value() -> None:
    lines = ["import mod", "var: type = mod"]
    assert _results(lines) == set()
    lines = ["import mod as alias", "var: type = alias"]
    assert _results(lines) == set()


def test_multiple_unused_imports() -> None:
    lines = ["import mod", "import pack"]
    assert _results(lines) == set()
    lines = ["import mod as mod_alias", "import pack as pack_alias"]
    assert _results(lines) == set()


def test_function_arguments() -> None:
    lines = ["def func(arg):", "    pass"]
    assert _results(lines) == set()
    lines = ["import mod", "def func(arg: pack):", "    pass"]
    assert _results(lines) == set()
    lines = ["import mod", "def func(arg: pack):", "    mod"]
    assert _results(lines) == set()
    lines = ["import mod", "def func(arg: mod):", "    pass"]
    assert _results(lines) == {"TCI100"}
    lines = ["import mod", "def func(arg=mod.Data):", "    pass"]
    assert _results(lines) == set()
    lines = ["import mod", "def func(arg: mod.Data):", "    pass"]
    assert _results(lines) == {"TCI100"}


def test_package() -> None:
    lines = ["import pack.mod"]
    assert _results(lines) == set()
    lines = ["import pack.mod", "pack"]
    assert _results(lines) == set()


def test_unused_type_checking() -> None:
    lines = ["import typing", "if typing.TYPE_CHECKING:", "    import mod"]
    assert _results(lines) == set()
    lines = ["from typing import TYPE_CHECKING", "if TYPE_CHECKING:", "    import mod"]
    assert _results(lines) == set()


def test_annotated_type_checking() -> None:
    lines = ["import typing", "if typing.TYPE_CHECKING:", "    import mod", "var: mod"]
    assert _results(lines) == set()
    lines = [
        "from typing import TYPE_CHECKING",
        "if TYPE_CHECKING:",
        "    import mod",
        "var: mod",
    ]
    assert _results(lines) == set()


def test_non_type_checking_if() -> None:
    lines = ["if True:", "    var = 0"]
    assert _results(lines) == set()


def test_shadowing() -> None:
    lines = ["import mod", "mod = 0", "var: mod.type = 0"]
    assert _results(lines) == set()
    # FIXME: handle shadowing of variables
    # lines = ["import mod", "var: mod.type = 0", "mod = 0"]
    # assert _results(lines) == {"TCI100"}


def test_function_return() -> None:
    lines = ["import mod", "def func() -> mod:", "    pass"]
    assert _results(lines) == {"TCI100"}


def test_relative_imports() -> None:
    lines = ["from . import mod"]
    assert _results(lines) == set()
    lines = ["from . import mod", "var = mod.value"]
    assert _results(lines) == set()
    lines = ["from . import mod", "var: mod.Type = 0"]
    assert _results(lines) == {"TCI100"}
    lines = ["from . import mod", "var: mod.Type = mod.value"]
    assert _results(lines) == set()
