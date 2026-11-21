"""Builds the downloadable PDF: summary, architecture diagram, notes and the Terraform code."""
import math
from datetime import date
from xml.sax.saxutils import escape

from reportlab.graphics.shapes import Circle, Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (ListFlowable, ListItem, PageBreak, Paragraph,
                                Preformatted, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

ACCENT = colors.HexColor("#0E6B5C")
LIGHT = colors.HexColor("#E6F2EF")
INK = colors.HexColor("#14181F")
MUTED = colors.HexColor("#4A5260")
LINE = colors.HexColor("#C5CAD3")
WARN_BG = colors.HexColor("#FFF6E0")
WARN_LINE = colors.HexColor("#E8C873")

TITLE = ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=INK)
SUB = ParagraphStyle("sub", fontName="Helvetica", fontSize=10, leading=14, textColor=MUTED)
H2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=14, leading=18, textColor=ACCENT,
                    spaceBefore=16, spaceAfter=6)
BODY = ParagraphStyle("body", fontName="Helvetica", fontSize=10, leading=14, textColor=INK)
CELL = ParagraphStyle("cell", parent=BODY, fontSize=9, leading=12)
CODE = ParagraphStyle("code", fontName="Courier", fontSize=7.5, leading=9.4, textColor=INK)


def _t(value):
    """Standard PDF fonts only cover Latin-1: replace anything else so nothing breaks."""
    return str(value).encode("latin-1", "replace").decode("latin-1")


def _p(text, style=BODY):
    return Paragraph(escape(_t(text)), style)


def _bullets(items):
    if not items:
        items = ["None"]
    return ListFlowable(
        [ListItem(_p(i), leftIndent=14) for i in items],
        bulletType="bullet", start="\u2022", leftIndent=14,
    )


# ---------------------------------------------------------------- diagram helpers
def _text(d, x, y, s, size=9, bold=False, anchor="start", color=INK):
    d.add(String(x, y, _t(s), fontName="Helvetica-Bold" if bold else "Helvetica",
                 fontSize=size, fillColor=color, textAnchor=anchor))


def _box(d, x, y, w, h, fill, stroke, dash=None, width=1.2):
    d.add(Rect(x, y, w, h, rx=6, ry=6, fillColor=fill, strokeColor=stroke,
               strokeWidth=width, strokeDashArray=dash))


def _node(d, x, y, w, h, title, sub=""):
    _box(d, x, y, w, h, LIGHT, ACCENT)
    cx = x + w / 2
    if sub:
        _text(d, cx, y + h - 14, title, 9, True, "middle")
        _text(d, cx, y + 7, sub, 8, False, "middle", MUTED)
    else:
        _text(d, cx, y + h / 2 - 3, title, 9, True, "middle")


def _arrow(d, x1, y1, x2, y2, label=None, dx=6, dy=4):
    d.add(Line(x1, y1, x2, y2, strokeColor=INK, strokeWidth=1.2))
    length = math.hypot(x2 - x1, y2 - y1) or 1
    ux, uy = (x2 - x1) / length, (y2 - y1) / length
    px, py = -uy, ux
    bx, by = x2 - ux * 7, y2 - uy * 7
    d.add(Polygon([x2, y2, bx + px * 3.5, by + py * 3.5, bx - px * 3.5, by - py * 3.5],
                  fillColor=INK, strokeColor=INK))
    if label:
        _text(d, (x1 + x2) / 2 + dx, (y1 + y2) / 2 + dy, label, 8, False, "start", MUTED)


def _diagram(components, ctx, region_label):
    has = set(components)
    d = Drawing(495, 270)

    _box(d, 100, 8, 388, 254, colors.white, MUTED, dash=[4, 3], width=1)
    _text(d, 110, 248, f"AWS Cloud: {region_label}", 9, True, color=MUTED)

    if "ec2" in has:
        d.add(Circle(45, 143, 26, fillColor=colors.white, strokeColor=INK, strokeWidth=1.2))
        _text(d, 45, 140, "Client", 9, anchor="middle")

    if "vpc" in has:
        _box(d, 112, 66, 364, 170, colors.white, ACCENT, dash=[5, 3])
        _text(d, 122, 222, "VPC 10.0.0.0/16", 9, True, color=ACCENT)
        _node(d, 122, 125, 70, 36, "Internet", "gateway")

        if "ec2" in has:
            _box(d, 215, 150, 250, 62, colors.white, LINE, dash=[3, 3], width=1)
            _text(d, 223, 200, "Public subnets (2 zones)", 8, color=MUTED)
            _node(d, 285, 156, 150, 34, "EC2 web server", ctx["instance_type"])
            _arrow(d, 71, 143, 122, 143, "HTTP 80", dx=-15, dy=6)
            _arrow(d, 192, 143, 285, 173)

        if "rds" in has:
            _box(d, 215, 76, 250, 62, colors.white, LINE, dash=[3, 3], width=1)
            _text(d, 223, 126, "Private subnets (2 zones)", 8, color=MUTED)
            ha = ", Multi-AZ" if ctx["db_multi_az"] else ""
            _node(d, 285, 82, 150, 34, f"RDS {ctx['db_engine']}",
                  f"{ctx['db_instance_class']}{ha}")
            if "ec2" in has:
                _arrow(d, 360, 156, 360, 117, f"port {ctx['db_port']}")

    if "s3" in has:
        _node(d, 122, 20, 230, 34, "S3 bucket", "private, encrypted, versioned")

    return d


# ---------------------------------------------------------------- document
def _footer(project):
    def draw(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(48, 28, _t(f"Terra-GEN  |  {project}"))
        canvas.drawRightString(A4[0] - 48, 28, f"Page {doc.page}")
        canvas.restoreState()
    return draw


def _table(rows, widths, header=None):
    data = []
    if header:
        data.append([_p(h, ParagraphStyle("th", parent=CELL, fontName="Helvetica-Bold"))
                     for h in header])
    data += [[_p(a, CELL), _p(b, CELL)] for a, b in rows]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), LIGHT))
    t.setStyle(TableStyle(style))
    return t


def build_pdf(path, data):
    """data keys: project, region_label, budget, environment, high_availability, traffic,
    components, ctx, decisions, not_covered, notes (flow/security/cost),
    fill_in [(name, description)], main_tf, tfvars."""
    project = data["project"]
    story = []

    story += [
        _p(f"{project}", TITLE),
        Spacer(1, 4),
        _p(f"AWS infrastructure package, generated by Terra-GEN on {date.today():%d %B %Y}", SUB),
        Spacer(1, 12),
    ]

    story.append(_table([
        ("Region", data["region_label"]),
        ("Budget", data["budget"]),
        ("Environment", data["environment"]),
        ("High availability", "yes" if data["high_availability"] else "no"),
        ("Expected traffic", data["traffic"]),
        ("Components built", ", ".join(data["components"])),
    ], [120, 379]))

    story.append(_p("1. Architecture", H2))
    story.append(_diagram(data["components"], data["ctx"], data["region_label"]))
    story.append(Spacer(1, 6))
    story.append(_p("How traffic flows", ParagraphStyle("b", parent=BODY, fontName="Helvetica-Bold")))
    story.append(Spacer(1, 3))
    story.append(_bullets(data["notes"]["flow"]))

    story.append(_p("2. Decisions made", H2))
    story.append(_bullets(data["decisions"]))

    story.append(_p("3. Security", H2))
    story.append(_bullets(data["notes"]["security"]))

    story.append(_p("4. Cost notes", H2))
    story.append(_bullets(data["notes"]["cost"]))
    story.append(Spacer(1, 4))
    story.append(_p("Check current prices with the AWS Pricing Calculator before quoting a total.", SUB))

    story.append(_p("5. Not covered, write manually", H2))
    box = Table([[_bullets(data["not_covered"])]], colWidths=[499])
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), WARN_BG),
        ("BOX", (0, 0), (-1, -1), 0.8, WARN_LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(box)

    story.append(_p("6. Before you deploy", H2))
    story.append(_p("Open terraform.tfvars and replace every FILL_ value. These are the only "
                    "values you edit:"))
    story.append(Spacer(1, 6))
    story.append(_table(data["fill_in"], [140, 359], header=["Value", "What to enter"]))
    story.append(Spacer(1, 8))
    story.append(_bullets([
        "Use only one folder: merged (one main.tf) or split (one file per service). "
        "Both build the same infrastructure.",
        "Run: terraform init, then terraform plan (shows what will be created), "
        "then terraform apply.",
        "When finished, run terraform destroy to stop charges.",
        "Never share terraform.tfvars or commit it to Git: it holds your keys.",
    ]))

    story.append(PageBreak())
    story.append(_p("7. Terraform code (main.tf)", H2))
    story.append(_p("The same code is also supplied one file per service in the split folder.", SUB))
    story.append(Spacer(1, 6))
    story.append(Preformatted(_t(data["main_tf"]), CODE))

    story.append(PageBreak())
    story.append(_p("8. terraform.tfvars (fill in before deploying)", H2))
    story.append(Spacer(1, 6))
    story.append(Preformatted(_t(data["tfvars"]), CODE))

    doc = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=48, rightMargin=48,
                            topMargin=44, bottomMargin=48,
                            title=_t(f"{project} infrastructure package"), author="Terra-GEN")
    footer = _footer(project)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


def diagram_svg(components, ctx, region_label):
    """The same architecture diagram as inline SVG for the web page."""
    from reportlab.graphics import renderSVG

    svg = renderSVG.drawToString(_diagram(components, ctx, region_label))
    svg = svg[svg.index("<svg"):]
    svg = svg.replace("font-family: Helvetica-Bold;",
                      "font-family: system-ui, Arial, sans-serif; font-weight: 700;")
    svg = svg.replace("font-family: Helvetica;", "font-family: system-ui, Arial, sans-serif;")
    return svg
