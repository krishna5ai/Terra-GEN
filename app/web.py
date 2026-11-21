"""Terra-GEN web interface (Flask): paste a requirement, review it, get the Terraform."""
import re
import threading
from pathlib import Path

import yaml
from flask import Flask, render_template, request, send_from_directory

from app.extractor import extract
from app.pipeline import run

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
SAMPLES_DIR = BASE_DIR / "samples"
MAX_TEXT = 20000

EXAMPLE = (
    "Our client runs an online shop with about 5,000 users.\n"
    "The shop needs a web server and a MySQL database, but no CDN.\n"
    "The budget is low and the site must not go down during sales.\n"
    "Product images should be stored safely.\n"
    "They also want a VPN to their office."
)

_LOCK = threading.Lock()   # the output folder is shared, so build one project at a time


def slugify(value) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value or "").lower()).strip("-")[:40] or "client-project"


def create_app():
    web = Flask(__name__, template_folder=str(BASE_DIR / "web" / "templates"))
    web.config["MAX_CONTENT_LENGTH"] = 200 * 1024

    @web.get("/")
    def index():
        return render_template("index.html", step=1, name="", text="", example=EXAMPLE)

    @web.post("/understand")
    def understand():
        text = request.form.get("requirement", "").strip()
        name = slugify(request.form.get("project_name", ""))
        if not text:
            return render_template("index.html", step=1, name=name, text=text, example=EXAMPLE,
                                   error="Paste the client requirement first."), 400
        if len(text) > MAX_TEXT:
            return render_template("index.html", step=1, name=name, text=text[:MAX_TEXT],
                                   example=EXAMPLE,
                                   error="That text is too long. Keep it under 20,000 characters."), 400

        result = extract(text, name)
        return render_template(
            "understand.html", step=2,
            understood=result["understood"], warnings=result["warnings"],
            not_understood=result["not_understood"],
            yaml_text=yaml.safe_dump(result["requirement"], sort_keys=False),
        )

    @web.post("/generate")
    def generate_route():
        yaml_text = request.form.get("yaml_text", "")
        try:
            data = yaml.safe_load(yaml_text)
            if not isinstance(data, dict):
                raise ValueError("The requirement is not valid YAML. It should be a list of 'key: value' lines.")
            SAMPLES_DIR.mkdir(exist_ok=True)
            path = SAMPLES_DIR / f"{slugify(data.get('project_name'))}.yaml"
            path.write_text(yaml_text)
            with _LOCK:
                result = run(str(path))
        except (yaml.YAMLError, ValueError, KeyError, TypeError) as exc:
            return render_template("understand.html", step=2, understood=[], warnings=[],
                                   not_understood=[], yaml_text=yaml_text,
                                   error=str(exc)), 400
        return render_template("result.html", step=3, r=result)

    @web.get("/files/<path:filename>")
    def files(filename):
        return send_from_directory(OUTPUT_DIR, filename)

    return web
