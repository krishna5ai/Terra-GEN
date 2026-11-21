"""One call that runs: requirement YAML -> evaluate -> Terraform + report + architecture + PDF + copy page."""
import shutil
import subprocess
from pathlib import Path

from app.architecture import REGION_NAMES, build_architecture, notes
from app.copy_page import write_copy_page
from app.evaluator import build_report, evaluate, load_requirement
from app.generator import DB_PORTS, REGION_CODES, generate
from app.pdf_builder import build_pdf, diagram_svg
from app.registry import COMPONENTS

BASE_DIR = Path(__file__).resolve().parent.parent


def _format(folder: Path):
    """Tidy the HCL so the PDF and copy page show the same code the user receives."""
    if shutil.which("terraform"):
        subprocess.run(["terraform", "fmt", "-no-color"], cwd=folder, capture_output=True)


def run(yaml_path: str) -> dict:
    out = BASE_DIR / "output"

    requirement = load_requirement(yaml_path)
    result = evaluate(requirement)
    gen = result["generate_req"]
    generated = generate(gen)
    components = generated["components"]

    for folder in ("merged", "split"):
        _format(out / folder)

    report = build_report(requirement, components, result["decisions"], result["not_covered"])
    (out / "REPORT.md").write_text(report)

    arch_ctx = {
        "region": gen["region"],
        "instance_type": gen["instance_type"],
        "db_engine": gen["db_engine"],
        "db_instance_class": gen["db_instance_class"],
        "db_multi_az": gen["db_multi_az"],
        "db_port": DB_PORTS[gen["db_engine"]],
    }
    project = requirement["project_name"]
    (out / "ARCHITECTURE.md").write_text(build_architecture(project, components, arch_ctx))

    # The values the user must fill in terraform.tfvars
    fill_in = [
        ("aws_access_key", "Your AWS access key ID"),
        ("aws_secret_key", "Your AWS secret access key"),
    ]
    for name in components:
        fill_in += [(v["name"], v["description"]) for v in COMPONENTS[name]["extra_vars"]]

    main_tf = (out / "merged" / "main.tf").read_text()
    tfvars = (out / "merged" / "terraform.tfvars").read_text()

    # PDF
    for old in out.glob("*.pdf"):
        old.unlink()
    pdf_name = f"{project}-infrastructure.pdf"
    build_pdf(out / pdf_name, {
        "project": project,
        "region_label": f"{REGION_CODES[gen['region']]} ({REGION_NAMES[gen['region']]})",
        "budget": requirement.get("budget", "medium"),
        "environment": requirement.get("environment", "dev"),
        "high_availability": bool(requirement.get("high_availability")),
        "traffic": requirement.get("expected_traffic", "low"),
        "components": components,
        "ctx": arch_ctx,
        "decisions": result["decisions"],
        "not_covered": result["not_covered"],
        "notes": notes(components, arch_ctx),
        "fill_in": fill_in,
        "main_tf": main_tf,
        "tfvars": tfvars,
    })

    # Copy page (HTML with Copy buttons)
    for old in out.glob("*-copy.html"):
        old.unlink()
    copy_name = f"{project}-copy.html"
    split_files = [
        (f.split("/", 1)[1], (out / f).read_text())
        for f in generated["files"]
        if f.startswith("split/") and f.endswith(".tf")
    ]
    write_copy_page(out / copy_name, project, main_tf, tfvars, split_files)

    return {
        "project": project,
        "components": components,
        "decisions": result["decisions"],
        "not_covered": result["not_covered"],
        "diagram_svg": diagram_svg(
            components, arch_ctx,
            f"{REGION_CODES[gen['region']]} ({REGION_NAMES[gen['region']]})"),
        "pdf": pdf_name,
        "copy_page": copy_name,
        "report": report,
        "files": generated["files"] + ["REPORT.md", "ARCHITECTURE.md", pdf_name, copy_name],
    }
