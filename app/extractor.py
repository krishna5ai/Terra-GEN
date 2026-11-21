"""Reads a client's requirement as plain text and fills the requirement YAML structure.

No AI: keyword lists, a few regular expressions and simple negation handling.
Anything it cannot place is kept as a note, never dropped.
"""
import re

# Words a client may use -> checklist key in the requirement YAML. Grow this over time.
KEYWORDS = {
    "web_server": ["web server", "server", "vm", "virtual machine", "ec2",
                   "website", "web app", "web application", "app server"],
    "database": ["database", "mysql", "postgres", "postgresql", "sql", "rds", "db"],
    "storage": ["storage", "bucket", "s3", "files", "file upload", "uploads",
                "images", "backup", "backups"],
    "load_balancer": ["load balancer", "load balancing", "distribute traffic", "alb"],
    "cdn": ["cdn", "cloudfront", "content delivery", "worldwide", "global users"],
    "serverless_api": ["serverless", "lambda", "api gateway", "rest api"],
    "monitoring": ["monitor", "monitoring", "alert", "alerts", "alarm", "alarms",
                   "logging", "cloudwatch"],
}

LABELS = {
    "web_server": "web server", "database": "database", "storage": "storage",
    "load_balancer": "load balancer", "cdn": "CDN",
    "serverless_api": "serverless API", "monitoring": "monitoring",
}

REGIONS = {
    "mumbai": "mumbai", "india": "mumbai",
    "singapore": "singapore",
    "virginia": "virginia", "usa": "virginia", "united states": "virginia",
    "america": "virginia",
    "ireland": "ireland", "europe": "ireland",
}

LOW_BUDGET = [
    r"\bbudget\b\W+(?:is\W+|are\W+)?(?:very\W+|quite\W+)?(?:low|small|tight|limited)",
    r"\b(?:cheap|low[- ]cost|low budget|small budget|minimum cost|cost[- ]effective|startup)\b",
]
HIGH_BUDGET = [r"\b(?:enterprise|unlimited budget|no budget limit|premium)\b"]

HIGH_AVAIL = ["high availability", "no downtime", "always online", "24/7",
              "must not go down", "should not go down", "fault tolerant", "multi-az"]
SENSITIVE = ["sensitive", "confidential", "payment", "payments", "medical",
             "personal data", "compliance", "encrypt", "encrypted", "encryption",
             "hipaa", "pci"]

NEG = re.compile(r"\b(no|not|without|never|don't|dont|doesn't|doesnt|neither|nor)\b")


def has(words, text):
    return any(re.search(rf"\b{re.escape(w)}\b", text) for w in words)


def traffic_from(clause):
    """Return (level, source text) or None."""
    m = re.search(
        r"(\d+(?:\.\d+)?)\s*([km])?\s*\+?\s*(?:concurrent\s+|daily\s+|monthly\s+)?"
        r"(?:users|visitors|customers|people)", clause)
    if m:
        n = float(m.group(1)) * {"k": 1000, "m": 1000000}.get(m.group(2), 1)
        level = "high" if n > 10000 else "medium" if n > 1000 else "low"
        return level, m.group(0).strip()
    if has(["high traffic", "heavy traffic", "millions of users"], clause):
        return "high", "high traffic"
    if has(["low traffic", "few users", "small number of users"], clause):
        return "low", "low traffic"
    return None


def extract(text, project_name=None):
    """Return {"requirement", "understood", "warnings", "not_understood"}."""
    text = re.sub(r"(?<=\d),(?=\d{3})", "", text)          # 5,000 -> 5000
    sentences = [s.strip() for s in re.split(r"[.;\n]+", text) if s.strip()]

    on, off = set(), set()
    region = budget = traffic = engine = None
    traffic_src = ""
    ha = sensitive = False
    not_understood = []

    for sentence in sentences:
        matched = False
        # Clauses, so "a database, but no CDN" is read as two separate ideas
        for clause in re.split(r",| but | however | except | although ", sentence.lower()):
            clause = clause.strip()
            if not clause:
                continue

            # "no downtime" contains "no" but is a requirement, not a rejection
            negated = bool(NEG.search(clause)) and not has(HIGH_AVAIL, clause)

            for key, words in KEYWORDS.items():
                if has(words, clause):
                    (off if negated else on).add(key)
                    matched = True

            for word, code in REGIONS.items():
                if has([word], clause):
                    region = code
                    matched = True

            if any(re.search(p, clause) for p in LOW_BUDGET):
                budget = "low"
                matched = True
            elif any(re.search(p, clause) for p in HIGH_BUDGET):
                budget = "high"
                matched = True

            if has(HIGH_AVAIL, clause):
                ha = True
                matched = True
            if has(SENSITIVE, clause):
                sensitive = True
                matched = True

            if has(["postgres", "postgresql"], clause):
                engine = "postgres"
            elif has(["mysql"], clause):
                engine = "mysql"

            found = traffic_from(clause)
            if found:
                traffic, traffic_src = found
                matched = True

        if not matched:
            not_understood.append(sentence)

    warnings = []
    for key in sorted(on & off):
        warnings.append(f"The text both asks for and rejects {LABELS[key]}. "
                        "It is ticked: please check.")
    off -= on

    components = {"network": True}
    components.update({key: key in on for key in KEYWORDS})
    if not on:
        warnings.append("No components were recognised, so only the VPC will be built. "
                        "Tick components in the YAML file.")

    slug = re.sub(r"[^a-z0-9]+", "-", (project_name or "").lower()).strip("-") or "client-project"
    requirement = {
        "project_name": slug,
        "region": region or "mumbai",
        "environment": "dev",
        "budget": budget or "medium",
        "high_availability": ha,
        "expected_traffic": traffic or "low",
        "sensitive_data": sensitive,
        "components": components,
        "details": {
            "database_engine": engine or "mysql",
            "notes": "; ".join(not_understood),
        },
    }

    understood = [
        f"Region: {requirement['region']}" + ("" if region else " (not mentioned, default)"),
        f"Budget: {requirement['budget']}" + ("" if budget else " (not mentioned, default)"),
        f"High availability: {'yes' if ha else 'no'}",
        f"Expected traffic: {requirement['expected_traffic']}"
        + (f" (from '{traffic_src}')" if traffic else " (not mentioned, default)"),
        f"Sensitive data: {'yes' if sensitive else 'no'}",
        "Components: network (always), "
        + (", ".join(LABELS[k] for k in KEYWORDS if k in on) or "none found"),
    ]
    if "database" in on:
        understood.append(f"Database engine: {requirement['details']['database_engine']}")
    if off:
        understood.append("Client said NOT needed: " + ", ".join(LABELS[k] for k in KEYWORDS if k in off))

    return {
        "requirement": requirement,
        "understood": understood,
        "warnings": warnings,
        "not_understood": not_understood,
    }
