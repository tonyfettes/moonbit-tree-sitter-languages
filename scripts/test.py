import subprocess
from pathlib import Path
import json
import shutil


class Grammar:
    name: str
    path: Path

    def __init__(self, name: str, path: Path):
        self.name = name
        self.path = path


def generate_test_module(grammars: list[Grammar], destination: Path):
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    moon_mod_deps = {}
    for grammar in grammars:
        moon_mod_deps[f"tonyfettes/tree_sitter_{grammar.name}"] = {"path": str(grammar.path.relative_to(destination, walk_up=True))}
    moon_mod_json = {
        "name": "tonyfettes/tree_sitter_language/test",
        "version": "0.1.0",
        "deps": moon_mod_deps,
    }
    (destination / "moon.mod.json").write_text(
        json.dumps(moon_mod_json, indent=2) + "\n"
    )
    imports = ["tonyfettes/tree_sitter"]
    for grammar in grammars:
        imports.append(f"tonyfettes/tree_sitter_{grammar.name}")
    moon_pkg_json = {
        "import": imports,
        "link": {
            "native": {
                "cc-flags": ""
            }
        }
    }
    (destination / "moon.pkg.json").write_text(
        json.dumps(moon_pkg_json, indent=2) + "\n"
    )
    subprocess.run(["moon", "add", "tonyfettes/tree_sitter"], cwd=destination, check=True)
    (destination / "moon.mod.json").write_text(
        (destination / "moon.mod.json").read_text() + "\n"
    )
    tests = []
    for grammar in grammars:
        tests.append(
            f"""///|
test "can_load_grammar" {{
    let parser = @tree_sitter.Parser::new()
    let language = @tree_sitter_{grammar.name}.language()
    parser.set_language(language)
}}
"""
        )
    (destination / "test.mbt").write_text("\n".join(tests))
    subprocess.run(["moon", "fmt"], cwd=destination, check=True)
    subprocess.run(["moon", "test", "--target", "native"], cwd=destination, check=True)


def main():
    grammars = []
    bindings = Path("bindings")
    for item in bindings.iterdir():
        if not item.is_dir():
            continue
        if not item.name.startswith("tree_sitter_"):
            continue
        grammars.append(
            Grammar(
                name=item.name.removeprefix("tree_sitter_"),
                path=item,
            )
        )
    grammars.sort(key=lambda grammar: grammar.name)
    generate_test_module(grammars, bindings / "test")


if __name__ == "__main__":
    main()
