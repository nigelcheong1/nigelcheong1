# Pixel profile updates

The README uses the approved animated pixel header, original research-room artwork and circular GitHub statistics cards. It contains native GitHub markup and self-contained image assets; no page JavaScript or preview controls are published.

`generate_pixel_profile.py` fetches the last 365 days through the existing validated GitHub calendar API and regenerates the displayed desktop/phone SVG calendars and their reduced-motion stills. `pixel_art.py` contains the original authored glyphs and robot geometry. Dates, totals, intensity levels and individual day counts come from the validated response. Missing/invalid API data leaves the displayed calendars unchanged.

The existing daily workflow now runs this generator at 19:37 UTC (03:37 Malaysia time) and on source changes. It refreshes the existing public statistics/language-card sources and adds the approved pixel frames. Service errors retain the last successful cards. The streak workflow refreshes the framed streak card after updating its source. Both workflows share a concurrency group so their commits do not race. They use the existing automatic `GITHUB_TOKEN`; no new secret is needed.

Run locally with Python 3.11+:

```sh
python -m pip install -r scripts/requirements.txt
python -m unittest discover -s tests -v
# Set GH_TOKEN or GITHUB_TOKEN through your normal credential manager.
python scripts/generate_pixel_profile.py --username nigelcheong1 --refresh-stats
# Reframe existing cards without fetching a calendar:
python scripts/generate_pixel_profile.py --frames-only
```

The research scene is original illustrative artwork; the arena and scanner motion are authored SVG effects. Statistics and streaks retain their original source designs. The personal startup, name/role animation and rally are contained in the header image. GitHub may replay an image intro when it reloads; it cannot run a visitor-controlled application inside a README.

## Earlier workshop renderer

The earlier GIF/PNG renderer and its tests remain available for manual regeneration. The profile now displays the pixel SVG calendar instead. The older workflow description below applies only to that archived rendering path.

# Contribution workshop

The robot builds the white-and-green calendar from the last 365 days of actual GitHub contribution data. It places a block on an active day in each quarter with activity, then that column briefly wobbles. All other columns assemble in chronological order. The complete calendar stays visible before the loop restarts.

The GIF begins with the completed calendar so clients that show only the first frame still display the data. The README's `picture` selects a still PNG for browsers requesting reduced motion. The compact image keeps the contribution total, changing build status, and month labels.

## Regeneration

The **Update contribution workshop** Actions workflow runs daily at 19:37 UTC (03:37 in Malaysia). It also runs manually and when its source changes on `main`. GitHub may delay scheduled runs. GitHub can disable scheduled workflows in public repositories after 60 days without repository activity; re-enable the workflow in Actions if that happens.

The workflow uses the automatic `GITHUB_TOKEN`, with repository contents permission to commit the two generated images. It does not need a personal access token or a third-party contribution service. It uses the contribution counts GitHub makes visible to that token and does not collect repository names, commit messages, or private source code.

To regenerate locally with Python 3.11 or later:

```sh
python -m pip install -r scripts/requirements.txt
python -m unittest discover -s tests -v
# Set GH_TOKEN or GITHUB_TOKEN in the environment using your normal credential manager.
python scripts/generate_robot_builder.py --username nigelcheong1
```

The renderer validates calendar dates and nonnegative counts before generating anything. API or validation failures leave the last successful images in place. The height uses a logarithmic scale of the actual count, while the shade follows GitHub's contribution intensity level. Zero-contribution days stay flat; gray boundary tiles fall outside the displayed date range.

Only Pillow is required. Windows uses Segoe UI; Ubuntu uses DejaVu Sans, with Pillow's default font as a fallback. Rendering is deterministic for the same input on the same platform.

Research-room typing, cursor-click and right-console effects are regenerated with `python scripts/animate_research.py`. This composes the immutable original plate using clipped SVG layers, preserves the still versions, and enables motion only with no-preference.
