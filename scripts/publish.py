import subprocess
from pathlib import Path


def main():
    bindings = Path("bindings")
    subprocess.run(["moon", "test", "--target", "native"], cwd=(bindings / "test"), check=True)
    for binding in bindings.iterdir():
        if not binding.is_dir():
            continue
        if not binding.name.startswith("tree_sitter_"):
            continue
        try:
            subprocess.run(["moon", "publish"], cwd=binding, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed to publish {binding}: {e}")


if __name__ == "__main__":
    main()
