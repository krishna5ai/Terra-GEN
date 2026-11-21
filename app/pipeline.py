"""One call that runs: requirement YAML -> evaluate -> Terraform + report + architecture."""
from pathlib import Path

from app.architecture import build_architecture
from app.evaluator import build_report, evaluate, load_requirement
from app.generator import DB_PORTS, generate

BASE_DIR = Path(__file__).resolve().parent.parent


def run(yaml_path: str) -> dict:
    out = BASE_DIR / "output"

    requirement = load_requirement(yaml_path)
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
    architecture = build_architecture(requirement["project_name"],
                                      generated["components"], arch_ctx)
    (out / "ARCHITECTURE.md").write_text(architecture)

    return {
        "report": report,
        "files": generated["files"] + ["REPORT.md", "ARCHITECTURE.md"],
    }
