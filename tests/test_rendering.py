"""Decode terminal colors and half blocks back to source pixels at both scales."""
import os
import re
import unittest
from unittest.mock import patch

import kiwi_pet as pet


SGR = re.compile(r'\x1b\[([0-9;]*)m')


def decode(line, screen):
    upper, lower = [], []
    fg = bg = None
    position = 0
    while position < len(line):
        match = SGR.match(line, position)
        if match:
            codes = list(map(int, match[1].split(';')))
            i = 0
            while i < len(codes):
                code = codes[i]
                if code == 0:
                    fg = bg = None
                elif code == 39:
                    fg = None
                elif code == 49:
                    bg = None
                elif code in (38, 48):
                    assert codes[i + 1] == 5
                    if code == 38:
                        fg = codes[i + 2]
                    else:
                        bg = codes[i + 2]
                    i += 2
                elif 30 <= code <= 37 or 90 <= code <= 97:
                    assert screen
                    fg = code + 10
                elif 40 <= code <= 47 or 100 <= code <= 107:
                    assert screen
                    bg = code
                else:
                    raise AssertionError(f'Unexpected SGR {code}')
                i += 1
            position = match.end()
        else:
            glyph = line[position]
            assert glyph in ' ▀▄'
            upper.append(fg if glyph == '▀' else bg)
            lower.append(fg if glyph == '▄' else bg)
            position += 1
    return upper, lower


class RenderingTests(unittest.TestCase):
    def assert_scene(self, rows, design, blink=False):
        width = max(map(len, rows))
        palette = pet.pixel_palette(design)
        expected = [[None if c == ' ' else palette['b' if blink and c == 'e' else c]
                     for c in row.ljust(width)] for row in rows]
        for size in (1, 2):
            rendered = pet.render_rows(rows, blink, design, size, renderer="half-block")
            decoded = []
            for line in rendered:
                upper, lower = decode(line, bool(os.environ.get('STY')))
                self.assertEqual(len(upper), width * size)
                if size == 1:
                    decoded.extend((upper, lower))
                else:
                    self.assertEqual(upper, lower)
                    self.assertEqual(upper[::2], upper[1::2])
                    decoded.append(upper[::2])
            self.assertEqual(decoded[:len(rows)], expected)
            for extra in decoded[len(rows):]:
                self.assertEqual(extra, [None] * width)
            min_width, min_height = pet.scene_dimensions(design, size, "half-block")
            self.assertLessEqual(width * size, min_width)
            self.assertLessEqual(len(rendered) + 1, min_height)

    def test_solid_regions_use_background_spaces(self):
        for screen in ('', 'screen-test'):
            with patch.dict(os.environ, STY=screen):
                for design in pet.DESIGNS:
                    for pixel in pet.pixel_palette(design):
                        rendered = pet.compact_pixels(pixel * 3, pixel * 3, False, design)
                        self.assertEqual(SGR.sub('', rendered), '   ')

    def test_every_color_pair_and_transparency(self):
        for screen in ('', 'screen-test'):
            with patch.dict(os.environ, STY=screen):
                for design in pet.DESIGNS:
                    colors = ' ' + ''.join(pet.pixel_palette(design))
                    # Deliberately include unequal row lengths and odd heights.
                    for upper in colors:
                        for lower in colors:
                            for blink in (False, True):
                                self.assert_scene([upper * 3, lower, 'e'], design, blink)

    def test_all_standalone_animation_phases(self):
        scenes = {
            'round': pet.round_scene, 'bedtime': pet.bedtime_scene,
            'sleep': pet.side_sleep_scene, 'sleep_side': pet.side_sleep_scene,
            'sleep_large': pet.large_sleep_scene, 'coffee': pet.coffee_scene,
            'reading': pet.reading_scene,
            'classic': lambda tick: pet.BODY + list(pet.FEET[tick % 2]),
        }
        for screen in ('', 'screen-test'):
            with patch.dict(os.environ, STY=screen):
                for design, scene in scenes.items():
                    for tick in range(244):
                        self.assert_scene(scene(tick), design, tick % 7 == 0)

    def test_every_daily_event_recovery_and_night_display(self):
        events = {**pet.DAY_LENGTHS, 'terminal': 122, 'semicolon': 122}
        for screen in ('', 'screen-test'):
            with patch.dict(os.environ, STY=screen), patch.dict(pet.DAY_LENGTHS, events):
                for event in events:
                    schedule = pet.DaySchedule(seed=7)
                    for display in pet.NIGTHT_DISPLAYS:
                        schedule.night_displays[0] = display
                        with patch.object(schedule, 'day_at', return_value=(0, (event, event), 0)):
                            for phase in range(events[event]):
                                with patch.object(schedule, 'at', return_value=(event, phase)):
                                    self.assert_scene(pet.emergency_scene(phase, schedule), 'daily', phase % 7 == 0)


if __name__ == '__main__':
    unittest.main()
