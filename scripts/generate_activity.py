"""Generate a profile calendar from every branch in public repositories."""
import collections
import datetime as dt
import html
import json
import os
import pathlib
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"
USER = os.getenv("PROFILE_USER", "IsraelJulio")
TOKEN = os.getenv("GH_TOKEN", "")
TODAY = dt.datetime.now(dt.timezone.utc).date()
START = TODAY - dt.timedelta(days=364)


def pages(path, **params):
    params.update(per_page=100)
    page = 1
    while True:
        query = urllib.parse.urlencode(dict(params, page=page))
        request = urllib.request.Request(API + path + "?" + query, headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + TOKEN,
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "profile-all-branches-calendar",
        })
        for attempt in range(4):
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    batch = json.load(response)
                break
            except urllib.error.HTTPError as error:
                if error.code in (429, 500, 502, 503, 504) and attempt < 3:
                    time.sleep(2 ** (attempt + 1))
                    continue
                raise
        yield from batch
        if len(batch) < 100:
            return
        page += 1


def collect():
    # Public owned repos, including forks. Add explicit public collaborator
    # repositories through EXTRA_REPOSITORIES, separated by commas.
    repos = {r["full_name"]: r for r in pages(
        "/users/" + USER + "/repos", type="owner")}
    for name in os.getenv("EXTRA_REPOSITORIES", "").split(","):
        if name.strip():
            repos.setdefault(name.strip(), {"full_name": name.strip(), "size": 1})
    seen = set()
    counts = collections.Counter()
    scanned = 0
    for name, repo in sorted(repos.items()):
        if repo.get("size") == 0:
            continue
        print("Scanning " + name, flush=True)
        for branch in pages("/repos/" + name + "/branches"):
            for commit in pages("/repos/" + name + "/commits",
                                sha=branch["name"], author=USER,
                                since=START.isoformat() + "T00:00:00Z"):
                sha = commit["sha"]
                author = commit.get("author") or {}
                if author.get("login", "").lower() != USER.lower() or sha in seen:
                    continue
                day = dt.datetime.fromisoformat(
                    commit["commit"]["author"]["date"].replace("Z", "+00:00")
                ).astimezone(dt.timezone.utc).date()
                if START <= day <= TODAY:
                    seen.add(sha)
                    counts[day] += 1
        scanned += 1
    return counts, scanned


def render(counts, scanned):
    total = sum(counts.values())
    peak = max(counts.values(), default=1) or 1
    beginning = START - dt.timedelta(days=(START.weekday() + 1) % 7)
    colors = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="250" viewBox="0 0 900 250" role="img">',
        '<title>All-branch commit activity for ' + html.escape(USER) + '</title>',
        '<rect width="900" height="250" rx="14" fill="#0d1117"/>',
        '<g font-family="Arial,sans-serif" fill="#e6edf3">',
        '<text x="26" y="34" font-size="20" font-weight="bold">Activity across all branches</text>',
        f'<text x="26" y="60" font-size="14">{total:,} unique commits · {scanned} public repositories · last 365 days</text>',
    ]
    for offset in range((TODAY - beginning).days + 1):
        day = beginning + dt.timedelta(days=offset)
        if day < START:
            continue
        value = counts.get(day, 0)
        level = 0 if not value else min(4, 1 + int(3 * value / peak))
        x, y = 55 + (offset // 7) * 15, 88 + (offset % 7) * 15
        svg.append(f'<rect x="{x}" y="{y}" width="11" height="11" rx="2" fill="{colors[level]}"><title>{day}: {value} commits</title></rect>')
    for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        svg.append(f'<text x="22" y="{97 + row * 15}" font-size="10" fill="#9198a1">{label}</text>')
    svg.extend([
        f'<text x="26" y="216" font-size="12" fill="#9198a1">Author dates in UTC · identical SHAs counted once · updated {TODAY}</text>',
        '<text x="26" y="236" font-size="11" fill="#9198a1">Public owned repositories + configured extras. Only commits reachable from existing branches.</text>',
        '</g></svg>',
    ])
    return "\n".join(svg)


if __name__ == "__main__":
    counts, scanned = collect()  # Fail without replacing the image on API errors.
    target = pathlib.Path("assets/activity.svg")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render(counts, scanned), encoding="utf-8")
