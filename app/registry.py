"""Knowledge base: every supported component and what it needs."""

COMPONENTS = {
    "vpc": {
        "label": "VPC (2 public + 2 private subnets)",
        "requires": [],
        "extra_vars": [],
    },
    "ec2": {
        "label": "EC2 web server",
        "requires": ["vpc"],
        "extra_vars": [
            {"name": "ami_id",
             "description": "AMI ID valid in the chosen region",
             "sensitive": False,
             "placeholder": "FILL_AMI_ID"},
            {"name": "allowed_ssh_cidr",
             "description": "Your public IP for SSH, for example 203.0.113.10/32",
             "sensitive": False,
             "placeholder": "FILL_YOUR_IP/32"},
        ],
    },
    "rds": {
        "label": "RDS database (private subnets)",
        "requires": ["vpc"],
        "extra_vars": [
            {"name": "db_password",
             "description": "Master password for the database",
             "sensitive": True,
             "placeholder": "FILL_DB_PASSWORD"},
        ],
    },
    "s3": {
        "label": "S3 bucket (private, encrypted, versioned)",
        "requires": [],
        "extra_vars": [],
    },
}


def resolve(selected):
    """Add required components automatically and return them in build order."""
    unknown = [name for name in selected if name not in COMPONENTS]
    if unknown:
        raise ValueError(f"Not supported yet: {unknown}. Supported: {sorted(COMPONENTS)}")

    result = []

    def add(name):
        for needed in COMPONENTS[name]["requires"]:
            add(needed)
        if name not in result:
            result.append(name)

    for name in selected:
        add(name)
    return result
