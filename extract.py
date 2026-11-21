"""Usage: python extract.py samples/client1.txt"""
import re
import sys
from pathlib import Path

import yaml

from app.extractor import extract
from app.pipeline import run

BASE_DIR = Path(__file__).resolve().parent


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: python extract.py samples/client1.txt")

    text_path = Path(sys.argv[1])
    text = text_path.read_text()

    default_name = re.sub(r"[^a-z0-9]+", "-", text_path.stem.lower()).strip("-")
    name = input(f"Project name [{default_name}]: ").strip() or default_name

    result = extract(text, name)
    req = result["requirement"]

    print("\nWhat we understood")
    for line in result["understood"]:
        print(f"  - {line}")

    if result["warnings"]:
        print("\nPlease check")
        for w in result["warnings"]:
            print(f"  ! {w}")

    if result["not_understood"]:
        print("\nNot understood (goes to the 'write manually' list)")
        for s in result["not_understood"]:
            print(f"  ? {s}")

    yaml_path = BASE_DIR / "samples" / f"{req['project_name']}.yaml"
    with open(yaml_path, "w") as f:
        yaml.safe_dump(req, f, sort_keys=False)
    print(f"\nSaved {yaml_path.relative_to(BASE_DIR)}")
    print("If anything above is wrong, edit that file in VS Code, then run:")
    print(f"  python main.py samples/{req['project_name']}.yaml")

    if input("\nGenerate Terraform now? [y/n]: ").strip().lower() == "y":
        output = run(str(yaml_path))
        print()
        print(output["report"])
        print("Files:", ", ".join(output["files"]))


main()
