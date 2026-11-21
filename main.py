import sys
from pathlib import Path

from app.evaluator import build_report, evaluate, load_requirement
from app.generator import generate

path = sys.argv[1] if len(sys.argv) > 1 else "samples/shop-site.yaml"

requirement = load_requirement(path)
result = evaluate(requirement)
generated = generate(result["generate_req"])

report = build_report(requirement, generated["components"],
                      result["decisions"], result["not_covered"])
(Path(__file__).parent / "output" / "REPORT.md").write_text(report)

print(report)
print("Files:", ", ".join(generated["files"] + ["REPORT.md"]))
