import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from PIL import Image, ImageChops
from scripts.calendar_data import Calendar, ContributionDay
from scripts.generate_robot_builder import WorkshopRenderer, export_assets


def calendar(active=True):
    start = date(2025, 11, 12)
    origin = start-timedelta(days=(start.weekday()+1)%7)
    days = {}
    for n in range(365):
        day = start+timedelta(days=n)
        offset = (day-origin).days
        count = (n%17+1) if active and n%4==0 else 0
        days[offset//7,offset%7] = ContributionDay(day,count,2 if count else 0)
    return Calendar('nigelcheong1', start, start+timedelta(days=364), days,53,
                    sum(item.count for item in days.values()))


class RobotBuilderTests(unittest.TestCase):
    def test_empty_calendar_renders_without_fake_columns(self):
        renderer=WorkshopRenderer(calendar(False))
        self.assertEqual(renderer.targets, [])
        self.assertEqual(renderer.frame(6).size, (1120,410))

    def test_robot_really_moves_and_completed_calendar_is_visible(self):
        renderer=WorkshopRenderer(calendar())
        early,late=renderer.frame(1),renderer.frame(13.6)
        self.assertIsNotNone(ImageChops.difference(early,late).getbbox())
        self.assertEqual(len(renderer.targets),4)
        self.assertEqual(renderer.frame(0).size,(1120,410))

    def test_saturday_block_lands_on_a_complete_base_and_stays_full_height(self):
        start=date(2025,12,28)
        days={(0,n): ContributionDay(start+timedelta(days=n),100 if n==6 else 0,4 if n==6 else 0)
              for n in range(7)}
        renderer=WorkshopRenderer(Calendar('nigelcheong1',start,start+timedelta(days=6),days,1,100))
        landing=renderer.places[0]+.69
        before,_=renderer.column_state((0,6),landing-.2)
        after,_=renderer.column_state((0,6),landing+.01)
        complete,_=renderer.column_state((0,6),13.6)
        self.assertEqual(before,40)
        self.assertEqual(after,48)
        self.assertEqual(complete,48)

    def test_exported_gif_loops_and_starts_with_a_completed_calendar(self):
        with tempfile.TemporaryDirectory() as tmp:
            gif,png=export_assets(calendar(),Path(tmp),fps=2)
            with Image.open(gif) as image, Image.open(png) as still:
                self.assertGreater(image.n_frames,8)
                self.assertEqual(image.info['loop'],0)
                self.assertEqual(image.size,still.size)
                # Quantization may change colors slightly; both first frame and
                # still must show roughly the same number of green chart pixels.
                def green_pixels(im):
                    return sum(g>r*1.15 and g>b*1.1 for r,g,b in im.convert('RGB').crop((30,80,1090,400)).get_flattened_data())
                self.assertGreater(green_pixels(image),1000)
                self.assertLess(abs(green_pixels(image)-green_pixels(still)),1000)
                duration=0
                for frame in range(image.n_frames):
                    image.seek(frame)
                    duration+=image.info['duration']
                self.assertEqual(duration,16000)


if __name__ == '__main__':
    unittest.main()
