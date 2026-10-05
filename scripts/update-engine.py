#!/usr/bin/env python3
"""
Update this site's engine from the template, leaving the league alone.

    python3 scripts/update-engine.py            # the latest engine (the template's main branch)
    python3 scripts/update-engine.py v1.2.0     # a tag, branch or commit
    python3 scripts/update-engine.py --from DIR # a local checkout of the template instead

The engine is every file in the template except each site's own content and generated files
(engine_files() below). An update copies in every engine file of the new template, and removes
files the last update's list (`.engine-files`) had and the new one doesn't. Nothing else is
touched: not league/, not static/data/, not the generated brand (static/brand/, the icons,
src/theme/_league.scss), not README.md, and not any file a league added itself.

Refuses to run with uncommitted changes, so the update arrives as one reviewable diff. Afterwards:
`git diff`, then `npm install && npm run smui-theme-light`, read the CHANGELOG, and commit.
Stdlib only.
"""
import io
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = "garrett-pdx/fantasy-football-website-with-history"
MANIFEST = ".engine-files"

# Each site's own content and generated files: never part of the engine.
INSTANCE_DIRS = ("league/", "static/data/", "static/brand/", "static/favicons/", "try-league/",
                 "node_modules/", ".git/", ".svelte-kit/", "build/")
INSTANCE_FILES = {"README.md", "src/theme/_league.scss", "docs/league-lore.md", MANIFEST,
                  "static/pwa/apple-icon-180.png", "static/pwa/manifest-icon-192.png",
                  "static/pwa/manifest-icon-512.png", "static/smui.css", "static/smui-dark.css",
                  ".env"}


def engine_files(base):
    """Every engine file under base, as sorted relative paths."""
    out = []
    for dirpath, dirnames, filenames in os.walk(base):
        rel_dir = os.path.relpath(dirpath, base)
        rel_dir = "" if rel_dir == "." else rel_dir + "/"
        dirnames[:] = [d for d in dirnames if not (rel_dir + d + "/").startswith(INSTANCE_DIRS)]
        for f in filenames:
            rel = rel_dir + f
            if rel not in INSTANCE_FILES and f != ".DS_Store":
                out.append(rel)
    return sorted(out)


def write_manifest(base, files):
    with open(os.path.join(base, MANIFEST), "w") as f:
        f.write("# The engine's files at the last update, for scripts/update-engine.py. Do not edit;\n"
                "# everything not listed belongs to the league.\n")
        f.write("\n".join(files) + "\n")


def read_manifest(base):
    path = os.path.join(base, MANIFEST)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


def fetch(ref, dest):
    url = f"https://codeload.github.com/{REPO}/tar.gz/{ref}"
    print(f"downloading {url}")
    with urllib.request.urlopen(url, timeout=60) as r:
        data = r.read()
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        tar.extractall(dest)
    (top,) = os.listdir(dest)
    return os.path.join(dest, top)


def main():
    args = sys.argv[1:]
    status = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True)
    if status.stdout.strip():
        print("uncommitted changes; commit or stash them first so the update is one clean diff",
              file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory() as tmp:
        if "--from" in args:
            src = os.path.abspath(args[args.index("--from") + 1])
        else:
            src = fetch(next((a for a in args if not a.startswith("--")), "main"), tmp)

        if not os.path.exists(os.path.join(src, "schema", "league.schema.json")):
            print(f"{src} doesn't look like the template (no schema/league.schema.json)", file=sys.stderr)
            return 1
        new = engine_files(src)
        old = read_manifest(ROOT) or []
        protected = INSTANCE_DIRS

        copied = 0
        for rel in new:
            if rel.startswith(protected):
                continue  # never the league's content or generated files, whatever a manifest says
            source = os.path.join(src, rel)
            if not os.path.isfile(source):
                continue
            target = os.path.join(ROOT, rel)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copy2(source, target)
            copied += 1

        removed = []
        for rel in sorted(set(old) - set(new)):
            target = os.path.join(ROOT, rel)
            if not rel.startswith(protected) and os.path.isfile(target):
                os.remove(target)
                removed.append(rel)

        write_manifest(ROOT, new)

    print(f"engine updated: {copied} file(s) copied, {len(removed)} removed")
    for rel in removed:
        print(f"  removed {rel}")
    print("next: git diff; npm install && npm run smui-theme-light; read CHANGELOG.md; commit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
