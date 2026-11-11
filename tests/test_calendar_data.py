import unittest
from datetime import date, timedelta

from scripts.calendar_data import normalize_calendar, column_height, placement_targets


def response(start=date(2025, 12, 28), length=10, counts=None):
    counts = counts or {}
    days = []
    for offset in range(length):
        day = start + timedelta(days=offset)
        count = counts.get(offset, 0)
        days.append({
            'date': day.isoformat(), 'weekday': (day.weekday() + 1) % 7,
            'contributionCount': count,
            'contributionLevel': 'SECOND_QUARTILE' if count else 'NONE',
        })
    return {'data': {'user': {'contributionsCollection': {'contributionCalendar': {
        'totalContributions': sum(d['contributionCount'] for d in days),
        'weeks': [{'contributionDays': days}],
    }}}}}


class CalendarDataTests(unittest.TestCase):
    def parse(self, payload, start=date(2025, 12, 28), end=date(2026, 1, 6)):
        return normalize_calendar(payload, 'nigelcheong1', start, end)

    def test_calendar_preserves_counts_and_sunday_alignment_across_new_year(self):
        cal = self.parse(response(counts={0: 1, 4: 17, 9: 3}))
        self.assertEqual(cal.total, 21)
        self.assertEqual(cal.days[0, 0].count, 1)
        self.assertEqual(cal.days[0, 4].day, date(2026, 1, 1))
        self.assertEqual(cal.days[0, 4].count, 17)
        self.assertEqual(cal.days[1, 2].count, 3)

    def test_partial_first_week_is_padded_without_inventing_days(self):
        start = date(2026, 1, 1)
        cal = self.parse(response(start, 5), start, date(2026, 1, 5))
        self.assertNotIn((0, 0), cal.days)
        self.assertEqual(cal.days[0, 4].day, start)
        self.assertEqual(cal.days[1, 1].day, date(2026, 1, 5))

    def test_no_activity_never_creates_fake_placement_targets(self):
        cal = self.parse(response())
        self.assertEqual(cal.total, 0)
        self.assertEqual(placement_targets(cal), [])
        self.assertEqual(column_height(0, 0), 0)

    def test_targets_always_correspond_to_real_nonzero_days(self):
        cal = self.parse(response(counts={2: 4, 8: 9}))
        self.assertEqual(set(placement_targets(cal)), {(0, 2), (1, 1)})
        heights = [column_height(n, 100) for n in [0, 1, 5, 20, 100]]
        self.assertEqual(heights[0], 0)
        self.assertTrue(all(a < b for a, b in zip(heights, heights[1:])))
        self.assertLessEqual(heights[-1], 50)

    def test_missing_or_duplicate_dates_are_rejected(self):
        for replacement in [lambda ds: ds[:-1], lambda ds: ds + [ds[0]]]:
            payload = response()
            graph = payload['data']['user']['contributionsCollection']['contributionCalendar']
            graph['weeks'][0]['contributionDays'] = replacement(graph['weeks'][0]['contributionDays'])
            with self.assertRaises(ValueError):
                self.parse(payload)

    def test_graphql_errors_and_invalid_counts_are_rejected(self):
        with self.assertRaises(ValueError):
            self.parse({'errors': [{'message': 'Not authorized'}]})
        for value in [-1, '7', True]:
            payload = response()
            payload['data']['user']['contributionsCollection']['contributionCalendar']['weeks'][0]['contributionDays'][0]['contributionCount'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.parse(payload)

    def test_inconsistent_weekday_is_rejected(self):
        payload = response()
        payload['data']['user']['contributionsCollection']['contributionCalendar']['weeks'][0]['contributionDays'][0]['weekday'] = 3
        with self.assertRaises(ValueError):
            self.parse(payload)


if __name__ == '__main__':
    unittest.main()
