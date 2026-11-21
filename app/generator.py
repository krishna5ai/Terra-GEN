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


def generate(req: dict, out_dir: str = "output") -> dict:
    """Create the Terraform files for one requirement.

    Returns {"components": [...], "files": [...]}.
    """
    out = BASE_DIR / out_dir
    out.mkdir(exist_ok=True)

    # Remove files from a previous run so old components do not linger
    for old in list(out.glob("*.tf")) + list(out.glob("*.tfvars")):
        old.unlink()

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

    files = ["providers.tf", "variables.tf", "terraform.tfvars"]
    files += [f"{name}.tf" for name in components]
    files += ["outputs.tf"]

    for filename in files:
        text = env.get_template(f"{filename}.j2").render(**ctx)
        (out / filename).write_text(text)

    (out / ".gitignore").write_text("terraform.tfvars\n*.tfstate*\n.terraform/\n")
    return {"components": components, "files": files + [".gitignore"]}
