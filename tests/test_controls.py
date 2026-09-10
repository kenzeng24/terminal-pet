import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import kiwi_pet as pet


class ControlTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.root_patch = patch.object(pet, 'session_root', return_value=root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.env = patch.dict(os.environ)
        self.env.start()
        self.addCleanup(self.env.stop)
        os.environ.pop('KIWI_SESSION', None)

    def test_random_from_first_day_and_no_adjacent_repeats(self):
        openings = set()
        for seed in range(20):
            schedule = pet.DaySchedule(seed)
            openings.add(schedule.days[0][1])
            schedule.day_at(5000)
            previous = None
            for _, pair in schedule.days:
                self.assertNotEqual(pair[0], pair[1])
                self.assertNotEqual(pair[0], previous)
                previous = pair[1]
        self.assertGreater(len(openings), 1)
        self.assertEqual(pet.DaySchedule(7).days, pet.DaySchedule(7).days)

    def test_actions_hold_and_random_resets(self):
        with pet.control_session() as session, patch('sys.stdout', new_callable=io.StringIO):
            control = pet.ActivityControl('daily', session)
            for action, expected in pet.ACTIONS.items():
                control.tick = 100
                pet.send_action(action)
                control.poll()
                self.assertEqual(control.design, expected)
                self.assertEqual(control.tick, 0)
                control.tick = 1000
                control.poll()
                self.assertEqual(control.design, expected)
                self.assertEqual(control.tick, 1000)
            self.assertFalse((session / 'command').exists())
        self.assertFalse(session.exists())
        self.assertNotIn('KIWI_SESSION', os.environ)

    def test_latest_command_wins(self):
        with pet.control_session() as session, patch('sys.stdout', new_callable=io.StringIO):
            pet.send_action('sleep')
            pet.send_action('wake')
            control = pet.ActivityControl('daily', session)
            control.poll()
            self.assertEqual(control.design, 'round')

    def test_session_selection_and_no_running_pet(self):
        with self.assertRaisesRegex(SystemExit, 'No kiwi'):
            pet.send_action('coffee')
        with pet.control_session() as first:
            os.environ.pop('KIWI_SESSION')
            with pet.control_session() as second:
                os.environ.pop('KIWI_SESSION')
                with self.assertRaisesRegex(SystemExit, 'Several kiwis'):
                    pet.send_action('sleep')
                os.environ['KIWI_SESSION'] = str(first)
                with patch('sys.stdout', new_callable=io.StringIO):
                    pet.send_action('sleep')
                self.assertEqual((first / 'command').read_text(), 'sleep')
                self.assertFalse((second / 'command').exists())

    def test_command_subprocess_delivers_to_running_session(self):
        # Use a real session directory and a separate CLI process.
        self.root_patch.stop()
        with pet.control_session() as session:
            for action in pet.ACTIONS:
                result = subprocess.run([sys.executable, str(Path(pet.__file__).with_name('kiwi')), action], capture_output=True, text=True, check=True)
                self.assertIn(action, result.stdout)
                control = pet.ActivityControl('daily', session)
                control.poll()
                self.assertEqual(control.design, pet.ACTIONS[action])

    def test_installed_shell_exposes_entry_point_directory(self):
        args = SimpleNamespace(pet=False, shell=True)
        with patch.object(pet, '__file__', str(Path(self.temp.name) / 'site-packages' / 'kiwi_pet.py')), \
                patch.object(pet.sysconfig, 'get_path', return_value='/installed/bin'), \
                patch.dict(os.environ, {'STY': 'test', 'PATH': '/usr/bin'}), \
                patch.object(pet.subprocess, 'call') as shell, \
                patch.object(pet.subprocess, 'run'):
            pet.run(args, 'half-block')
        self.assertEqual(shell.call_args.kwargs['env']['PATH'], '/installed/bin:/usr/bin')

    def test_book_preview_launches_without_split_shell(self):
        with patch.object(sys, 'argv', ['kiwi', '--book', '--renderer', 'half-block']), \
                patch.object(pet, 'animate') as animate, \
                patch.object(pet.subprocess, 'run') as subprocess_run:
            pet.main()
        self.assertEqual(animate.call_args.args[0], 'book')
        subprocess_run.assert_not_called()

    def test_flat_book_preview_launches_without_split_shell(self):
        with patch.object(sys, 'argv', ['kiwi', '--book-flat', '--renderer', 'half-block']), \
                patch.object(pet, 'animate') as animate, \
                patch.object(pet.subprocess, 'run') as subprocess_run:
            pet.main()
        self.assertEqual(animate.call_args.args[0], 'book_flat')
        subprocess_run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
