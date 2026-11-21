import sys
from pathlib import Path

from app.architecture import build_architecture
from app.evaluator import build_report, evaluate, load_requirement
from app.generator import DB_PORTS, generate

path = sys.argv[1] if len(sys.argv) > 1 else "samples/shop-site.yaml"
out = Path(__file__).parent / "output"

requirement = load_requirement(path)
result = evaluate(requirement)
gen = result["generate_req"]
generated = generate(gen)

report = build_report(requirement, generated["components"],
                      result["decisions"], result["not_covered"])
(out / "REPORT.md").write_text(report)

arch_ctx = {
    "region": gen["region"],
    "instance_type": gen["instance_type"],
    "db_engine": gen["db_engine"],
    "db_instance_class": gen["db_instance_class"],
    "db_multi_az": gen["db_multi_az"],
    "db_port": DB_PORTS[gen["db_engine"]],
}
architecture = build_architecture(requirement["project_name"], generated["components"], arch_ctx)
(out / "ARCHITECTURE.md").write_text(architecture)

print(report)
print("Files:", ", ".join(generated["files"] + ["REPORT.md", "ARCHITECTURE.md"]))
