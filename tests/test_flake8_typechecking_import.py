import ast
from flake8_typechecking_import import Plugin


def _results(lines: list[str]) -> set[str]:
    data = "\n".join(lines)
    tree = ast.parse(data)
    plugin = Plugin(tree)
    return {msg.split(" ")[0] for line, col, msg, _ in plugin.run()}


def test_trivial_case():
    assert _results("") == set()


def test_unused_import():
    lines = ["import mod"]
    assert _results(lines) == {"TCI100"}
    lines = ["import mod as alias"]
    assert _results(lines) == {"TCI100"}


def test_used_import():
    lines = ["import mod", "mod"]
    assert _results(lines) == set()
    lines = ["import mod as alias", "alias"]
    assert _results(lines) == set()


def test_annotation():
    lines = ["import mod", "var: mod"]
    assert _results(lines) == {"TCI100"}
    lines = ["import mod as alias", "var: alias"]
    assert _results(lines) == {"TCI100"}


def test_annotated_assignment():
    lines = ["import mod", "var: mod = []"]
    assert _results(lines) == {"TCI100"}
    lines = ["import mod as alias", "var: alias = []"]
    assert _results(lines) == {"TCI100"}


def test_annotated_assignment_value():
    lines = ["import mod", "var: type = mod"]
    assert _results(lines) == set()
    lines = ["import mod as alias", "var: type = alias"]
    assert _results(lines) == set()


def test_multiple_unused_imports():
    lines = ["import mod", "import pack"]
    assert _results(lines) == {"TCI100"}
    lines = ["import mod as mod_alias", "import pack as pack_alias"]
    assert _results(lines) == {"TCI100"}


def test_function_arguments():
    lines = ["import mod", "def func(arg: pack):", "    pass"]
    assert _results(lines) == {"TCI100"}
    lines = ["import mod", "def func(arg: pack):", "    mod"]
    assert _results(lines) == set()
    lines = ["import mod", "def func(arg: mod):", "    pass"]
    assert _results(lines) == {"TCI100"}
    lines = ["import mod", "def func(arg: mod.Data):", "    pass"]
    assert _results(lines) == {"TCI100"}


def test_package():
    lines = ["import pack.mod"]
    assert _results(lines) == {"TCI100"}
    lines = ["import pack.mod", "pack"]
    assert _results(lines) == set()
