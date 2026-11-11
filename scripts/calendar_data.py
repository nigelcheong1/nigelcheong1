"""Fetch and validate GitHub's contribution calendar; never synthesize activity."""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
import json
import math
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class ContributionDay:
    day: date
    count: int
    level: int


@dataclass
class Calendar:
    username: str
    start: date
    end: date
    days: dict[tuple[int, int], ContributionDay]
    weeks: int
    total: int


def fetch_calendar(username: str, token: str, now: datetime | None = None) -> tuple[dict, date, date]:
    if not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?', username):
        raise ValueError('Invalid GitHub username')
    if not token:
        raise ValueError('Set GH_TOKEN or GITHUB_TOKEN to fetch contribution data')
    now = now or datetime.now(timezone.utc)
    end = now.date()
    start = end - timedelta(days=364)
    query = '''query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            totalContributions
            weeks { contributionDays { date weekday contributionCount contributionLevel } }
          }
        }
      }
    }'''
    variables = {
        'login': username,
        'from': datetime.combine(start, time.min, timezone.utc).isoformat(),
        'to': now.isoformat(),
    }
    request = Request('https://api.github.com/graphql',
        data=json.dumps({'query': query, 'variables': variables}).encode(),
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json',
                 'User-Agent': 'github-contribution-workshop', 'Accept': 'application/vnd.github+json'})
    try:
        with urlopen(request, timeout=45) as result:
            payload = json.load(result)
    except HTTPError as error:
        raise RuntimeError(f'GitHub calendar request failed (HTTP {error.code})') from None
    except URLError:
        raise RuntimeError('Unable to reach the GitHub contribution API') from None
    return payload, start, end


def normalize_calendar(payload: dict, username: str, start: date, end: date) -> Calendar:
    """Align actual dates to Sunday-first columns, keeping partial weeks honest."""
    if payload.get('errors'):
        raise ValueError('GitHub returned a GraphQL error; previous calendar was preserved')
    if not 1 <= (end-start).days+1 <= 366:
        raise ValueError('Calendar must contain between 1 and 366 days')
    try:
        graph = payload['data']['user']['contributionsCollection']['contributionCalendar']
        weeks = graph['weeks']
        levels = {'NONE': 0, 'FIRST_QUARTILE': 1, 'SECOND_QUARTILE': 2,
                  'THIRD_QUARTILE': 3, 'FOURTH_QUARTILE': 4}
        prefix = (start.weekday()+1) % 7
        origin = start - timedelta(days=prefix)
        days = {}
        seen = set()
        for week in weeks:
            for item in week['contributionDays']:
                day = date.fromisoformat(item['date'])
                if day in seen:
                    raise ValueError('Duplicate contribution date')
                seen.add(day)
                count = item['contributionCount']
                if type(count) is not int or not 0 <= count <= 2**31-1:
                    raise ValueError('Invalid contribution count')
                if item['weekday'] != (day.weekday()+1) % 7:
                    raise ValueError('Contribution weekday does not match its date')
                level = levels[item['contributionLevel']]
                if (count == 0) != (level == 0):
                    raise ValueError('Contribution level does not match its count')
                if start <= day <= end:
                    offset = (day-origin).days
                    days[offset//7, offset%7] = ContributionDay(day, count, level)
        expected = {start+timedelta(days=i) for i in range((end-start).days+1)}
        if {item.day for item in days.values()} != expected:
            raise ValueError('GitHub calendar is missing dates; previous calendar was preserved')
        return Calendar(username, start, end, days,
                        (prefix+(end-start).days+1+6)//7,
                        sum(item.count for item in days.values()))
    except (KeyError, TypeError, AttributeError) as error:
        raise ValueError('Invalid GitHub calendar response') from None


def column_height(count: int, maximum: int) -> float:
    """Log-scaled height preserves order without letting one busy day hide a week."""
    return 0 if count <= 0 else 7 + 41*math.log1p(count)/math.log1p(max(maximum, count))


def placement_targets(calendar: Calendar) -> list[tuple[int, int]]:
    """Pick at most one genuine active day per quarter for the robot's stops."""
    groups = [[] for _ in range(4)]
    for position, day in calendar.days.items():
        if day.count:
            groups[min(3, position[0]*4//calendar.weeks)].append(position)
    return sorted(max(group, key=lambda pos: (calendar.days[pos].count, -abs(pos[1]-4)))
                  for group in groups if group)
