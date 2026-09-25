"""Live verification of the GitHub profile stats auto-update system.

Run:  python verify-live.py     (exits 0 when every check passes)

Proves that github.com really serves the locally generated stats, and that
the numbers on the card track GitHub's own contribution calendar - so the
data is fetched, never hard-coded.
"""
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

USER = "siddharthkumarrai"
REPO = USER + "/" + USER
API_HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/vnd.github+json"}
PASSED, FAILED = [], []


def check(ok, label):
    (PASSED if ok else FAILED).append(label)


def get(url, headers=None):
    request = urllib.request.Request(url, headers=headers or {"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", "replace"), dict(response.headers)


# --- 1. the profile serves the local card, not the external service ------
html, _ = get("https://github.com/" + USER)
check("raw/main/assets/github-streak.svg" in html, "profile renders ./assets/github-streak.svg")
check("streak-stats.demolab.com" not in html, "profile no longer loads streak-stats.demolab.com")
check(html.count("raw/main/profile-summary-card-output") == 4,
      "profile renders all 4 local summary cards")

# --- 2. remote SVG is valid, non-empty and shows three stats -------------
raw, headers = get("https://raw.githubusercontent.com/%s/main/assets/github-streak.svg" % REPO)
try:
    check(ET.fromstring(raw).tag.endswith("svg"), "remote SVG parses as XML")
except ET.ParseError as exc:
    check(False, "remote SVG parses as XML (%s)" % exc)
check(len(raw) > 400, "remote SVG is non-empty (%d bytes)" % len(raw))
numbers = re.findall(r">([0-9][0-9,]*)</text>", raw)
check(len(numbers) == 3, "remote SVG shows 3 stat numbers: %s" % numbers)
cache = headers.get("Cache-Control", "")
check("max-age=300" in cache, "raw CDN cache is 5 minutes, not 24 (%s)" % cache)

# --- 3. cross-check the total against GitHub's own calendar --------------
# This is what proves the numbers are fetched from GitHub, not baked in.
cal, _ = get("https://github.com/users/%s/contributions" % USER)
live = 0
for match in re.finditer(r"<tool-tip\b([^>]*)>(.*?)</tool-tip>", cal, re.S):
    text = re.sub(r"<[^>]+>", "", match.group(2)).strip()
    hit = re.match(r"(\d+)\s+contribution", text)
    if hit:
        live += int(hit.group(1))
svg_total = int(numbers[-1].replace(",", "")) if numbers else 0
check(svg_total > 0, "SVG total is a real value, not a placeholder: %d" % svg_total)
check(abs(svg_total - live) <= 100,
      "SVG total tracks GitHub's live calendar: svg=%d live=%d delta=%d"
      % (svg_total, live, abs(svg_total - live)))

# --- 4. workflows are registered and active ------------------------------
wfs = json.loads(get("https://api.github.com/repos/%s/actions/workflows" % REPO, API_HEADERS)[0])
states = {w["path"]: w["state"] for w in wfs["workflows"]}
check(states.get(".github/workflows/update-stats.yml") == "active",
      "workflow 'Update GitHub stats' is active")
check(states.get(".github/workflows/profile-cards.yml") == "active",
      "workflow 'GitHub-Profile-Summary-Cards' is active")

# --- 5. the refresh workflow actually runs and succeeds -------------------
runs = json.loads(get("https://api.github.com/repos/%s/actions/runs?per_page=15" % REPO,
                      API_HEADERS)[0])["workflow_runs"]
stats_runs = [r for r in runs if str(r.get("path", "")).endswith("update-stats.yml")]
check(bool(stats_runs), "update-stats has executed at least once")
done = [r for r in stats_runs if r["status"] == "completed"]
check(bool(done) and all(r["conclusion"] == "success" for r in done[:3]),
      "latest completed update-stats runs are green: %s"
      % [r["conclusion"] for r in done[:3]])
events = sorted({r["event"] for r in stats_runs})
check(bool(events), "runs observed from events: %s" % events)

# --- 6. main is reachable and current ------------------------------------
head = json.loads(get("https://api.github.com/repos/%s/commits/main" % REPO, API_HEADERS)[0])
check(bool(head.get("sha")), "main HEAD reachable: %s %s"
      % (head["sha"][:7], head["commit"]["message"].splitlines()[0][:52]))

for msg in PASSED:
    print("  PASS  " + msg)
for msg in FAILED:
    print("  FAIL  " + msg)
print("\n%d passed, %d failed" % (len(PASSED), len(FAILED)))
sys.exit(1 if FAILED else 0)
