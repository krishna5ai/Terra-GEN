"""Standalone architecture page: diagram, traffic flow, decisions and what is not covered."""
import html
from pathlib import Path
from string import Template

PAGE = Template("""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>$title</title>
<style>
:root{--bg:#F6F7F9;--card:#fff;--ink:#14181F;--muted:#4A5260;--line:#E3E6EB;--accent:#0E6B5C}
@media (prefers-color-scheme: dark){:root{--bg:#12161B;--card:#1A2027;--ink:#E8ECF1;--muted:#A5AEBB;--line:#2B333D;--accent:#3FB6A0}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:980px;margin:0 auto;padding:32px 20px 64px}
h1{margin:0 0 4px;font-size:28px;letter-spacing:-0.01em}
h2{margin:0 0 12px;font-size:18px}
h3{margin:16px 0 8px;font-size:15px}
p.sub{margin:0 0 24px;color:var(--muted)}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px;margin-bottom:20px}
.diagram{background:#fff;border-radius:10px;padding:12px;border:1px solid var(--line)}
.diagram svg{display:block;width:100%;height:auto}
ul.list{margin:0;padding-left:22px}
ul.list li{margin:4px 0}
.cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px;align-items:start;margin-bottom:20px}
.cols .card{margin-bottom:0}
</style>
</head>
<body>
<main>
<h1>$project: architecture</h1>
<p class="sub">$region. Built: $built</p>
<section class="card">
<h2>Diagram</h2>
<div class="diagram">$svg</div>
<h3>How traffic flows</h3>
<ul class="list">$flow</ul>
</section>
<div class="cols">
<section class="card"><h2>Decisions made</h2><ul class="list">$decisions</ul></section>
<section class="card"><h2>Not covered, write manually</h2><ul class="list">$not_covered</ul></section>
</div>
</main>
</body>
</html>
""")


def _items(values):
    return "".join(f"<li>{html.escape(v)}</li>" for v in (values or ["None"]))


def write_architecture_page(path, project, arch):
    """arch keys: svg, region_label, components, flow, decisions, not_covered."""
    Path(path).write_text(PAGE.substitute(
        title=html.escape(f"{project} - architecture"),
        project=html.escape(project),
        region=html.escape(arch["region_label"]),
        built=html.escape(", ".join(arch["components"])),
        svg=arch["svg"],
        flow=_items(arch["flow"]),
        decisions=_items(arch["decisions"]),
        not_covered=_items(arch["not_covered"]),
    ), encoding="utf-8")
