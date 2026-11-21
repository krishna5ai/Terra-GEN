"""Usage: python validate.py   (run python main.py first)"""
import sys
from pathlib import Path

from app.validator import validate_projects

out_dir = Path(__file__).resolve().parent / "output"
if not (out_dir / "merged").exists():
    sys.exit("Nothing to check. Run: python main.py")

print("Checking the generated Terraform. The first run downloads the AWS provider, so it can take a few minutes.\n")
results = validate_projects(out_dir)

all_ok = True
for folder, steps in results.items():
    line = []
    for label, passed, message in steps:
        line.append(f"{label} {'OK' if passed else 'FAILED'}")
        if not passed:
            all_ok = False
            print(f"--- {folder}: {label} failed ---\n{message}\n")
    print(f"{folder:7}: " + ", ".join(line))

print("\nAll checks passed." if all_ok else "\nSome checks failed. See the messages above.")
sys.exit(0 if all_ok else 1)
