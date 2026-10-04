#!/usr/bin/env python3
"""
Add every person who has ever held a roster to league.json's managers, from the dataset.

    python3 scripts/sync-managers.py            # add missing managers, report what it did
    python3 scripts/sync-managers.py --photos   # also download each new manager's Sleeper
                                                #   avatar into league/managers/<handle>.<ext>

A new entry gets the Sleeper user_id and display name and nothing else; real names, bios,
hometowns and rivals are for the league to add. Existing entries are never changed, and
orphaned rosters (pull-league-history.py's stand-in managers) are never added. Run it after
scripts/pull-league-history.py, at setup and whenever someone new joins.

Photos are served from league/managers/ rather than hotlinked, because a Sleeper avatar URL
changes when its owner changes their avatar. Each file is named after the manager's Sleeper
handle, and its extension comes from the file's bytes: Sleeper's Content-Type header is not
reliable (it has served JPEG bytes labelled image/png).
"""
import json
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from league_config import CONFIG, CONFIG_PATH, DATA_DIR  # noqa: E402

PHOTO_DIR = os.path.join(os.path.dirname(CONFIG_PATH), "managers")


def sniff(data):
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    return None


def download_avatar(avatar, handle):
    url = f"https://sleepercdn.com/avatars/{avatar}"
    with urllib.request.urlopen(url, timeout=30) as r:
        data = r.read()
    ext = sniff(data)
    if not ext:
        raise ValueError(f"unrecognised image format from {url}")
    name = re.sub(r"[^a-z0-9_-]+", "", handle.lower()) or avatar
    os.makedirs(PHOTO_DIR, exist_ok=True)
    path = os.path.join(PHOTO_DIR, f"{name}.{ext}")
    with open(path, "wb") as f:
        f.write(data)
    return os.path.basename(path)


def main():
    photos = "--photos" in sys.argv[1:]
    with open(os.path.join(DATA_DIR, "league-history.json")) as f:
        history = json.load(f)

    entries = CONFIG.setdefault("managers", [])
    known = {m["userId"] for m in entries}
    # Most recent season first, so current managers lead and departed ones follow, as the
    # Managers page lists them.
    people = [(uid, m) for uid, m in history["managers"].items()
              if m.get("seasons_rostered") and not m.get("orphan")]
    people.sort(key=lambda x: (-max(int(s) for s in x[1]["seasons_rostered"]), x[1].get("handle") or ""))

    added = []
    for uid, m in people:
        if uid in known:
            continue
        handle = m.get("handle") or uid
        entry = {"userId": uid, "name": handle}
        if photos and m.get("avatar"):
            try:
                entry["photo"] = download_avatar(m["avatar"], handle)
            except Exception as err:  # a missing avatar must not stop the sync
                print(f"  no photo for {handle}: {err}", file=sys.stderr)
        entries.append(entry)
        added.append(entry)

    if not added:
        print(f"league.json already lists all {len(people)} managers")
        return 0
    with open(CONFIG_PATH, "w") as f:
        f.write(json.dumps(CONFIG, indent=2, ensure_ascii=False) + "\n")
    print(f"added {len(added)} manager(s) to {os.path.relpath(CONFIG_PATH)}:")
    for e in added:
        print(f"  {e['userId']}  {e['name']}" + (f"  ({e['photo']})" if e.get("photo") else ""))
    print("Their names are Sleeper handles; replace them with real names, and add bios, "
          "hometowns and rivals as the league supplies them.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
