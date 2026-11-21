"""Runs terraform fmt, init and validate on every generated project folder."""
import os
import shutil
import subprocess
from pathlib import Path

STEPS = [
    ("fmt", ["terraform", "fmt", "-no-color"]),
    ("init", ["terraform", "init", "-backend=false", "-input=false", "-no-color"]),
    ("validate", ["terraform", "validate", "-no-color"]),
]


def validate_projects(out_dir: Path, folders=("merged", "split")) -> dict:
    """Return {folder: [(step, passed, message), ...]}. Stops a folder at its first failure."""
    if shutil.which("terraform") is None:
        raise RuntimeError("Terraform is not installed (see Step 6.1)")

    # One shared provider download, reused by every folder and every later run
    cache = Path.home() / ".terraform.d" / "plugin-cache"
    cache.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "TF_PLUGIN_CACHE_DIR": str(cache), "TF_IN_AUTOMATION": "1"}

    results = {}
    for folder in folders:
        path = out_dir / folder
        steps = []
        for label, cmd in STEPS:
            proc = subprocess.run(cmd, cwd=path, env=env, capture_output=True, text=True)
            steps.append((label, proc.returncode == 0, (proc.stdout + proc.stderr).strip()))
            if proc.returncode != 0:
                break
        results[folder] = steps

        # Do not ship local tool files to the user
        shutil.rmtree(path / ".terraform", ignore_errors=True)
        (path / ".terraform.lock.hcl").unlink(missing_ok=True)
    return results
