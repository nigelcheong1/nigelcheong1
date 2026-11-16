import unittest
from datetime import date, timedelta
import xml.etree.ElementTree as ET

from scripts.calendar_data import normalize_calendar
from scripts.generate_pixel_profile import render_calendar, frame_card, refresh_statistics
from tests.test_calendar_data import response


class PixelProfileTests(unittest.TestCase):
    def calendar(self, counts=None):
        start = date(2025, 12, 28)
        return normalize_calendar(response(start, 10, counts), 'nigelcheong1', start, start + timedelta(days=9))

    def test_real_dates_and_counts_survive_desktop_and_phone_rendering(self):
        cal = self.calendar({0: 1, 4: 17, 9: 3})
        expected = {item.day.isoformat(): str(item.count) for item in cal.days.values()}
        for mobile in (False, True):
            root = ET.fromstring(render_calendar(cal, mobile=mobile))
            actual = {node.attrib['data-date']: node.attrib['data-count']
                      for node in root.iter() if 'data-date' in node.attrib}
            self.assertEqual(actual, expected)
            self.assertIn('21 CONTRIBUTIONS', root.find('{http://www.w3.org/2000/svg}title').text)

    def test_empty_activity_stays_flat_and_static_has_no_animation(self):
        root = ET.fromstring(render_calendar(self.calendar(), animated=False))
        cells = [node for node in root.iter() if 'data-date' in node.attrib]
        self.assertEqual(len(cells), 10)
        self.assertTrue(all(node.attrib['fill'] == '#e4ece5' for node in cells))
        self.assertNotIn('@keyframes', ET.tostring(root, encoding='unicode'))

    def test_matching_card_frames_preserve_source_proportions(self):
        ns = '{http://www.w3.org/2000/svg}'
        for w, h in [(467, 195), (300, 165)]:
            source = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}"><text>Existing data</text></svg>'
            root = ET.fromstring(frame_card(source, 'Statistics', canvas=(491, 219)))
            self.assertEqual(root.attrib['viewBox'], '0 0 491 219')
            image = root.find(ns + 'image')
            self.assertAlmostEqual(float(image.attrib['width']) / float(image.attrib['height']), w / h)
            self.assertGreaterEqual(float(image.attrib['x']), 12)
            self.assertEqual(float(image.attrib['y']), 12)

    def test_cached_cards_are_fully_visible_without_an_entrance_animation(self):
        source = '<svg xmlns="http://www.w3.org/2000/svg" width="467" height="195"><style>.stagger{opacity:0}</style><text class="stagger">210</text><circle class="rank-circle"/></svg>'
        result = frame_card(source, 'GitHub statistics')
        root = ET.fromstring(result)
        self.assertEqual(root.attrib['viewBox'], '0 0 491.0 219.0')
        import base64, re
        inner = base64.b64decode(re.search(r'base64,([^\"]+)', result).group(1)).decode()
        self.assertIn('.stagger{opacity:1!important}', inner)
        self.assertIn('animation:none!important', inner)

    def test_card_error_pages_and_unsafe_dimensions_are_rejected(self):
        for source in ['<html>Service unavailable</html>', '<svg width="0" height="165"/>', '<svg width="NaN" height="165"/>']:
            with self.assertRaises(ValueError):
                frame_card(source, 'Statistics')

    def test_rank_arc_tracks_each_source_cards_actual_final_value(self):
        import base64, re
        for offset in ('137.5', '211.25'):
            source = '<svg width="467" height="195"><style>@keyframes rankAnimation{from{stroke-dashoffset:251.3}to{stroke-dashoffset:' + offset + '}}</style><circle class="rank-circle"/></svg>'
            result = frame_card(source, 'Statistics')
            inner = base64.b64decode(re.search(r'base64,([^\"]+)', result).group(1)).decode()
            self.assertIn('.rank-circle{stroke-dashoffset:' + offset + '}', inner)

    def test_service_error_svg_cannot_replace_successful_cached_statistics(self):
        from pathlib import Path
        import tempfile
        from unittest.mock import MagicMock, patch
        error = b'<svg width="467" height="195"><text>Could not fetch total commits.</text></svg>'
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            for name in ('github-stats.svg', 'github-languages.svg'):
                (folder / name).write_text('last successful card')
            mocked = MagicMock()
            mocked.__enter__.return_value.read.return_value = error
            with patch('scripts.generate_pixel_profile.urlopen', return_value=mocked):
                refresh_statistics('nigelcheong1', folder)
            for name in ('github-stats.svg', 'github-languages.svg'):
                self.assertEqual((folder / name).read_text(), 'last successful card')


if __name__ == '__main__':
    unittest.main()
