import subprocess
from pathlib import Path


def main():
    for binding in Path("bindings").iterdir():
        if not binding.is_dir():
            continue
        subprocess.run(["moon", "publish"], cwd=binding, check=True)


if __name__ == "__main__":
    main()
