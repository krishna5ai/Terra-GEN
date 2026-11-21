"""Builds ARCHITECTURE.md (Mermaid diagram + notes) from the resolved components."""

from app.generator import REGION_CODES

REGION_NAMES = {
    "mumbai": "Mumbai",
    "singapore": "Singapore",
    "virginia": "N. Virginia",
    "ireland": "Ireland",
}

SECURITY = {
    "vpc": ["Private subnets have no route to the internet"],
    "ec2": [
        "Root disk encrypted",
        "IMDSv2 required (blocks a common credential-theft attack)",
        "SSH allowed only from the IP you set in terraform.tfvars",
        "HTTP (port 80) is open to the internet, as a web server needs",
    ],
    "rds": [
        "Database is not publicly accessible",
        "Storage encrypted",
    ],
    "s3": [
        "All public access blocked",
        "Encryption on (AES256)",
        "Versioning on",
    ],
}

COST = {
    "vpc": ["No NAT gateway: a NAT gateway has a steady hourly charge, so it is left out"],
    "ec2": ["Instance size follows the budget answer; stop or destroy it when not in use"],
    "rds": ["Single instance unless high availability was requested (Multi-AZ roughly doubles the database cost)"],
    "s3": ["Billed by storage used and number of requests"],
}


def notes(components, ctx):
    """Return {"flow": [...], "security": [...], "cost": [...]} for the components."""
    flow = []
    if "ec2" in components:
        flow.append("Users reach the web server through the internet gateway on port 80.")
    if "ec2" in components and "rds" in components:
        flow.append(
            f"The web server talks to the database on port {ctx['db_port']}. "
            "The database sits in private subnets and accepts traffic only from the web server."
        )
    if "rds" in components and "ec2" not in components:
        flow.append("The database sits in private subnets with no public access.")
    if "s3" in components:
        flow.append("The S3 bucket is private and has no public access.")

    def pick(table):
        items = []
        for name in components:
            items += table.get(name, [])
        return items

    return {"flow": flow, "security": pick(SECURITY), "cost": pick(COST)}


def _mermaid(components, ctx):
    region_code = REGION_CODES[ctx["region"]]
    region_name = REGION_NAMES[ctx["region"]]

    lines = [
        "flowchart LR",
        '  user(("Client users"))',
        f'  subgraph aws["AWS Cloud: {region_code} ({region_name})"]',
    ]

    if "vpc" in components:
        lines.append('    subgraph vpc["VPC 10.0.0.0/16"]')
        lines.append('      igw["Internet gateway"]')
        if "ec2" in components:
            lines.append('      subgraph pub["Public subnets (2 zones)"]')
            lines.append(f'        ec2["EC2 web server<br/>{ctx["instance_type"]}"]')
            lines.append("      end")
        if "rds" in components:
            ha = ", Multi-AZ" if ctx["db_multi_az"] else ""
            lines.append('      subgraph priv["Private subnets (2 zones)"]')
            lines.append(
                f'        rds[("RDS {ctx["db_engine"]}<br/>{ctx["db_instance_class"]}{ha}")]'
            )
            lines.append("      end")
        if "ec2" not in components and "rds" not in components:
            lines.append('      subnets["2 public + 2 private subnets"]')
        lines.append("    end")

    if "s3" in components:
        lines.append('    s3[("S3 bucket<br/>private, encrypted, versioned")]')

    lines.append("  end")

    if "ec2" in components:
        lines.append("  user -->|HTTP 80| igw")
        lines.append("  igw --> ec2")
    if "ec2" in components and "rds" in components:
        lines.append(f'  ec2 -->|port {ctx["db_port"]}| rds')

    return "\n".join(lines)


def build_architecture(project_name, components, ctx):
    """ctx needs: region, instance_type, db_engine, db_instance_class, db_multi_az, db_port."""
    n = notes(components, ctx)

    def bullets(items):
        return "\n".join(f"- {i}" for i in items) or "- None"

    return (
        f"# {project_name}: architecture\n\n"
        f"```mermaid\n{_mermaid(components, ctx)}\n```\n\n"
        f"## How traffic flows\n{bullets(n['flow'])}\n\n"
        f"## Security\n{bullets(n['security'])}\n\n"
        f"## Cost notes\n{bullets(n['cost'])}\n\n"
        "Check current prices with the AWS Pricing Calculator before quoting a total to a client.\n"
    )
