import shutil
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from app.registry import COMPONENTS, resolve

BASE_DIR = Path(__file__).resolve().parent.parent

env = Environment(
    loader=FileSystemLoader(BASE_DIR / "templates"),
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=True,
)

REGION_CODES = {
    "mumbai": "ap-south-1",
    "singapore": "ap-southeast-1",
    "virginia": "us-east-1",
    "ireland": "eu-west-1",
}

DB_PORTS = {"mysql": 3306, "postgres": 5432}

GITIGNORE = "terraform.tfvars\n*.tfstate*\n.terraform/\n"


def _banner(title: str) -> str:
    line = "# " + "=" * 60
    return f"{line}\n# {title}\n{line}\n"


def generate(req: dict, out_dir: str = "output") -> dict:
    """Create merged/ (one main.tf) and split/ (one file per part).

    Returns {"components": [...], "files": [...]} with paths relative to out_dir.
    """
    out = BASE_DIR / out_dir
    out.mkdir(exist_ok=True)

    # Remove everything from a previous run so old components do not linger
    for old in list(out.glob("*.tf")) + list(out.glob("*.tfvars")):
        old.unlink()
    (out / ".gitignore").unlink(missing_ok=True)
    for sub in ("merged", "split"):
        shutil.rmtree(out / sub, ignore_errors=True)

    components = resolve(req.get("components", []))

    extra_vars = []
    for name in components:
        extra_vars += COMPONENTS[name]["extra_vars"]

    db_engine = req.get("db_engine", "mysql")
    ctx = {
        "project_name": req["project_name"],
        "region": REGION_CODES[req["region"]],
        "components": components,
        "extra_vars": extra_vars,
        "instance_type": req.get("instance_type", "t3.micro"),
        "db_engine": db_engine,
        "db_port": DB_PORTS[db_engine],
        "db_instance_class": req.get("db_instance_class", "db.t3.micro"),
        "db_multi_az": req.get("db_multi_az", False),
    }

    # (section title, template file) in the order they appear
    parts = [("Provider and settings", "providers.tf"), ("Variables", "variables.tf")]
    parts += [(COMPONENTS[name]["label"], f"{name}.tf") for name in components]
    parts += [("Outputs", "outputs.tf")]

    rendered = [
        (title, filename, env.get_template(f"{filename}.j2").render(**ctx))
        for title, filename in parts
    ]
    tfvars = env.get_template("terraform.tfvars.j2").render(**ctx)

    files = []

    # Option A: one merged file
    merged = out / "merged"
    merged.mkdir()
    body = "\n".join(
        _banner(title) + "\n" + text.strip() + "\n" for title, _, text in rendered
    )
    (merged / "main.tf").write_text(body)
    (merged / "terraform.tfvars").write_text(tfvars)
    (merged / ".gitignore").write_text(GITIGNORE)
    files += ["merged/main.tf", "merged/terraform.tfvars", "merged/.gitignore"]

    # Option B: one file per part (vpc.tf, s3.tf, ...)
    split = out / "split"
    split.mkdir()
    for _, filename, text in rendered:
        (split / filename).write_text(text)
        files.append(f"split/{filename}")
    (split / "terraform.tfvars").write_text(tfvars)
    (split / ".gitignore").write_text(GITIGNORE)
    files += ["split/terraform.tfvars", "split/.gitignore"]

    return {"components": components, "files": files}
