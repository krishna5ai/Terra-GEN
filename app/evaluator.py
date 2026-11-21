"""Turns a client requirement (YAML) into design decisions and a coverage report."""
import re

import yaml

from app.generator import REGION_CODES
from app.registry import COMPONENTS, resolve

# Checklist item in the YAML -> component name in the registry
NAME_MAP = {
    "network": "vpc",
    "web_server": "ec2",
    "database": "rds",
    "storage": "s3",
    "load_balancer": "alb",
    "cdn": "cloudfront",
    "serverless_api": "lambda_api",
    "monitoring": "cloudwatch",
}

LABELS = {
    "alb": "Load balancer (ALB)",
    "cloudfront": "CDN (CloudFront)",
    "lambda_api": "Serverless API (Lambda + API Gateway)",
    "cloudwatch": "Monitoring (CloudWatch)",
}

EC2_SIZES = {"low": "t3.micro", "medium": "t3.small", "high": "t3.medium"}
DB_SIZES = {"low": "db.t3.micro", "medium": "db.t3.small", "high": "db.t3.medium"}
DB_ENGINES = ("mysql", "postgres")


def load_requirement(path: str) -> dict:
    with open(path) as f:
        req = yaml.safe_load(f)

    if not re.fullmatch(r"[a-z0-9-]+", str(req.get("project_name", ""))):
        raise ValueError("project_name: use lowercase letters, numbers and hyphens only")
    if req.get("region") not in REGION_CODES:
        raise ValueError(f"region must be one of {sorted(REGION_CODES)}")
    if req.get("budget", "medium") not in EC2_SIZES:
        raise ValueError("budget must be low, medium or high")
    if not any((req.get("components") or {}).values()):
        raise ValueError("Select at least one component")
    engine = (req.get("details") or {}).get("database_engine", "mysql")
    if engine not in DB_ENGINES:
        raise ValueError(f"database_engine must be one of {DB_ENGINES}")
    return req


def evaluate(req: dict) -> dict:
    """Return {"generate_req": {...}, "decisions": [...], "not_covered": [...]}."""
    decisions = []
    not_covered = []
    details = req.get("details") or {}
    budget = req.get("budget", "medium")

    # 1. Which checklist items can we build?
    requested = []
    for key, on in req["components"].items():
        if not on:
            continue
        name = NAME_MAP.get(key)
        if name is None:
            not_covered.append(f"Unknown requirement item: {key}")
        elif name in COMPONENTS:
            requested.append(name)
        else:
            not_covered.append(f"{LABELS.get(name, name)}: no template yet, write manually")

    # 2. Dependencies we add automatically
    resolved = resolve(requested)
    added = [c for c in resolved if c not in requested]
    if added:
        decisions.append(f"Added automatically: {', '.join(added)} (required by the other components)")

    # 3. Sizes from the budget
    gen = {
        "project_name": req["project_name"],
        "region": req["region"],
        "components": requested,
        "instance_type": EC2_SIZES[budget],
        "db_instance_class": DB_SIZES[budget],
        "db_engine": details.get("database_engine", "mysql"),
        "db_multi_az": False,
    }
    decisions.append(
        f"Budget '{budget}': EC2 {gen['instance_type']}, RDS {gen['db_instance_class']}, "
        "no NAT gateway (keeps the monthly cost low)"
    )

    # 4. High availability
    if req.get("high_availability"):
        if "rds" in resolved:
            gen["db_multi_az"] = True
            decisions.append("High availability: RDS Multi-AZ enabled (standby in a second zone, roughly doubles the database cost)")
        if "ec2" in resolved:
            not_covered.append(
                "Load balancer and Auto Scaling for the web tier: no template yet, "
                "the web server is a single instance until you add them"
            )

    # 5. Sensitive data
    if req.get("sensitive_data"):
        decisions.append(
            "Sensitive data: already the default here (private database subnets, encrypted "
            "disks and storage, IMDSv2 only, S3 public access blocked)"
        )
        not_covered.append("Customer-managed KMS keys and WAF: no template yet")

    # 6. Traffic
    if req.get("expected_traffic") == "high":
        not_covered.append("CDN and load balancer are recommended for high traffic: no template yet")

    # 7. Free-text notes from the client are never dropped
    for note in str(details.get("notes", "")).split(";"):
        if note.strip():
            not_covered.append(f"Client note: {note.strip()} (write manually)")

    return {"generate_req": gen, "decisions": decisions, "not_covered": not_covered}


def build_report(req: dict, components: list, decisions: list, not_covered: list) -> str:
    def bullets(items):
        return "\n".join(f"- {i}" for i in items) if items else "- None"

    return (
        f"# {req['project_name']}: design report\n\n"
        f"Region: {req['region']}  |  Budget: {req.get('budget', 'medium')}  |  "
        f"Environment: {req.get('environment', 'dev')}\n\n"
        f"## Generated components\n{bullets(components)}\n\n"
        f"## Decisions made\n{bullets(decisions)}\n\n"
        f"## Not covered, write manually\n{bullets(not_covered)}\n"
    )
