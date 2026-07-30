#!/usr/bin/env python3
"""Re-check every claim this profile makes, then write the result to disk.

A README is a set of assertions about the world: these links resolve, these
demos are up, these repos exist. Assertions rot. This script tests them and
records the outcome so the badge on the profile reflects reality rather than
whatever was true the day it was written.

Writes data/status.json. Exits non-zero if any check fails, so a rotted link
surfaces as a failed CI run instead of quietly sitting on the profile.
"""

import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
OUT = ROOT / "data" / "status.json"

USER = "agarwaladarshcoding-maker"
UA = "Mozilla/5.0 (compatible; profile-self-verify/1.0; +github.com/%s)" % USER
TIMEOUT = 20

# Live deployments the README points at. Checked separately from plain links
# because these being down is a real failure, not a dead bookmark.
DEMOS = [
    ("portfolio", "https://know-about-adarsh.vercel.app"),
    # The Medical RAG demo front end is deployed at medical-rag-demo.vercel.app
    # but its /api/ask returns 503 until CHAT_API_KEY is set on that Vercel
    # project. Uncomment once the key is in place — checking the front page
    # alone would be a green tick for a broken demo, which defeats the point.
    # ("medical-rag /api/ask", "https://medical-rag-demo.vercel.app/api/ask"),
]

# Repos the README claims exist and are public.
PINNED = [
    "Advanced-Medical-Based-RAG-System",
    "AgentWatcher",
    "Amber-Student-Chatbot",
    "Algorithmic_Portfolio_Manager",
    "High-Frequency-Order-Book",
    "Monte-Carlo-Project-Simulator",
]

# Hosts that answer automated requests with a refusal rather than the page, as
# bot defence. Reaching them at all proves the host resolves and the path is
# shaped right; the status code carries no signal about the link being good.
# 429 shows up specifically from CI: GitHub's runner IPs are shared and already
# rate-limited by LinkedIn before this workflow ever gets there.
BOT_WALLED = ("codeforces.com", "linkedin.com", "x.com", "twitter.com",
              "medium.com")
WALL_CODES = (401, 403, 405, 429, 999)

# Notebooks are ~95% JSON scaffolding around Python. Counting them as their
# own language wildly overstates them, so fold them in.
LANG_MERGE = {"Jupyter Notebook": "Python"}
LANG_SKIP = {"CSS", "HTML", "SCSS", "Makefile", "Dockerfile", "Batchfile",
             "Shell", "CMake", "Objective-C", "Swift", "Kotlin", "Ruby"}


def fetch(url, method="GET", token=None):
    req = urllib.request.Request(url, method=method)
    req.add_header("User-Agent", UA)
    req.add_header("Accept", "*/*")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    return urllib.request.urlopen(req, timeout=TIMEOUT)


def check_url(url):
    """Return (ok, detail). HEAD first, fall back to GET on 4xx/405."""
    host = urllib.parse.urlparse(url).netloc.lower()
    walled = any(h in host for h in BOT_WALLED)
    for method in ("HEAD", "GET"):
        try:
            r = fetch(url, method=method)
            return True, str(r.status)
        except urllib.error.HTTPError as e:
            if walled and e.code in WALL_CODES:
                return True, f"{e.code} (bot-walled, host reachable)"
            if e.code == 405 and method == "HEAD":
                continue                     # server rejects HEAD, try GET
            if method == "GET":
                return False, f"HTTP {e.code}"
        except Exception as e:                       # DNS, TLS, timeout
            if method == "GET":
                return False, type(e).__name__
    return False, "unreachable"


def readme_links():
    if not README.exists():
        return []
    text = README.read_text()
    urls = set(re.findall(r"\]\((https?://[^\s)]+)\)", text))
    urls |= set(re.findall(r'(?:href|src)="(https?://[^"]+)"', text))
    # shields/camo badge images and our own asset paths carry no claim
    return sorted(u for u in urls if "img.shields.io" not in u)


def languages(token):
    """Byte-weighted language mix across public, non-fork repos."""
    agg = {}
    try:
        page = 1
        while True:
            r = fetch(f"https://api.github.com/users/{USER}/repos"
                      f"?per_page=100&type=owner&page={page}", token=token)
            repos = json.loads(r.read())
            if not repos:
                break
            for repo in repos:
                if repo.get("fork") or repo.get("private"):
                    continue
                try:
                    lr = fetch(repo["languages_url"], token=token)
                    for lang, size in json.loads(lr.read()).items():
                        lang = LANG_MERGE.get(lang, lang)
                        if lang in LANG_SKIP:
                            continue
                        agg[lang] = agg.get(lang, 0) + size
                except Exception:
                    continue
            if len(repos) < 100:
                break
            page += 1
    except Exception as e:
        print(f"  ! language collection failed: {e}", file=sys.stderr)
        return []
    total = sum(agg.values()) or 1
    return [{"name": k, "pct": round(100 * v / total, 1)}
            for k, v in sorted(agg.items(), key=lambda kv: -kv[1])[:7]]


def main():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    groups, failures = [], []

    def run(name, items):
        passed = 0
        print(f"\n{name}:")
        for label, fn in items:
            ok, detail = fn()
            print(f"  {'PASS' if ok else 'FAIL'}  {label}  ({detail})")
            if ok:
                passed += 1
            else:
                failures.append(f"{name}: {label} — {detail}")
        groups.append({"name": name, "passed": passed, "total": len(items)})

    links = readme_links()
    run("links", [(u, (lambda u=u: check_url(u))) for u in links])
    run("demos", [(n, (lambda u=u: check_url(u))) for n, u in DEMOS])

    def repo_public(name):
        def go():
            try:
                r = fetch(f"https://api.github.com/repos/{USER}/{name}",
                          token=token)
                d = json.loads(r.read())
                if d.get("private"):
                    return False, "private"
                if d.get("archived"):
                    return False, "archived"
                return True, "public"
            except urllib.error.HTTPError as e:
                return False, f"HTTP {e.code}"
            except Exception as e:
                return False, type(e).__name__
        return go

    run("repos", [(n, repo_public(n)) for n in PINNED])

    passed = sum(g["passed"] for g in groups)
    total = sum(g["total"] for g in groups)
    status = {
        "ok": not failures,
        "checks": {"passed": passed, "total": total},
        "groups": groups,
        "failures": failures,
        "generated": datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC"),
        "languages": languages(token),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(status, indent=2) + "\n")

    print(f"\n{'─'*58}\n{passed}/{total} checks passing")
    if failures:
        print("\nfailures:")
        for f in failures:
            print(f"  · {f}")
        sys.exit(1)


if __name__ == "__main__":
    main()
