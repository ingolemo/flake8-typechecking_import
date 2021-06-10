"A flake plugin that checks for typing.TYPE_CHECKING-able imports"

__version__ = "0.4"

import ast
import dataclasses
from typing import Generator, List, Set, Tuple, Type


@dataclasses.dataclass
class Import:
    line: int
    column: int
    module: str
    identifiers: List[str]
    type_checking: bool = False

    def is_used(self: "Import", names: Set[str]) -> bool:
        if self.module in whitelist:
            return True
        return any(ident in names for ident in self.identifiers)


@dataclasses.dataclass
class Name:
    identifier: str
    type_checking: bool = False


@dataclasses.dataclass
class Result:
    imports: List[Import]
    names: List[Name]

    @classmethod
    def new(cls) -> "Result":
        return Result([], [])

    def combine(self, other: "Result") -> "Result":
        return Result(self.imports + other.imports, self.names + other.names)

    def set_type_checking(self, *, imports: bool = False) -> None:
        for name in self.names:
            name.type_checking = True
        if imports:
            for import_obj in self.imports:
                import_obj.type_checking = True

    def regular_names(self) -> Set[str]:
        return {name.identifier for name in self.names if not name.type_checking}

    def typing_names(self) -> Set[str]:
        return {name.identifier for name in self.names if name.type_checking}


whitelist = {
    "__future__",
    "typing",
}


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
    def visit(self, node: ast.AST) -> Result:
        result = super().visit(node)
        assert isinstance(result, Result)
        return result

    def generic_visit(self, node: ast.AST) -> Result:
        result = Result.new()
        for node in ast.iter_child_nodes(node):
            result = result.combine(self.visit(node))
        return result

    def visit_Import(self, node: ast.Import) -> Result:  # noqa: N802
        result = self.generic_visit(node)
        for alias in node.names:
            name = alias.name.split(".")[0]
            identifier = alias.name if alias.asname is None else alias.asname
            identifier = identifier.split(".")[0]
            import_obj = Import(node.lineno, node.col_offset, name, [identifier])
            result.imports.append(import_obj)
        return result

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Result:  # noqa: N802
        module = find_module_name(node)
        identifiers: List[str] = [
            alias.name if alias.asname is None else alias.asname for alias in node.names
        ]

        result = self.generic_visit(node)
        import_obj = Import(node.lineno, node.col_offset, module, identifiers)
        result.imports.append(import_obj)
        return result

    def visit_Name(self, node: ast.Name) -> Result:  # noqa: N802
        result = self.generic_visit(node)
        result.names.append(Name(node.id))
        return result

    def visit_AnnAssign(self, node: ast.AnnAssign) -> Result:  # noqa: N802
        result = self.visit(node.target)
        if node.value is not None:
            result = result.combine(self.visit(node.value))
        type_result = self.visit(node.annotation)
        type_result.set_type_checking()
        return result.combine(type_result)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Result:  # noqa: N802
        type_result = Result.new()
        result = Result.new()
        if node.returns:
            type_result = type_result.combine(self.visit(node.returns))
        for arg in node.args.args:
            if arg.annotation is None:
                continue
            type_result = type_result.combine(self.visit(arg.annotation))
        for defaults in node.args.defaults:
            result = result.combine(self.visit(defaults))
        for subnode in node.body:
            result = result.combine(self.visit(subnode))
        type_result.set_type_checking()
        return result.combine(type_result)

    def visit_If(self, node: ast.If) -> Result:  # noqa: N802
        result = self.generic_visit(node)
        if is_if_type_checking(node):
            result.set_type_checking(imports=True)
        return result


class Plugin:
    name = __name__
    version = __version__

    def __init__(self, tree: ast.AST) -> None:
        self.tree = tree

    def run(self) -> Generator[Tuple[int, int, str, Type["Plugin"]], None, None]:
        message = "TCI100 import {0!r} only necessary during TYPE_CHECKING"
        visitor = Visitor()
        result = visitor.visit(self.tree)
        typing_names = result.typing_names()
        regular_names = result.regular_names()
        for import_obj in result.imports:
            if import_obj.type_checking:
                continue
            if not import_obj.is_used(typing_names):
                continue
            if import_obj.is_used(regular_names):
                continue
            line, col = import_obj.line, import_obj.column
            module = import_obj.module
            yield line, col, message.format(module), type(self)
