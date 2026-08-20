"""Merge a fresh Allure report into the accumulating GitHub Pages site.

Run by CI (see .github/workflows/api-tests.yml) against a checkout of the `gh-pages` branch.
Given this run's freshly-generated Allure report, it:

  - copies the report into runs/<run_number>/
  - prunes runs/* beyond the retention count (oldest first)
  - rewrites latest/index.html as a redirect to the newest run
  - rewrites the root index.html: a table of all kept runs with pass/fail counts

Stdlib-only by design — this runs in CI before dependencies are guaranteed installed, and keeps the
publish step dependency-free.
"""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from html import escape
from pathlib import Path


@dataclass(frozen=True)
class RunInfo:
    number: int
    sha: str
    actor: str
    event: str
    timestamp: str  # ISO-8601 UTC, passed in by the workflow (Date.now() isn't available in-script)


def merge_run(site_dir: Path, report_dir: Path, run: RunInfo) -> Path:
    """Copy this run's report into site_dir/runs/<number>/, replacing any prior copy.

    Also drops a meta.json alongside the report so the index page can show this run's commit/actor/
    timestamp again later, once it's no longer the "current" run being generated.
    """
    dest = site_dir / "runs" / str(run.number)
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(report_dir, dest)
    (dest / "meta.json").write_text(
        json.dumps({"sha": run.sha, "actor": run.actor, "event": run.event, "timestamp": run.timestamp})
    )
    return dest


def prune_old_runs(site_dir: Path, retain: int) -> list[int]:
    """Delete runs/* beyond the retention count, oldest first. Returns the removed run numbers."""
    runs_dir = site_dir / "runs"
    if not runs_dir.exists():
        return []

    numbers = sorted(
        (int(p.name) for p in runs_dir.iterdir() if p.is_dir() and p.name.isdigit()),
        reverse=True,
    )
    to_remove = numbers[retain:]
    for number in to_remove:
        shutil.rmtree(runs_dir / str(number))
    return to_remove


def kept_run_numbers(site_dir: Path) -> list[int]:
    runs_dir = site_dir / "runs"
    if not runs_dir.exists():
        return []
    return sorted(
        (int(p.name) for p in runs_dir.iterdir() if p.is_dir() and p.name.isdigit()),
        reverse=True,
    )


def read_summary(site_dir: Path, run_number: int) -> dict | None:
    summary_path = site_dir / "runs" / str(run_number) / "widgets" / "summary.json"
    if not summary_path.exists():
        return None
    try:
        return json.loads(summary_path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def read_meta(site_dir: Path, run_number: int) -> dict | None:
    meta_path = site_dir / "runs" / str(run_number) / "meta.json"
    if not meta_path.exists():
        return None
    try:
        return json.loads(meta_path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def write_latest_redirect(site_dir: Path, newest_run: int) -> None:
    latest_dir = site_dir / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    target = f"../runs/{newest_run}/index.html"
    (latest_dir / "index.html").write_text(
        f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="0; url={escape(target)}">
  <title>Latest Allure report</title>
</head>
<body>
  <p>Redirecting to the latest report&hellip; <a href="{escape(target)}">click here</a> if you're not
  redirected automatically.</p>
</body>
</html>
"""
    )


def _row_html(site_dir: Path, run_number: int, repo: str) -> str:
    summary = read_summary(site_dir, run_number)
    if summary is not None:
        stats = summary.get("statistic", {})
        counts = (
            f"{stats.get('passed', '?')} passed / "
            f"{stats.get('failed', '?')} failed / "
            f"{stats.get('total', '?')} total"
        )
    else:
        counts = "—"

    meta = read_meta(site_dir, run_number)
    sha = meta.get("sha", "—") if meta else "—"
    actor = meta.get("actor", "—") if meta else "—"
    event = meta.get("event", "—") if meta else "—"
    timestamp = meta.get("timestamp", "—") if meta else "—"

    sha_cell = (
        f'<a href="https://github.com/{escape(repo)}/commit/{escape(sha)}">{escape(sha[:7])}</a>'
        if sha != "—"
        else "—"
    )

    return (
        "<tr>"
        f'<td><a href="runs/{run_number}/index.html">#{run_number}</a></td>'
        f"<td>{sha_cell}</td>"
        f"<td>{escape(event)}</td>"
        f"<td>{escape(actor)}</td>"
        f"<td>{escape(timestamp)}</td>"
        f"<td>{escape(counts)}</td>"
        "</tr>"
    )


def write_index(site_dir: Path, repo: str) -> None:
    rows = "\n".join(_row_html(site_dir, n, repo) for n in kept_run_numbers(site_dir))
    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Allure reports — {escape(repo)}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ text-align: left; padding: 0.5rem 0.75rem; border-bottom: 1px solid #ddd; }}
    th {{ background: #f5f5f5; }}
    a {{ color: #0969da; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <h1>Allure reports</h1>
  <p><a href="latest/index.html"><strong>&#128202; Latest report</strong></a></p>
  <table>
    <thead>
      <tr>
        <th>Run</th><th>Commit</th><th>Trigger</th><th>Actor</th><th>Timestamp (UTC)</th><th>Result</th>
      </tr>
    </thead>
    <tbody>
      {rows}
    </tbody>
  </table>
</body>
</html>
"""
    (site_dir / "index.html").write_text(html)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-dir", required=True, type=Path)
    parser.add_argument("--report-dir", required=True, type=Path)
    parser.add_argument("--run-number", required=True, type=int)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--event", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--timestamp", required=True, help="ISO-8601 UTC timestamp for this run")
    parser.add_argument("--retain", required=True, type=int)
    args = parser.parse_args()

    run = RunInfo(
        number=args.run_number,
        sha=args.sha,
        actor=args.actor,
        event=args.event,
        timestamp=args.timestamp,
    )

    args.site_dir.mkdir(parents=True, exist_ok=True)
    merge_run(args.site_dir, args.report_dir, run)

    removed = prune_old_runs(args.site_dir, args.retain)
    if removed:
        print(f"Pruned {len(removed)} old run(s) beyond retention ({args.retain}): {removed}")

    write_latest_redirect(args.site_dir, run.number)
    write_index(args.site_dir, args.repo)
    print(f"Published run #{run.number} to site dir: {args.site_dir}")


if __name__ == "__main__":
    main()
