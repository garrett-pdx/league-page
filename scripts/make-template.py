#!/usr/bin/env python3
"""
Assemble the public template repository from this repository's committed HEAD.

    python3 scripts/make-template.py <empty output directory>

This repository is one league's site (its content in league/). The template is the same engine
with the demo league from template/ in its place, a fresh git history, and an `.engine-files`
manifest that scripts/update-engine.py uses to update any site built from it. Steps:

  1. export HEAD (committed files only) into the output directory;
  2. drop this league's content, data, docs and one-off scripts, and template/ itself;
  3. put template/league, template/README.md and template/CHANGELOG.md in their place;
  4. build the demo league's dataset from Sleeper and generate its brand (needs network, and
     this repository's node_modules for the icon renderer);
  5. write the manifest, then `git init` and commit.

Nothing is pushed. Review the result, then create the GitHub repository and push it yourself.
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# This league's material, never part of the template (paths relative to the export).
DROP = [
    "league", "template", "docs/league-lore.md", "README.md", "CHANGELOG.md",
    "static/data/projections", "scripts/analyze-draft-positions.py",
    "scripts/derive-draft-report.py", "scripts/make-template.py",
]
ENGINE_DOCS = {"setup.md", "writing.md", "data.md"}

# What counts as engine is defined once, in update-engine.py.
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location("update_engine", os.path.join(ROOT, "scripts", "update-engine.py"))
UPDATE = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(UPDATE)


def run(cmd, cwd, env=None):
    print("$ " + " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True, env=env)


def inside(out, rel):
    path = os.path.realpath(os.path.join(out, rel))
    if not path.startswith(os.path.realpath(out) + os.sep):
        raise SystemExit(f"refusing to touch {path}: outside {out}")
    return path


def remove(out, rel):
    path = inside(out, rel)
    if os.path.isdir(path) and not os.path.islink(path):
        shutil.rmtree(path)
    elif os.path.lexists(path):
        os.remove(path)


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    out = os.path.abspath(sys.argv[1])
    os.makedirs(out, exist_ok=True)
    if os.listdir(out):
        raise SystemExit(f"{out} is not empty")
    if subprocess.run(["git", "diff", "--quiet", "HEAD"], cwd=ROOT).returncode:
        raise SystemExit("uncommitted changes: the template is built from HEAD, so commit first")
    for need in ("template/league/league.json", "template/README.md", "template/CHANGELOG.md"):
        if not os.path.exists(os.path.join(ROOT, need)):
            raise SystemExit(f"missing {need}")

    # 1. export
    archive = subprocess.run(["git", "archive", "HEAD"], cwd=ROOT, check=True, capture_output=True).stdout
    subprocess.run(["tar", "-x", "-C", out], input=archive, check=True)

    # 2. drop this league's material
    for rel in DROP:
        remove(out, rel)
    for name in os.listdir(inside(out, "docs")):
        if name.endswith(".md") and name not in ENGINE_DOCS:
            remove(out, os.path.join("docs", name))
    for rel in ("static/data", "static/brand"):
        for name in os.listdir(inside(out, rel)):
            if name != "README.md":
                remove(out, os.path.join(rel, name))

    # 3. the demo league
    shutil.copytree(os.path.join(ROOT, "template/league"), inside(out, "league"))
    for d in ("league/managers", "league/drafts", "league/brand"):
        os.makedirs(inside(out, d), exist_ok=True)
        open(inside(out, os.path.join(d, ".gitkeep")), "w").close()
    shutil.copy2(os.path.join(ROOT, "template/README.md"), inside(out, "README.md"))
    shutil.copy2(os.path.join(ROOT, "template/CHANGELOG.md"), inside(out, "CHANGELOG.md"))

    # 4. data and brand, with the export's own scripts
    env = {k: v for k, v in os.environ.items() if not k.startswith("LEAGUE_")}
    run([sys.executable, "scripts/pull-league-history.py"], out, env)
    run([sys.executable, "scripts/derive-site-data.py"], out, env)
    run([sys.executable, "scripts/derive-narratives.py"], out, env)
    link = inside(out, "node_modules")
    os.symlink(os.path.join(ROOT, "node_modules"), link)
    try:
        run(["node", "scripts/brand.mjs"], out, env)
    finally:
        os.unlink(link)

    # 5. manifest and history
    engine = UPDATE.engine_files(out)
    UPDATE.write_manifest(out, engine)

    run(["git", "init", "-q"], out)
    run(["git", "symbolic-ref", "HEAD", "refs/heads/main"], out)  # `init -b` needs git 2.28
    run(["git", "add", "-A"], out)
    version = subprocess.run(["node", "-p", "require('./package.json').version"], cwd=out,
                             capture_output=True, text=True).stdout.strip()
    run(["git", "commit", "-q", "-m", f"Fantasy Football Website with History {version}"], out)
    print(f"\ntemplate ready in {out}: {len(engine)} engine files. Nothing has been pushed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
