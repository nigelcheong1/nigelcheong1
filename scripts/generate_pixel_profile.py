"""Refresh the approved pixel contribution calendar and circular analytics."""
import argparse
import base64
from datetime import date
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

if __package__:
    from .calendar_data import fetch_calendar, normalize_calendar
    from .pixel_art import render_calendar, svg
else:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from scripts.calendar_data import fetch_calendar, normalize_calendar
    from scripts.pixel_art import render_calendar, svg

ASSETS = Path(__file__).resolve().parents[1] / 'assets'
CARDS = [('github-stats.svg', 'pixel-stats.svg', 'GitHub statistics and rank'),
         ('github-languages.svg', 'pixel-languages.svg', 'Repository languages'),
         ('streak.svg', 'pixel-streak.svg', 'GitHub contribution streaks')]


def frame_card(source: str, title: str) -> str:
    """Reuse the original cards, fully visible even when nested SVGs do not animate."""
    try:
        root = ET.fromstring(source)
        if root.tag.rsplit('}', 1)[-1] != 'svg':
            raise ValueError('Expected an SVG statistics card')
        for node in root.iter():
            if node.tag.rsplit('}', 1)[-1] in ('script', 'foreignObject'):
                raise ValueError('Unsupported active SVG content')
            for key, value in node.attrib.items():
                if key.lower().startswith('on') or (key.rsplit('}', 1)[-1] == 'href' and not value.startswith('#')):
                    raise ValueError('Unsupported SVG external reference')
        if re.search(r'@import|url\(\s*[\"\x27]?(?:https?:|//)', source, re.I):
            raise ValueError('Unsupported SVG external stylesheet')
        viewbox = root.attrib.get('viewBox', '').split()
        def dimension(key, index):
            value = root.attrib.get(key, '')
            if not re.fullmatch(r'[\d.]+', value):
                value = viewbox[index] if len(viewbox) == 4 else ''
            result = float(value)
            if not math.isfinite(result) or not 0 < result <= 4096:
                raise ValueError('Invalid statistics card dimensions')
            return result
        w, h = dimension('width', 2), dimension('height', 3)
    except (ET.ParseError, TypeError, IndexError) as error:
        raise ValueError('Invalid SVG statistics card') from error
    settled = '*{animation:none!important}.stagger{opacity:1!important}.rank-text{transform:translate(-5px,5px)}'
    final_rank = re.search(r'@keyframes\s+rankAnimation\s*\{.*?(?:to|100%)\s*\{[^}]*stroke-dashoffset:\s*([\d.eE+-]+)', source, re.S)
    if final_rank:
        settled += '.rank-circle{stroke-dashoffset:' + final_rank[1] + '}'
    source = (source.replace('</style>', settled + '</style>', 1) if '<style>' in source
              else source.replace('</svg>', '<style>' + settled + '</style></svg>'))
    embedded = 'data:image/svg+xml;base64,' + base64.b64encode(source.encode()).decode()
    body = f'<path d="M6 0H{w+18}V6H{w+24}V{h+18}H{w+18}V{h+24}H6V{h+18}H0V6H6Z" fill="#0d1117" stroke="#456f4e" stroke-width="2"/>'
    body += f'<image x="12" y="12" width="{w}" height="{h}" href="{embedded}"/>'
    return svg(w+24, h+24, title, body)


def write_atomic(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as file:
        temporary = Path(file.name)
        file.write(content)
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def refresh_statistics(username: str, directory: Path):
    """Keep the last successful card if the existing public service is unavailable."""
    common = {'username': username, 'hide_border': 'true', 'disable_animations': 'true', 'title_color': '7ee787',
              'text_color': 'bac5d0', 'bg_color': '0d1117'}
    endpoints = [('api', 'github-stats.svg', {'show_icons': 'true', 'count_private': 'true',
                  'include_all_commits': 'true', 'icon_color': '56d364'}, 'commits'),
                 ('api/top-langs/', 'github-languages.svg', {'layout': 'compact', 'langs_count': '8'}, 'lang-name')]
    for endpoint, name, options, expected in endpoints:
        try:
            request = Request('https://github-stats-extended.vercel.app/' + endpoint + '?' + urlencode(common | options),
                              headers={'User-Agent': 'nigelcheong1-profile'})
            with urlopen(request, timeout=25) as response:
                content = response.read(1_000_001)
            if len(content) > 1_000_000:
                raise ValueError('Statistics response is too large')
            source = content.decode('utf-8')
            frame_card(source, name)
            marker = next((node for node in ET.fromstring(source).iter()
                           if node.attrib.get('data-testid') == expected), None)
            value = ''.join(marker.itertext()).strip() if marker is not None else ''
            if not value or (expected == 'commits' and not re.fullmatch(r'[\d.,kKmMbB]+', value)):
                raise ValueError('Statistics service returned an error card')
            write_atomic(directory / name, source)
        except Exception as error:
            if not (directory / name).is_file():
                raise RuntimeError(f'No successful cached card for {name}') from error
            print(f'Keeping the last successful {name}: {type(error).__name__}', file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--username', default='nigelcheong1')
    parser.add_argument('--input', type=Path, help='Saved response fixture with start, end and response fields')
    parser.add_argument('--output', type=Path, default=ASSETS)
    parser.add_argument('--frames-only', action='store_true')
    parser.add_argument('--refresh-stats', action='store_true')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?', args.username):
        raise ValueError('Invalid GitHub username')
    outputs = {}
    if not args.frames_only:
        if args.input:
            payload = json.loads(args.input.read_text(encoding='utf-8'))
            start, end = date.fromisoformat(payload['start']), date.fromisoformat(payload['end'])
            payload = payload.get('response', payload)
        else:
            payload, start, end = fetch_calendar(args.username, os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN', ''))
        calendar = normalize_calendar(payload, args.username, start, end)
        for mobile in (False, True):
            for animated in (True, False):
                name = 'pixel-calendar' + ('-mobile' if mobile else '') + ('' if animated else '-still') + '.svg'
                outputs[name] = render_calendar(calendar, animated=animated, mobile=mobile)
        print(f'Validated {len(calendar.days)} genuine contribution days ({start} to {end}), total {calendar.total}.')
    if args.refresh_stats:
        refresh_statistics(args.username, args.output)
    for source, destination, title in CARDS:
        outputs[destination] = frame_card((args.output / source).read_text(encoding='utf-8'), title)
    # Validate everything before replacing a displayed asset.
    for content in outputs.values():
        ET.fromstring(content)
    for name, content in outputs.items():
        write_atomic(args.output / name, content)
    print(f'Updated {len(outputs)} pixel profile assets.')


if __name__ == '__main__':
    main()
