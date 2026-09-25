"""Generate the local GitHub streak card used by the profile README.

Writes ``assets/github-streak.svg`` from GitHub contribution data so the
profile no longer depends on a third-party stats service (or its caches).

Data sources, first one that works wins:

1. The official GraphQL ``contributionCalendar`` when ``GITHUB_TOKEN`` or
   ``GH_TOKEN`` is set - the GitHub Actions runner always provides one.
2. The public ``/users/<login>/contributions`` calendar, which needs no
   token. This is what lets the script run on a local machine too.

Run:  python tools/generate_streak.py
Env:  GITHUB_TOKEN | GH_TOKEN   optional API token
      GITHUB_USERNAME           optional login, defaults to this profile
"""
import json
import os
import re
import sys
import urllib.request
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "github-streak.svg"

DEFAULT_USERNAME = "siddharthkumarrai"
USER_AGENT = "siddharthkumarrai-profile-readme-stats"

# Theme mirrors the tokyonight summary cards already used in README.md.
WIDTH, HEIGHT = 490, 140
BG = "#1a1b27"
FONT = "'Segoe UI', Ubuntu, 'Helvetica Neue', Sans-Serif"
COLOR_STREAK = "#f7768e"
COLOR_LONGEST = "#bb9af7"
COLOR_TOTAL = "#7dcfff"
COLOR_LABEL = "#38bdae"
COLOR_DIM = "#565f89"
COLUMNS = (95, 245, 395)

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""


def fetch_graphql(username, token):
    """Return ``([(date, count), ...], total)`` from the official GraphQL API."""
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": username}}).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
            "Accept": "application/vnd.github+json",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if payload.get("errors"):
        raise RuntimeError("; ".join(e.get("message", "error") for e in payload["errors"]))
    user = (payload.get("data") or {}).get("user")
    if not user:
        raise RuntimeError("user not found: " + username)
    calendar = user["contributionsCollection"]["contributionCalendar"]
    days = sorted(
        (date.fromisoformat(day["date"]), int(day["contributionCount"]))
        for week in calendar["weeks"]
        for day in week["contributionDays"]
    )
    return days, int(calendar["totalContributions"])


def fetch_public(username):
    """Return ``([(date, count), ...], total)`` scraped from the public calendar.

    The calendar cells only expose a level (0-4); the exact per-day counts
    live in the paired ``tool-tip`` elements keyed by the cell id.
    """
    request = urllib.request.Request(
        "https://github.com/users/" + username + "/contributions",
        headers={"User-Agent": USER_AGENT, "Accept": "text/html"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        html = response.read().decode("utf-8", "replace")

    cells = {}
    for tag in re.findall(r"<td\b[^>]*>", html):
        if "ContributionCalendar-day" not in tag:
            continue
        cell_id = re.search(r'id="(contribution-day-component-\d+-\d+)"', tag)
        day = re.search(r'data-date="([0-9]{4}-[0-9]{2}-[0-9]{2})"', tag)
        level = re.search(r'data-level="(\d)"', tag)
        if cell_id and day:
            cells[cell_id.group(1)] = (day.group(1), int(level.group(1)) if level else 0)
    if not cells:
        raise RuntimeError("contribution calendar markup not found")

    counts = {}
    for match in re.finditer(r"<tool-tip\b([^>]*)>(.*?)</tool-tip>", html, re.S):
        cell_id = re.search(r'for="(contribution-day-component-\d+-\d+)"', match.group(1))
        if not cell_id:
            continue
        text = re.sub(r"<[^>]+>", "", match.group(2)).strip()
        exact = re.match(r"(\d+)\s+contribution", text)
        counts[cell_id.group(1)] = int(exact.group(1)) if exact else 0

    days = sorted(
        (date.fromisoformat(day_str), counts.get(cell_id, 1 if level else 0))
        for cell_id, (day_str, level) in cells.items()
    )
    return days, sum(count for _, count in days)


def compute_streaks(days):
    """Return current and longest streak facts, following GitHub's own rules.

    The current streak ends today, but if today has no contribution yet it
    falls back to yesterday so the streak is never forced to zero.
    """
    counts = dict(days)
    last_day = max(counts)
    end = last_day if counts.get(last_day, 0) > 0 else last_day - timedelta(days=1)

    current = 0
    cursor = end
    while counts.get(cursor, 0) > 0:
        current += 1
        cursor -= timedelta(days=1)
    current_start = cursor + timedelta(days=1) if current else None

    longest = 0
    longest_start = longest_end = None
    run = 0
    run_start = None
    for day, count in days:
        if count > 0:
            if run == 0:
                run_start = day
            run += 1
            if run > longest:
                longest = run
                longest_start = run_start
                longest_end = day
        else:
            run = 0

    return (
        current,
        current_start,
        end if current else None,
        longest,
        longest_start,
        longest_end,
    )


def format_day(value):
    return "%s %d" % (value.strftime("%b"), value.day)


def format_range(start, end, empty):
    if start is None or end is None:
        return empty
    same_year = start.year == end.year
    left = format_day(start) + ("" if same_year else ", %d" % start.year)
    right = format_day(end) + ("" if same_year else ", %d" % end.year)
    return left + " - " + right


def build_svg(username, total, facts):
    """Render the card.

    The output depends only on the stats - never on a timestamp - so a rerun
    with unchanged data produces byte-identical output and is not committed.
    """
    current, current_start, current_end, longest, longest_start, longest_end = facts
    stats = (
        (str(current), COLOR_STREAK, "Current Streak",
         format_range(current_start, current_end, "no active streak")),
        (str(longest), COLOR_LONGEST, "Longest Streak",
         format_range(longest_start, longest_end, "none yet")),
        ("{:,}".format(total), COLOR_TOTAL, "Total Contributions", "in the last year"),
    )

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
        'viewBox="0 0 %d %d" role="img" aria-label="GitHub streak stats for %s">'
        % (WIDTH, HEIGHT, WIDTH, HEIGHT, username),
        "<title>GitHub streak stats for %s</title>" % username,
        '<rect x="1" y="1" width="%d" height="%d" rx="5" fill="%s" stroke="%s"/>'
        % (WIDTH - 2, HEIGHT - 2, BG, BG),
        '<g font-family="%s" text-anchor="middle">' % FONT,
    ]
    for column, (value, value_color, label, caption) in zip(COLUMNS, stats):
        parts.append(
            '<text x="%d" y="58" font-size="36" font-weight="600" fill="%s">%s</text>'
            % (column, value_color, value)
        )
        parts.append(
            '<text x="%d" y="86" font-size="15" fill="%s">%s</text>'
            % (column, COLOR_LABEL, label)
        )
        parts.append(
            '<text x="%d" y="110" font-size="11" fill="%s">%s</text>'
            % (column, COLOR_DIM, caption)
        )
    parts.append("</g>")
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main() -> int:
    username = (
        os.environ.get("GITHUB_USERNAME")
        or os.environ.get("GITHUB_REPOSITORY_OWNER")
        or DEFAULT_USERNAME
    )
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    days = total = None
    source = "public calendar"
    if token:
        try:
            days, total = fetch_graphql(username, token)
            source = "graphql"
        except Exception as exc:  # noqa: BLE001 - degrade to the public calendar
            print("graphql unavailable (%s); using public calendar" % exc, file=sys.stderr)
    if days is None:
        days, total = fetch_public(username)
    if not days:
        raise RuntimeError("no contribution data returned for " + username)

    facts = compute_streaks(days)
    svg = build_svg(username, total, facts)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(svg)

    print(
        "wrote %s: %d bytes from %s, %d days, streak %d, longest %d, total %s"
        % (
            OUT.relative_to(ROOT).as_posix(),
            len(svg),
            source,
            len(days),
            facts[0],
            facts[3],
            "{:,}".format(total),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


