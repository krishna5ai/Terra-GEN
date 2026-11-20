from pathlib import Path
from jinja2 import Environment, FileSystemLoader

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

BASE_FILES = ["providers.tf", "variables.tf", "terraform.tfvars"]


def generate(req: dict, out_dir: str = "output") -> list:
    """Create the Terraform files for one requirement. Returns the file names."""
    out = BASE_DIR / out_dir
    out.mkdir(exist_ok=True)

    ctx = {
        "project_name": req["project_name"],
        "region": REGION_CODES[req["region"]],
        "extra_vars": [],   # components add to this in Step 2
    }

    for name in BASE_FILES:
        text = env.get_template(f"{name}.j2").render(**ctx)
        (out / name).write_text(text)

    (out / ".gitignore").write_text("terraform.tfvars\n*.tfstate*\n.terraform/\n")
    return BASE_FILES + [".gitignore"]
