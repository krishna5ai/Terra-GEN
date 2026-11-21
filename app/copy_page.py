"""Builds a self-contained HTML page with one-click Copy buttons for the generated code."""
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
:root{--bg:#F6F7F9;--card:#fff;--ink:#14181F;--muted:#4A5260;--line:#E3E6EB;--accent:#0E6B5C;--accent-ink:#fff;--code:#F2F4F7;--mark:#FFF1C2;--markink:#4A3A00}
@media (prefers-color-scheme: dark){:root{--bg:#12161B;--card:#1A2027;--ink:#E8ECF1;--muted:#A5AEBB;--line:#2B333D;--accent:#3FB6A0;--accent-ink:#0B1512;--code:#0F1318;--mark:#4A3F12;--markink:#FFE9A3}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:980px;margin:0 auto;padding:32px 20px 64px}
h1{margin:0 0 4px;font-size:28px;letter-spacing:-0.01em}
h2{margin:0;font-size:18px}
p.sub{margin:0 0 24px;color:var(--muted)}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px;margin-bottom:20px}
.head{display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between;margin-bottom:12px}
.hint{margin:0 0 12px;color:var(--muted);font-size:14px}
button.copy{min-height:44px;padding:0 20px;border:0;border-radius:10px;background:var(--accent);color:var(--accent-ink);font:600 15px system-ui,sans-serif;cursor:pointer}
button.copy.ok{background:#2E7D32;color:#fff}
button.copy:focus-visible,summary:focus-visible{outline:3px solid var(--accent);outline-offset:2px}
pre{margin:0;background:var(--code);border:1px solid var(--line);border-radius:10px;padding:14px 0;overflow:auto;max-height:70vh;font:13px/1.5 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.ln{display:block;min-height:1.5em;padding:0 14px;white-space:pre}
.ln.user{background:var(--mark);color:var(--markink)}
details{border-top:1px solid var(--line);padding:12px 0}
details:first-of-type{border-top:0}
summary{cursor:pointer;font-weight:600;min-height:44px;display:flex;align-items:center}
details .head{margin:8px 0 12px}
ol{margin:0;padding-left:22px}
li{margin:6px 0}
code.i{background:var(--code);border-radius:6px;padding:1px 6px;font:13px ui-monospace,Menlo,Consolas,monospace}
.legend{display:inline-block;background:var(--mark);color:var(--markink);border-radius:6px;padding:0 8px;font-size:13px}
</style>
</head>
<body>
<main>
<h1>$project</h1>
<p class="sub">Copy the code with one click and paste it into VS Code. Lines <span class="legend">highlighted</span> need your own value.</p>

<section class="card">
<div class="head"><h2>main.tf: the complete infrastructure in one file</h2>
<button class="copy" type="button" data-label="Copy main.tf" data-copy="raw-main">Copy main.tf</button></div>
<p class="hint">Save as <code class="i">main.tf</code> in an empty folder.</p>
$main_block
</section>

<section class="card">
<div class="head"><h2>terraform.tfvars: your values</h2>
<button class="copy" type="button" data-label="Copy terraform.tfvars" data-copy="raw-tfvars">Copy terraform.tfvars</button></div>
<p class="hint">Save next to main.tf, replace every <code class="i">FILL_</code> value, and never share or commit this file.</p>
$tfvars_block
</section>

<section class="card">
<h2>Or one file per service</h2>
<p class="hint">Use these instead of main.tf, never both. Put them all in one empty folder with terraform.tfvars.</p>
$split_blocks
</section>

<section class="card">
<h2>How to deploy</h2>
<ol>
<li>Make an empty folder and save the files above in it.</li>
<li>Fill every <code class="i">FILL_</code> value in <code class="i">terraform.tfvars</code>.</li>
<li>Run <code class="i">terraform init</code>, then <code class="i">terraform plan</code> to see what will be created.</li>
<li>Run <code class="i">terraform apply</code> to build it.</li>
<li>When finished, run <code class="i">terraform destroy</code> to stop charges.</li>
</ol>
</section>
</main>
<script>
function fallbackCopy(text){
  var ta = document.createElement("textarea");
  ta.value = text;
  ta.style.position = "fixed";
  ta.style.opacity = "0";
  document.body.appendChild(ta);
  ta.select();
  try { document.execCommand("copy"); } catch (e) {}
  document.body.removeChild(ta);
}
function copyText(text, btn){
  var done = function(){
    btn.textContent = "Copied";
    btn.classList.add("ok");
    setTimeout(function(){
      btn.textContent = btn.getAttribute("data-label");
      btn.classList.remove("ok");
    }, 1800);
  };
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text).then(done, function(){ fallbackCopy(text); done(); });
  } else {
    fallbackCopy(text);
    done();
  }
}
document.addEventListener("click", function(e){
  var btn = e.target.closest("[data-copy]");
  if (!btn) { return; }
  copyText(document.getElementById(btn.getAttribute("data-copy")).value, btn);
});
</script>
</body>
</html>
""")


def _code(raw_id, text):
    """A highlighted, scrollable code view plus a hidden textarea holding the exact text."""
    lines = []
    for line in text.splitlines():
        marked = ">>> USER" in line or "FILL_" in line
        cls = "ln user" if marked else "ln"
        lines.append(f'<span class="{cls}">{html.escape(line)}</span>')
    return (
        f'<pre aria-label="Terraform code">{"".join(lines)}</pre>'
        f'<textarea id="{raw_id}" hidden>{html.escape(text)}</textarea>'
    )


def build_copy_page(project, main_tf, tfvars, split_files):
    """split_files: ordered list of (filename, text)."""
    split_blocks = []
    for i, (name, text) in enumerate(split_files):
        raw_id = f"raw-split-{i}"
        split_blocks.append(
            f"<details><summary>{html.escape(name)}</summary>"
            f'<div class="head"><span class="hint">Save as {html.escape(name)}</span>'
            f'<button class="copy" type="button" data-label="Copy {html.escape(name)}" '
            f'data-copy="{raw_id}">Copy {html.escape(name)}</button></div>'
            f"{_code(raw_id, text)}</details>"
        )
    return PAGE.substitute(
        title=html.escape(f"{project} - Terraform code"),
        project=html.escape(project),
        main_block=_code("raw-main", main_tf),
        tfvars_block=_code("raw-tfvars", tfvars),
        split_blocks="\n".join(split_blocks),
    )


def write_copy_page(path, project, main_tf, tfvars, split_files):
    Path(path).write_text(build_copy_page(project, main_tf, tfvars, split_files), encoding="utf-8")
