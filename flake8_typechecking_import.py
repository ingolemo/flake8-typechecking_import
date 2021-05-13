"A flake plugin that checks for typing.TYPE_CHECKING-able imports"

__version__ = "0.1"

import ast
import dataclasses
from typing import Any, Generator

# from pprint import pprint


@dataclasses.dataclass
class Import:
    line: int
    column: int
    module: str
    identifiers: list[str]


whitelist = {
    "__future__",
    "typing",
}


def is_used(import_obj: Import, names: set[str]) -> bool:
    if import_obj.module in whitelist:
        return True
    return any(ident in names for ident in import_obj.identifiers)


def find_module_name(node: ast.ImportFrom) -> str:
    if node.module is not None:
        return node.module
    for alias in node.names:
        if alias.name is None:
            continue
        return alias.name.split(".")[0]
    raise Exception("unknown name")


def is_if_type_checking(node: ast.If) -> bool:
    if isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING":
        return True
    if (
        isinstance(node.test, ast.Attribute)
        and isinstance(node.test.value, ast.Name)
        and node.test.value.id == "typing"
        and node.test.attr == "TYPE_CHECKING"
    ):
        return True
    return False


class Visitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.imports: list[Import] = []
        self.names: set[str] = set()

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        for alias in node.names:
            name = alias.name.split(".")[0]
            identifier = alias.name if alias.asname is None else alias.asname
            identifier = identifier.split(".")[0]
            import_obj = Import(node.lineno, node.col_offset, name, [identifier])
            self.imports.append(import_obj)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        module = find_module_name(node)
        identifiers: list[str] = [
            alias.name if alias.asname is None else alias.asname for alias in node.names
        ]

        import_obj = Import(node.lineno, node.col_offset, module, identifiers)
        self.imports.append(import_obj)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:  # noqa: N802
        self.names.add(node.id)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:  # noqa: N802
        self.visit(node.target)
        if node.value is not None:
            self.visit(node.value)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        for argnode in node.args.defaults:
            self.visit(argnode)
        for subnode in node.body:
            self.visit(subnode)

    def visit_If(self, node: ast.If) -> None:  # noqa: N802
        if is_if_type_checking(node):
            return
        self.generic_visit(node)


class Plugin:
    name = __name__
    version = __version__

    def __init__(self, tree: ast.AST) -> None:
        self.tree = tree

    def run(self) -> Generator[tuple[int, int, str, type[Any]], None, None]:
        message = "TCI100 import {0!r} only necessary during TYPE_CHECKING"
        visitor = Visitor()
        visitor.visit(self.tree)
        # pprint(visitor.imports)
        # pprint(visitor.names)
        for import_obj in visitor.imports:
            if is_used(import_obj, visitor.names):
                continue
            line, col = import_obj.line, import_obj.column
            module = import_obj.module
            yield line, col, message.format(module), type(self)
