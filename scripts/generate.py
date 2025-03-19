import json
from pathlib import Path
import subprocess
import shutil
import semver
import os
import re


MOON_HOME = Path(os.getenv("MOON_HOME"))
VERSION = "0.1.7"


include_directories = [
    (Path(".") / "bindings" / "tinycc" / "include").absolute(),
]


def perform_c_include_to(path: Path):
    print(f"Processing {path}")
    system_include_pattern = re.compile(r"#\s*include\s+<([^>]+)>")
    already_included: set[Path] = set()

    def read_file(file: Path) -> list[str]:
        return file.read_text().splitlines()

    def try_include(include_path: str) -> list[str]:
        for include_dir in include_directories:
            include_file = include_dir / include_path
            if include_file.exists():
                if include_file in already_included:
                    return []
                print(f"Including {include_path}")
                already_included.add(include_file)
                return include_file.read_text().splitlines()
        raise FileNotFoundError(f"Could not find include file {include_path}")

    def process_file(lines: list[str]):
        expanded_lines: list[str] = []
        for line in lines:
            match = system_include_pattern.match(line)
            if match:
                try:
                    included_lines = try_include(match.group(1))
                    expanded_lines.extend(
                        ["#ifdef __TINYC__"]
                        + process_file(included_lines)
                        + ["#else", line, "#endif"]
                    )
                except FileNotFoundError:
                    expanded_lines.append(line)
            else:
                expanded_lines.append(line)
        return expanded_lines

    original_lines = read_file(path)
    expanded_lines = process_file(original_lines)
    path.write_text("\n".join(expanded_lines))


class Grammar:
    name: str
    path: Path
    old_version: semver.VersionInfo
    old_repository: str
    repository: str
    stubs: list[str]
    files: list[str]

    def __init__(self, name: str, path: Path, repository: str, commit: str):
        self.name = name
        self.path = path
        self.repository = f"{repository}#{commit}"
        self.stubs = []
        self.files = []
        src_path = path / "src"
        for file in src_path.iterdir():
            if file.suffix == ".c":
                self.stubs.append(str(file.relative_to(src_path)))
            self.files.append(str(file.relative_to(src_path)))

    def generate_gitignore_to(self, destination: Path):
        content = "\n".join(self.files) + "\n"
        destination.write_text(content)

    def generate_moon_mod_json_to(self, destination: Path, version: str):
        moon_mod_json = {
            "name": f"tonyfettes/tree_sitter_{self.name}",
            "version": version,
            "deps": {
                "tonyfettes/tree_sitter_language": "0.1.1",
            },
            "repository": self.repository,
            "license": "Apache-2.0",
            "include": self.files + ["binding.mbt", "moon.pkg.json"],
        }
        destination.write_text(json.dumps(moon_mod_json, indent=2) + "\n")

    def generate_moon_pkg_json_to(self, destination: Path):
        moon_pkg_json = {
            "import": ["tonyfettes/tree_sitter_language"],
            "native_stub": self.stubs,
            "support-targets": ["native"],
        }
        destination.write_text(json.dumps(moon_pkg_json, indent=2) + "\n")

    def generate_binding_mbt_to(self, destination: Path):
        content = f"""///|
pub extern "c" fn language() -> @tree_sitter_language.Language = "tree_sitter_{self.name}"
"""
        destination.write_text(content)

    def generate_binding_to(self, destination: Path):
        version = VERSION
        if destination.exists():
            if (destination / "moon.mod.json").exists():
                moon_mod_json = json.loads((destination / "moon.mod.json").read_text())
                if "version" in moon_mod_json:
                    version = moon_mod_json["version"]
                    if "repository" in moon_mod_json:
                        repository = moon_mod_json["repository"]
                        if repository != self.repository:
                            version = semver.bump_patch(version)
                    else:
                        version = semver.bump_patch(version)
                    if semver.compare(version, VERSION) < 0:
                        version = VERSION
            shutil.rmtree(destination)
        print(f"Generating binding for {self.name} at {destination}, version {version}")
        shutil.copytree(self.path / "src", destination)
        for file in destination.rglob("*.h"):
            perform_c_include_to(file)
        self.generate_gitignore_to(destination / ".gitignore")
        self.generate_moon_mod_json_to(destination / "moon.mod.json", version)
        self.generate_moon_pkg_json_to(destination / "moon.pkg.json")
        self.generate_binding_mbt_to(destination / "binding.mbt")


def git_submodule_url(path: Path) -> str:
    try:
        url = subprocess.run(
            ["git", "config", f"submodule.{path}.url"],
            capture_output=True,
            check=True,
            text=True,
        )
        url = url.stdout.strip()
    except subprocess.CalledProcessError:
        raise ValueError(f"Could not find submodule URL for {path}")
    return url


def git_submodule_commit(path: Path) -> str:
    try:
        commit = subprocess.run(
            ["git", "submodule", "status", path],
            capture_output=True,
            check=True,
            text=True,
        )
        commit = commit.stdout.strip().split(" ")[0]
    except Exception as e:
        raise ValueError(f"Could not get commit hash for {path}: {e}")

    return commit


def generate_binding(path: Path, bindings: Path):
    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist")

    url = git_submodule_url(path)
    commit = git_submodule_commit(path)

    tree_sitter_json_path = path / "tree-sitter.json"
    if not tree_sitter_json_path.exists():
        raise FileNotFoundError(f"{tree_sitter_json_path} does not exist")
    tree_sitter_json = json.loads(tree_sitter_json_path.read_text())
    grammars = tree_sitter_json["grammars"]
    for grammar in grammars:
        grammar_name = grammar["name"]
        grammar_path = "."
        if "path" in grammar:
            grammar_path = grammar["path"]
        print(f"Generating binding for {grammar_name} at {grammar_path}")
        grammar_path: Path = path / grammar_path
        grammar = Grammar(grammar_name, grammar_path, url, commit)
        binding_root: Path = (bindings / f"tree_sitter_{grammar_name}").resolve()

        grammar.generate_binding_to(binding_root)

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
