import json
from pathlib import Path
import subprocess

def generate_binding(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist")

    tree_sitter_json_path = path / "tree-sitter" / "tree-sitter.json"
    tree_sitter_json = json.loads(tree_sitter_json_path.read_text())
    grammars = tree_sitter_json["grammars"]
    for grammar in grammars:
        grammar_name = grammar["name"]
        grammar_path = grammar["path"]
        print(f"Generating binding for {grammar_name} at {grammar_path}")
        grammar_path: Path = path /  "tree-sitter" / grammar_path
        parser_files: list[str] = []
        print(grammar_path.absolute())
        for parser_file in (grammar_path / "src").glob("*.c"):
            parser_files.append(str(parser_file.relative_to(path)))

        moon_mod_json = {
            "name": f"tonyfettes/tree_sitter_{grammar_name}",
            "version": "0.1.0",
            "deps": {
                "tonyfettes/tree_sitter_language": "0.1.0",
            },
        }
        (path / "moon.mod.json").write_text(json.dumps(moon_mod_json, indent=2))

        moon_pkg_json = {
            "import": ["tonyfettes/tree_sitter_language"],
            "native_stub": parser_files,
            "support-targets": ["native"],
        }
        (path / "moon.pkg.json").write_text(json.dumps(moon_pkg_json, indent=2))

        binding_mbt = f"""///|
pub extern "c" fn language() -> @tree_sitter_language.Language = "tree_sitter_{grammar_name}"
"""
        (path / "binding.mbt").write_text(binding_mbt)

        subprocess.run(["moon", "build", "--target", "native"], cwd=path)


def main():
    for path in Path(".").iterdir():
        if not path.is_dir():
            continue

        if (path / "tree-sitter").exists():
            generate_binding(path)


if __name__ == "__main__":
    main()
