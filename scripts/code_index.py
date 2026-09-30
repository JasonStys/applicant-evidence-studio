"""Generate exact Python declaration/variable line maps without hand-maintained stale comments."""

# Index: argparse@4, ast@5, Path@6, ROOT@8, Symbols@11, Symbols.__init__@14, Symbols.__init__.self@14, Symbols.record@19, Symbols.record.line@19, Symbols.record.name@19, Symbols.record.self@19, Symbols.visit_ClassDef@23, Symbols.visit_ClassDef.node@23, Symbols.visit_ClassDef.self@23, Symbols.visit_FunctionDef@30, Symbols.visit_FunctionDef.node@30, Symbols.visit_FunctionDef.self@30, Symbols.visit_AsyncFunctionDef@37, Symbols.visit_arg@39, Symbols.visit_arg.node@39, Symbols.visit_arg.self@39, Symbols.visit_Name@43, Symbols.visit_Name.node@43, Symbols.visit_Name.self@43, Symbols.visit_alias@48, Symbols.visit_alias.node@48, Symbols.visit_alias.self@48, main@53, main.parser@55, main.args@57, main.report@58, main.stale@64, main.path@65, main.item@67, main.source@69, main.lines@70, main.index@71, main.line@71, main.marker@71, main.visitor@74, main.item@76, main.symbols@76, main.line@78, main.name@78, main.updated@80, main.relative@85, main.report@86, main.line@87, main.name@87, main.report@87, main.document@89, main.text@90
import argparse
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Symbols(ast.NodeVisitor):
    """Collect lexical declarations, parameters and written variables, not runtime coverage."""

    def __init__(self):
        """Start a scope stack and a deduplicated name/location mapping."""
        self.scope = []
        self.symbols = set()

    def record(self, name, line):
        """Qualify symbols with their class/function scope and exact source line."""
        self.symbols.add((".".join([*self.scope, name]), line))

    def visit_ClassDef(self, node):
        """Record a class and recursively inspect its body in a new scope."""
        self.record(node.name, node.lineno)
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_FunctionDef(self, node):
        """Record a callable and its argument bindings and local writes."""
        self.record(node.name, node.lineno)
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_arg(self, node):
        """Record parameter variables including keyword-only parameters."""
        self.record(node.arg, node.lineno)

    def visit_Name(self, node):
        """Record assignments, loops and comprehension bindings, but not every read."""
        if isinstance(node.ctx, ast.Store):
            self.record(node.id, node.lineno)

    def visit_alias(self, node):
        """Include imported bindings so used external functions/classes are discoverable."""
        self.record(node.asname or node.name.split(".")[0], node.lineno)


def main():
    """Refresh stable one-line file headers and the full documentation index; --check is read-only."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = [
        "# Python declaration and variable map",
        "",
        "Generated from Python AST. Names are lexical bindings; attributes/dynamic values are not exhaustive runtime tracing.",
        "",
    ]
    stale = []
    for path in sorted(
        [*ROOT.glob("app/*.py"), *ROOT.glob("tests/*.py"), *ROOT.glob("scripts/*.py")],
        key=lambda item: item.relative_to(ROOT).as_posix(),
    ):
        source = path.read_text(encoding="utf-8")
        lines = source.splitlines()
        marker = next((index for index, line in enumerate(lines) if line.startswith("# Index:")), None)
        if marker is None:
            raise SystemExit(f"Header index missing: {path.name}")
        visitor = Symbols()
        visitor.visit(ast.parse(source))
        symbols = sorted(visitor.symbols, key=lambda item: (item[1], item[0]))
        lines[marker] = "# Index: " + (
            ", ".join(f"{name}@{line}" for name, line in symbols) if symbols else "(no lexical bindings)"
        )
        updated = "\n".join(lines) + "\n"
        if updated != source:
            stale.append(path.relative_to(ROOT).as_posix())
            if not args.check:
                path.write_text(updated, encoding="utf-8", newline="\n")
        relative = path.relative_to(ROOT).as_posix()
        report += [f"## {relative}", "", "| Declaration / variable | Line |", "| --- | --- |"]
        report += [f"| `{name}` | {line} |" for name, line in symbols]
        report.append("")
    document = ROOT / "docs/code-map-python.md"
    text = "\n".join(report)
    if not document.exists() or document.read_text(encoding="utf-8") != text:
        stale.append("docs/code-map-python.md")
        if not args.check:
            document.parent.mkdir(exist_ok=True)
            document.write_text(text, encoding="utf-8", newline="\n")
    if args.check and stale:
        raise SystemExit("Stale line maps: " + ", ".join(stale))
    print(f"Python line maps {'checked' if args.check else 'refreshed'}.")


if __name__ == "__main__":
    main()
