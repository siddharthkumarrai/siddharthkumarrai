"""Static validation of the GitHub profile stats auto-update system.

Run:  python validate.py        (exits 0 when every check passes)

Checks the workflow definitions, README wiring, generated assets, loop
prevention and secret hygiene without needing network access.
"""
import importlib.util
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is required:  python -m pip install pyyaml")

ROOT = Path(__file__).resolve().parent
PASSED, FAILED = [], []


def check(ok, label):
    (PASSED if ok else FAILED).append(label)


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


# --- workflows parse ----------------------------------------------------
wf_stats = yaml.safe_load(read(".github/workflows/update-stats.yml"))
wf_cards = yaml.safe_load(read(".github/workflows/profile-cards.yml"))
check(isinstance(wf_stats, dict), "update-stats.yml is valid YAML")
check(isinstance(wf_cards, dict), "profile-cards.yml is valid YAML")

# PyYAML reads a bare `on:` key as boolean True (YAML 1.1 quirk)
trig_stats = wf_stats.get("on", wf_stats.get(True))
trig_cards = wf_cards.get("on", wf_cards.get(True))
check(isinstance(trig_stats, dict), "update-stats.yml has an `on` block")

# --- triggers: manual + schedule + safe push ----------------------------
check("workflow_dispatch" in trig_stats, "workflow_dispatch present (manual refresh)")
check("schedule" in trig_stats, "schedule present (automatic refresh)")
cron = trig_stats["schedule"][0]["cron"].split()
check(len(cron) == 5, "cron has 5 fields: %s" % trig_stats["schedule"][0]["cron"])
check(trig_stats["push"]["branches"] == ["main"], "push trigger limited to branch main")
check(trig_cards["push"]["paths"] == [".github/workflows/profile-cards.yml"],
      "profile-cards push trigger is self-referential only")

# --- permissions: minimal, job-scoped -----------------------------------
job = wf_stats["jobs"][next(iter(wf_stats["jobs"]))]
check(job.get("permissions") == {"contents": "write"},
      "minimal permissions: contents: write (job-scoped)")
check(bool(job.get("timeout-minutes")), "job declares timeout-minutes")

# --- loop prevention -----------------------------------------------------
paths = trig_stats["push"]["paths"]
check("assets/github-streak.svg" not in paths,
      "LOOP-SAFE: generated SVG is not a push-trigger path")
check(all(p.endswith((".yml", ".py")) or p == "README.md" for p in paths),
      "push triggers are source-only: %s" % paths)

# --- race safety: one shared writer group -------------------------------
check(wf_stats.get("concurrency", {}).get("group") == wf_cards.get("concurrency", {}).get("group"),
      "both push workflows share one concurrency group (no push race)")
check(bool(wf_cards["jobs"]["build"]["steps"][0].get("with", {}).get("ref")),
      "profile-cards checks out the branch tip, not the stale event SHA")


# --- generation + conditional commit ------------------------------------
steps = job["steps"]
gen = next((s for s in steps if "generate_streak" in str(s.get("run", ""))), None)
check(gen is not None, "workflow runs tools/generate_streak.py")
gen_env = (gen or {}).get("env", {})
check("GITHUB_TOKEN" in gen_env and "GITHUB_USERNAME" in gen_env,
      "generator receives token/username via env only")

commit = next((s for s in steps if "git commit" in str(s.get("run", ""))), None)
run = str((commit or {}).get("run", ""))
check("git diff --cached --quiet" in run, "commits ONLY when the staged SVG changed")
check("git pull --rebase" in run, "rebase before push (survives concurrent pushes)")
check('git push origin "HEAD:$GITHUB_REF_NAME"' in run, "pushes to the triggering branch")
check("github-actions[bot]" in run, "generated commits use the Actions bot identity")

# --- secret hygiene ------------------------------------------------------
secret_re = re.compile(r"\bghp_[A-Za-z0-9]{20,}|\bgho_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}")
for rel in ["README.md", ".github/workflows/update-stats.yml",
            ".github/workflows/profile-cards.yml", "tools/generate_streak.py"]:
    check(not secret_re.search(read(rel)), "no token-like string in %s" % rel)
check("echo $GITHUB_TOKEN" not in run, "token is never echoed to the logs")

# --- README wiring -------------------------------------------------------
readme = read("README.md")
check('src="./assets/github-streak.svg"' in readme, "README uses the local streak SVG")
check("streak-stats.demolab.com" not in readme, "no stale streak-stats.demolab.com URL")
check("github-readme-stats" not in readme, "no stale github-readme-stats URL")

spec = importlib.util.spec_from_file_location("build_readme", ROOT / "tools" / "build_readme.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
check(mod.P1 + mod.P2 + mod.P3 + mod.P4 + mod.P5 == readme,
      "README.md matches tools/build_readme.py output (no hand edits)")

for src in sorted(set(re.findall(r'src="\./([^"]+)"', readme))):
    check((ROOT / src).is_file(), "local image exists: ./%s" % src)


# --- generated assets ----------------------------------------------------
svg = ROOT / "assets" / "github-streak.svg"
check(svg.is_file() and svg.stat().st_size > 0, "assets/github-streak.svg exists and is non-empty")
if svg.is_file():
    try:
        node = ET.parse(svg).getroot()
        check(node.tag.endswith("svg"), "streak SVG parses as XML <svg>")
        check(bool(node.get("width")) and bool(node.get("height")), "streak SVG declares width/height")
    except ET.ParseError as exc:
        check(False, "streak SVG parses as XML (%s)" % exc)

for name in ("0-profile-details", "1-repos-per-language", "2-most-commit-language",
             "3-stats", "4-productive-time"):
    card = ROOT / "profile-summary-card-output" / "tokyonight" / (name + ".svg")
    check(card.is_file() and card.stat().st_size > 0, "summary card present: %s.svg" % name)

# --- data comes from GitHub, never baked into the source -----------------
gen_src = read("tools/generate_streak.py")
check("api.github.com/graphql" in gen_src, "generator queries the GitHub GraphQL API")
check("/contributions" in gen_src, "generator has a tokenless public-calendar fallback")
check("https://api.github.com/graphql" in gen_src and "urlopen" in gen_src,
      "generator reads live data over HTTPS")
check("text=auto eol=lf" in read(".gitattributes"), "line endings normalised via .gitattributes")

# --- report --------------------------------------------------------------
for msg in PASSED:
    print("  PASS  " + msg)
for msg in FAILED:
    print("  FAIL  " + msg)
print("\n%d passed, %d failed" % (len(PASSED), len(FAILED)))
sys.exit(1 if FAILED else 0)


