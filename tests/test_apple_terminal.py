import argparse
import io
import os
import subprocess
import unittest
from unittest.mock import patch

import kiwi_pet as pet


class AppleTerminalTests(unittest.TestCase):
    def test_detection_and_override(self):
        with patch.dict(os.environ, TERM_PROGRAM='Apple_Terminal'):
            self.assertEqual(pet.resolve_renderer(), 'apple-font')
            self.assertEqual(pet.resolve_renderer('half-block'), 'half-block')
        with patch.dict(os.environ, TERM_PROGRAM='another-terminal'):
            self.assertEqual(pet.resolve_renderer(), 'half-block')

    def test_font_is_halved_and_restored_on_normal_exit_and_interrupt(self):
        for interrupted in (False, True):
            with patch.object(pet.os, 'ttyname', return_value='/dev/ttys001'), patch.object(pet, 'terminal_font', side_effect=[14, 7, 14]) as font:
                try:
                    with pet.apple_pixel_scale():
                        self.assertEqual(font.call_args.args, ('/dev/ttys001', 7))
                        if interrupted:
                            raise KeyboardInterrupt
                except KeyboardInterrupt:
                    pass
                self.assertEqual([c.args for c in font.call_args_list], [('/dev/ttys001',), ('/dev/ttys001', 7), ('/dev/ttys001', 14)])

    def test_failed_font_change_still_restores_original(self):
        with patch.object(pet.os, 'ttyname', return_value='/dev/ttys001'), patch.object(pet, 'terminal_font', side_effect=[14, subprocess.CalledProcessError(1, 'osascript'), 14]) as font:
            with self.assertRaises((SystemExit, subprocess.CalledProcessError)):
                with pet.apple_pixel_scale():
                    self.fail('Must not run after a failed font change')
            self.assertEqual(font.call_args.args, ('/dev/ttys001', 14))

    def test_permission_failure_does_not_change_artwork_or_font(self):
        with patch.object(pet.os, 'ttyname', return_value='/dev/ttys001'), patch.object(pet, 'terminal_font', side_effect=subprocess.CalledProcessError(1, 'osascript')) as font:
            with self.assertRaises(SystemExit):
                with pet.apple_pixel_scale():
                    self.fail('Must not silently fall back to reduced artwork')
            self.assertEqual(font.call_count, 1)

    def test_apple_compact_runs_the_original_renderer(self):
        class Terminal(io.StringIO):
            def isatty(self):
                return True
        for pet_only in (False, True):
            args = ['kiwi_pet.py', '--pixel-size', '1'] + (['--pet'] if pet_only else [])
            with patch.dict(os.environ, TERM_PROGRAM='Apple_Terminal'), patch.object(pet.sys, 'argv', args), patch.object(pet.sys, 'stdin', Terminal()), patch.object(pet.sys, 'stdout', Terminal()), patch.object(pet, 'apple_pixel_scale') as scale, patch.object(pet, 'run') as run:
                pet.main()
                scale.assert_called_once()
                self.assertEqual(run.call_args.args[0].pixel_size, 2)
                self.assertEqual(run.call_args.args[1], 'half-block')

    def test_original_size_does_not_touch_font(self):
        with patch.dict(os.environ, TERM_PROGRAM='Apple_Terminal'), patch.object(pet.sys, 'argv', ['kiwi_pet.py', '--pet', '--pixel-size', '2']), patch.object(pet, 'apple_pixel_scale') as scale, patch.object(pet, 'run'):
            pet.main()
            scale.assert_not_called()


if __name__ == '__main__':
    unittest.main()
