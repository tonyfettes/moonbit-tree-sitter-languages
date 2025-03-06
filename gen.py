import json
from pathlib import Path
import subprocess
import shutil


def generate_binding(path: Path, bindings: Path):
    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist")

    tree_sitter_json_path = path / "tree-sitter.json"
    if not tree_sitter_json_path.exists():
        raise FileNotFoundError(f"{tree_sitter_json_path} does not exist")
    tree_sitter_json = json.loads(tree_sitter_json_path.read_text())
    grammars = tree_sitter_json["grammars"]
    for grammar in grammars:
        grammar_name = grammar["name"]
        grammar_path = grammar["path"]
        print(f"Generating binding for {grammar_name} at {grammar_path}")
        grammar_path: Path = path / grammar_path
        parser_files: list[str] = []
        for parser_file in (grammar_path / "src").glob("*.c"):
            parser_files.append(str(parser_file.relative_to(grammar_path)))

        binding_root: Path = (bindings / f"tree_sitter_{grammar_name}").resolve()
        print(f"Binding root: {binding_root}")
        shutil.rmtree(binding_root, ignore_errors=True)
        binding_root.mkdir(exist_ok=False)

        shutil.copytree(grammar_path / "src", binding_root / "src")

        moon_mod_json = {
            "name": f"tonyfettes/tree_sitter_{grammar_name}",
            "version": "0.1.3",
            "deps": {
                "tonyfettes/tree_sitter_language": "0.1.1",
            },
            "license": "Apache-2.0",
            "include": ["src", "binding.mbt", "moon.pkg.json"],
        }
        (binding_root / "moon.mod.json").write_text(
            json.dumps(moon_mod_json, indent=2) + "\n"
        )

        moon_pkg_json = {
            "import": ["tonyfettes/tree_sitter_language"],
            "native_stub": parser_files,
            "support-targets": ["native"],
        }
        (binding_root / "moon.pkg.json").write_text(
            json.dumps(moon_pkg_json, indent=2) + "\n"
        )

        binding_mbt = f"""///|
pub extern "c" fn language() -> @tree_sitter_language.Language = "tree_sitter_{grammar_name}"
"""
        (binding_root / "binding.mbt").write_text(binding_mbt)

        print(f"Building {grammar_name}")

        subprocess.run(
            ["moon", "build", "--target", "native"], cwd=binding_root, check=True
        )


def main():
    for path in Path("grammars").iterdir():
        if not path.is_dir():
            continue

        generate_binding(path, Path("bindings"))


if __name__ == "__main__":
    main()
