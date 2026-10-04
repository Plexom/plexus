#!/usr/bin/env python3
"""Builds the progress page from the project's state.

Reads plexus/ — the product, iterations, tasks, decisions, the backlog, the
changelog — and the git history, and writes one self-contained HTML file with no
external dependencies. The page is for someone who does not live in the project,
so finished work is shown as what the product can now do, not as closed tasks.

Run from the project root:  python3 dashboard.py [output file]
"""
import re
import subprocess
import sys
from datetime import date, datetime
from html import escape
from pathlib import Path

from plexus_state import (ROOT, STATE, SKIPPED, CLOSED_TASK, OPEN_ITERATION, load, ids,
                          feature_status, last_accepted, task_waits, versions, attribution)


def git(*args):
    try:
        out = subprocess.run(["git", *args], capture_output=True, text=True, cwd=ROOT)
        return out.stdout.strip() if out.returncode == 0 else ""
    except OSError:
        return ""


def days_since(value):
    try:
        return (date.today() - datetime.strptime(str(value), "%Y-%m-%d").date()).days
    except (ValueError, TypeError):
        return None


CSS = """
:root{--bg:#fbfbfa;--card:#fff;--ink:#1a1a19;--dim:#6b6b66;--line:#e6e4df;
--ok:#2d7d4f;--warn:#b5751a;--bad:#b23b3b;--accent:#3b6ea5;--shadow:0 1px 2px rgba(0,0,0,.05)}
@media(prefers-color-scheme:dark){:root{--bg:#16171a;--card:#1e2024;--ink:#e8e6e3;--dim:#9a978f;
--line:#2e3138;--ok:#5cbb85;--warn:#d9a44a;--bad:#e07070;--accent:#7aa8d8;--shadow:none}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:14px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif}
.wrap{max-width:1100px;margin:0 auto;padding:32px 20px 64px}
h1{font-size:22px;margin:0 0 2px;letter-spacing:-.01em}
.sub{color:var(--dim);font-size:13px;margin-bottom:24px}
.grid{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));margin-bottom:28px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;box-shadow:var(--shadow)}
.stat .n{font-size:26px;font-weight:600;letter-spacing:-.02em}
.stat .l{color:var(--dim);font-size:12px;margin-top:3px}
section{background:var(--card);border:1px solid var(--line);border-radius:10px;
padding:18px 20px;margin-bottom:16px;box-shadow:var(--shadow)}
h2{font-size:14px;margin:0 0 12px;letter-spacing:.02em;text-transform:uppercase;color:var(--dim);font-weight:600}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;color:var(--dim);font-weight:500;font-size:12px;padding:4px 10px 8px 0;border-bottom:1px solid var(--line)}
td{padding:8px 10px 8px 0;border-bottom:1px solid var(--line);vertical-align:top}
tr:last-child td{border-bottom:none}
.tag{display:inline-block;padding:1px 8px;border-radius:20px;font-size:11.5px;border:1px solid var(--line);white-space:nowrap}
.t-accepted,.t-done{color:var(--ok);border-color:currentColor}
.t-in-progress,.t-verify{color:var(--accent);border-color:currentColor}
.t-critical{color:var(--bad);border-color:currentColor}
.t-major{color:var(--warn);border-color:currentColor}
.t-todo,.t-planned,.t-wontfix,.t-dropped,.t-minor{color:var(--dim)}
.bar{height:6px;background:var(--line);border-radius:3px;overflow:hidden;margin:10px 0 4px}
.bar>i{display:block;height:100%;background:var(--ok)}
.dim{color:var(--dim)}
.mono{font-variant-numeric:tabular-nums}
.empty{color:var(--dim);font-style:italic;font-size:13px}
.scroll{overflow-x:auto}
.age{font-size:11.5px;color:var(--dim)}
.t-questioned{color:var(--warn);border-color:currentColor}
.t-open{color:var(--dim)}
details summary{cursor:pointer;color:var(--dim);font-size:12.5px}
"""


def stat(n, label):
    return f'<div class="stat"><div class="n">{n}</div><div class="l">{escape(label)}</div></div>'


def tag(value):
    v = str(value or "—")
    return f'<span class="tag t-{escape(v.replace(" ", "-"))}">{escape(v)}</span>'


def section(title, inner):
    return f"<section><h2>{escape(title)}</h2>{inner}</section>"


def build():
    s = load()
    iterations, tasks, decisions = s["iterations"], s["tasks"], s["decisions"]
    features, constraints = s["features"], s["constraints"]
    status = {f["id"]: feature_status(f, iterations) for f in features}
    mvp = [f for f in features if f["scope"] == "mvp"]
    mvp_done = sum(1 for f in mvp if status[f["id"]][0] == "done")
    live_its = [i for i in iterations if i.get("status") != "dropped"]
    accepted = [i for i in live_its if i.get("status") == "accepted"]
    open_tasks = [t for t in tasks if t.get("status") not in CLOSED_TASK]
    critical = [t for t in open_tasks if t.get("type") == "bug" and t.get("severity") == "critical"]
    in_force = [d for d in decisions if d.get("status") == "accepted"]
    questioned = [d for d in decisions if d.get("status") == "questioned"]
    superseded = [d for d in decisions if d.get("status") == "superseded"]
    held_at = last_accepted(iterations)

    rel = versions()
    branch = git("branch", "--show-current") or "—"
    dirty = bool(git("status", "--porcelain"))
    built = datetime.now().strftime("%Y-%m-%d %H:%M")

    p = [f"<!-- generated {built} -->", "<style>", CSS, "</style>", '<div class="wrap">',
         f"<h1>{escape(ROOT.name)}"
         + (f" <span class='dim'>{escape(rel[0][0])}</span>" if rel else "") + "</h1>",
         f'<div class="sub">built {built} · branch {escape(branch)} · '
         f'{"uncommitted changes present" if dirty else "working tree clean"}</div>']

    p += ['<div class="grid">',
          stat(f"{mvp_done}/{len(mvp)}" if mvp else "—", "MVP features done"),
          stat(f"{len(accepted)}/{len(live_its)}", "iterations accepted"),
          stat(len(open_tasks), "open tasks" + (f" · {len(critical)} critical bug" if critical else "")),
          stat(f"{len(in_force)}" + (f" · {len(questioned)}?" if questioned else ""), "decisions in force"),
          stat(len(s["debt"]), "debt lines"),
          "</div>"]

    # Features — the product as it stands
    if features:
        pct = round(100 * mvp_done / len(mvp)) if mvp else 0
        rows = [f'<div class="bar"><i style="width:{pct}%"></i></div>'
                f'<div class="dim" style="margin-bottom:12px">MVP {pct}% — counted by features, '
                'not by tasks</div><table>']
        for f in features:
            st, it = status[f["id"]]
            where = f" · {escape(it)}" if it else ""
            cls = "" if st in ("done", "in progress") else ' class="dim"'
            rows.append(f"<tr><td class='mono' style='width:110px'>{escape(f['id'])}</td>"
                        f"<td{cls}>{escape(f['text'])}</td>"
                        f"<td style='width:70px' class='dim'>{escape(f['scope'] or '—')}</td>"
                        f"<td style='width:190px'>{tag(st)}{where}</td></tr>")
        rows.append("</table>")
        p.append(section("Features", "".join(rows)))
    else:
        p.append(section("Features", '<div class="empty">No features recorded in the spec yet.</div>'))

    # Constraints — held as of the last acceptance, since verification checks all of them
    if constraints:
        note = (f"Checked on every iteration; last held at {escape(held_at)}." if held_at
                else "Not checked yet: no iteration has been accepted.")
        rows = [f'<div class="dim" style="margin-bottom:10px">{note}</div><table>']
        for c in constraints:
            rows.append(f"<tr><td class='mono' style='width:130px'>{escape(c['id'])}</td>"
                        f"<td>{escape(c['text'])}</td><td class='dim'>{escape(c['check'])}</td></tr>")
        rows.append("</table>")
        p.append(section("Constraints", "".join(rows)))

    # Iterations — accepted ones in one line with what they delivered; tasks folded
    if iterations:
        rows = ["<table>"]
        for it in sorted(iterations, key=lambda x: x["id"]):
            own = sorted((t for t in tasks if ids(t.get("iteration")) == [it["id"]]), key=lambda x: x["id"])
            names = ", ".join(ids(it.get("delivers"))) or "—"
            folded = ""
            if own:
                items = "".join(f"<li>{escape(t['id'])} · {escape(str(t.get('title', '')))} "
                                f"{tag(t.get('status'))}</li>" for t in own)
                done = sum(1 for t in own if t.get("status") == "done")
                folded = f"<details><summary>{done}/{len(own)} tasks</summary><ul>{items}</ul></details>"
            rows.append(f"<tr><td class='mono' style='width:110px'>{escape(it['id'])}</td>"
                        f"<td>{escape(str(it.get('title', '')))}<div class='dim'>delivers {escape(names)}</div>"
                        f"{folded}</td><td style='width:110px'>{tag(it.get('status'))}</td></tr>")
        rows.append("</table>")
        p.append(section("Iterations", "".join(rows)))

    # Open tasks only: finished ones live under their iteration
    if open_tasks:
        rows = ["<table><tr><th>id</th><th>task</th><th>status</th><th>waits for</th></tr>"]
        for t in sorted(open_tasks, key=lambda x: x["id"]):
            waits = ", ".join(task_waits(t, s["tasks_by_id"], s["decisions_by_id"])) or "—"
            kind = " " + tag(t.get("severity")) if t.get("type") == "bug" else ""
            rows.append(f"<tr><td class='mono'>{escape(t['id'])}</td>"
                        f"<td>{escape(str(t.get('title', '')))}{kind}</td>"
                        f"<td>{tag(t.get('status'))}</td><td class='dim'>{escape(waits)}</td></tr>")
        rows.append("</table>")
        p.append(section("Open tasks", "".join(rows)))

    # Decisions — in force and in question; replaced ones only counted
    shown = sorted(questioned + in_force + [d for d in decisions if d.get("status") == "proposed"],
                   key=lambda x: x["id"])
    if shown or superseded:
        rows = ["<table>"]
        for d in shown:
            rows.append(f"<tr><td class='mono' style='width:110px'>{escape(d['id'])}</td>"
                        f"<td>{escape(str(d.get('title', '')))}</td>"
                        f"<td style='width:110px'>{tag(d.get('status'))}</td></tr>")
        rows.append("</table>")
        if superseded:
            rows.append(f'<div class="dim" style="margin-top:8px">{len(superseded)} replaced '
                        'decisions kept as history.</div>')
        p.append(section("Decisions", "".join(rows)))

    # Backlog in its two blocks
    for title, items in (("Debt", s["debt"]), ("Ideas", s["ideas"])):
        if items:
            rows = ["<table>"] + [
                f"<tr><td class='mono' style='width:110px'>{escape(i['id'])}</td>"
                f"<td>{escape(i['text'])}</td><td class='dim'>{escape(' — '.join(i['rest']))}</td></tr>"
                for i in items] + ["</table>"]
            p.append(section(title, "".join(rows)))

    if rel:
        p.append(section("Versions", "<table>" + "".join(
            f"<tr><td class='mono' style='width:110px'>{escape(v)}</td><td class='dim'>{escape(d)}</td></tr>"
            for v, d in rel) + "</table>"))

    if SKIPPED:
        items = "".join(f"<li>{escape(str(path.relative_to(ROOT) if path.is_absolute() else path))}"
                        f" — {escape(why)}</li>" for path, why in SKIPPED)
        p.append(section("Files that could not be read",
                         '<div class="empty">These files did not reach the page; while they are listed, '
                         f'every number above is an undercount.</div><ul>{items}</ul>'))

    p.append('<div class="dim" style="font-size:12px;margin-top:20px">'
             f"Built {built} from the project state. This file is generated — edits to it will be lost."
             + (" Built with Plexus." if attribution() else "") + "</div>")
    p.append("</div>")
    return "\n".join(p)


if __name__ == "__main__":
    if not STATE.is_dir():
        print(f"no {STATE} directory — run from the root of a project with Plexus", file=sys.stderr)
        sys.exit(1)
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else STATE / "dashboard.html"
    html = build()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("<!doctype html><meta charset='utf-8'>"
                   f"<title>{escape(ROOT.name)} — progress</title>"
                   "<meta name='viewport' content='width=device-width,initial-scale=1'>" + html,
                   encoding="utf-8")
    print(f"built: {out} ({out.stat().st_size} bytes)")
    if SKIPPED:
        print(f"files skipped: {len(SKIPPED)} — the page is incomplete", file=sys.stderr)
        for path, why in SKIPPED:
            print(f"  {path} — {why}", file=sys.stderr)
        sys.exit(2)
