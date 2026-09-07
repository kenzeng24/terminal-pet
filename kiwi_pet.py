#!/usr/bin/env python3
"""A terminal kiwi above a working shell. Type exit to close both panes."""

import argparse
import ast
from functools import lru_cache
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
import time


BODY = [
    "        bbb     ",
    "       bbbeb    ",
    "   bbbbbbbbkkkkk",
    " bbbBbbbbbb    ",
    "bbBbbBbbbbb    ",
    " bbbbbbbbb     ",
    "  bbbbbbb      ",
]
FEET = [("   k  k", "  kk  kk"), ("    k k", "    kk kk")]
ROUND_BODY = [
    "    bbbbb      ",
    "  bbbbbbbbb    ",
    " bbbbbbbebb    ",
    "bbbbbbbbebkk   ",
    "bbbbbbbbbb kkk ",
    "bbbbbbbbbb   kk",
    " bbbbbbbb     k",
]
ROUND_FEET = [("   k   k       ", "  kkk kkk      ")]
SLEEPING_HEAD = [
    "aaaa ",
    "anaaa",
    "anaaa",
    "aaaaa",
]
LARGE_SLEEPING_HEAD = [
    " aaaaa ",
    "aaanaaa",
    "aaanaaa",
    "aaaaaaa",
    "aaaaaaa",
    " aaaaaa",
]
SIDE_SLEEPING_HEAD = [
    "         ",
    " aaaa    ",
    "aaaaaa   ",
    "aaaaaaa  ",
    "aannaaa  ",
    "aaaaaakkkk",
]
LAPTOP = [
    "    ssssssssss",
    "    sdddddddds",
    "    sdddddddds",
    "    sdddddddds",
    "    sdddddddds",
    "    sdddddddds",
    "    sdddddddds",
    "    ssssssssss",
    "sssssssssssss ",
]
MONITOR_FRAMES = [
    ("uuuuuunn", "vvvvnnnn", "nnnnnncn", "nnncnncc", "ncnccncc", "cccccccc"),
    ("uuuunnnn", "vvvvvnnn", "nnnnncnn", "nncnnccn", "cnccnccn", "cccccccn"),
    ("uuuuuuuu", "vvvvvvnn", "nnnncnnc", "ncnnccnc", "ccncccnc", "cccccccc"),
    ("uuunnnnn", "vvvvnnnn", "nnncnncn", "cnccnccn", "ccnccccc", "cccccccc"),
]
EMERGENCY_MONITOR_FRAMES = [
    ("RRRRRRRR", "TTTRRRRR", "nRRRnRRR", "RRRRnRRR", "RRRRRRRR", "RRRRRRRR"),
    ("RRRRRRRT", "RRRRRRRR", "RRnRRRRR", "RRRRRRnR", "RRRRnRRR", "RRRRRRRR"),
    ("TRRRRRRR", "RRRRRRRT", "RRRnRRRR", "nRRRRRRR", "RRRRRRnR", "RRRRRRRR"),
    ("RRRRRRRR", "RTRRRRRR", "RnRRRnRR", "RRnRRRRR", "RRRRRRRR", "RRRRRRRR"),
]
GPU = [
    "ggggrrrrrr",
    "grrgrnnnnr",
    "ggggrnnnnr",
    "grrgrnnnnr",
    "ggggrrrrrr",
    "grrgrnnnnr",
    "ggggrnnnnr",
    "grrgrnnnnr",
    "ggggrrrrrr",
]
FAN_FRAMES = [
    # Cross/X silhouettes with evenly colored blades.
    ("nfn", "fgf", "nfn"),
    ("fnf", "ngn", "fnf"),
]
BOOK = [
    "         o   ",
    "      aaoPa  ",
    " PPP aaoooPa ",
    " lllloooooPaa",
    " lllloooPoPaa",
    " llllooPoooPa",
    "  lllloooooPa",
    "   klloooooaa",
    "   kllooo aaa",
]
# Sheets pivot at (5, 3), the top junction of the lime and green covers.
PAGE_TURNS = [
    (),
    ((5, 3), (6, 3), (6, 2), (7, 2), (8, 2)),
    ((5, 3), (5, 2), (6, 2), (6, 1), (7, 1)),
    ((5, 3), (5, 2), (5, 1), (5, 0)),
    ((5, 3), (5, 2), (4, 2), (4, 1), (3, 1)),
    ((5, 3), (4, 3), (4, 2), (3, 2), (2, 2)),
    ((5, 3), (4, 3), (3, 3), (2, 3), (1, 3)),
]
COFFEE_KIWI = [
    "             ",
    "       aaaa  ",
    "      aaaaaa ",
    "     kaaeeaaa",
    " oooooooaaaaa",
    " o oooooaaaaa",
    " oooooooaaaaa",
    "  kooookkaaaa",
    "  kooookkaaaa",
]
STEAM_FRAMES = [
    ("  JJJ ", " JJ   ", " JJJ  ", "   JJ ", "  JJJ ", "   J  "),
    (" JJJJ ", "   JJ ", "  JJ  ", " JJ   ", " JJJJ ", "   J  "),
    ("   JJJ", "  JJ  ", "  JJJ ", "    JJ", "   JJ ", "   J  "),
    ("  JJJJ", "    JJ", "   JJ ", "  JJ  ", "  JJJJ", "   J  "),
]
ROUND_SCENE_WIDTH = 28 + 1 + len(GPU[0])
EMERGENCY_SCENE_WIDTH = ROUND_SCENE_WIDTH + 3
DESIGNS = {
    "classic": (BODY, FEET),
    "round": (ROUND_BODY, ROUND_FEET),
    "sleep": (ROUND_BODY, ROUND_FEET),
    "sleep_large": (ROUND_BODY, ROUND_FEET),
    "sleep_side": (ROUND_BODY, ROUND_FEET),
    "bedtime": (ROUND_BODY, ROUND_FEET),
    "daily": (ROUND_BODY, ROUND_FEET),
    "reading": (ROUND_BODY, ROUND_FEET),
    "coffee": (ROUND_BODY, ROUND_FEET)
}
DESK_DESIGNS = ("round", "sleep", "sleep_large", "sleep_side", "bedtime", "daily", "reading", "coffee")
BEDTIME_AWAKE_TICKS = 56
BEDTIME_CYCLE_TICKS = 122
DAY_LENGTHS = {
    "normal": 122,
    "blue_screen": 192,
    "overheat": 192,
    "download": 122,
    "coffee": 122,
    #"terminal": 122,
    "debugging": 122,
    # "semicolon": 122,
    "block_fix": 122,
}

NIGTHT_DISPLAYS = ("screensaver", "download", "default")


@lru_cache(maxsize=1)
def terminal_pixels():
    """Compress this file's actual code into eight-pixel text lines."""
    source = Path(__file__).read_text()
    lines = source.splitlines()
    rows = []
    # Skip sprite/palette literals and keep functions and classes in source order.
    for node in ast.parse(source).body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        for line in lines[node.lineno - 1:node.end_lineno]:
            text = line.strip()
            if not text:
                rows.append("n" * 8)
                continue
            indent = min(3, (len(line) - len(line.lstrip())) // 4)
            # One pixel per indentation level; ten source characters per text pixel.
            chunks = [text[i:i + 10] for i in range(0, len(text), 10)]
            ink = "".join("u" if chunk.strip() else "n" for chunk in chunks)
            rows.append(("n" * indent + ink[:8 - indent]).ljust(8, "n"))
        rows.extend(("n" * 8, "n" * 8))
    return tuple(rows)


class DaySchedule:
    """Choose two distinct daytime events, followed by one night."""

    NIGHT_TICKS = BEDTIME_CYCLE_TICKS - BEDTIME_AWAKE_TICKS

    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        if len(DAY_LENGTHS) < 2:
            raise ValueError("Keep at least two events enabled in DAY_LENGTHS.")
        first_pair = self.enabled_pair(("normal", "coffee"))
        second_pair = self.enabled_pair(("semicolon", "block_fix"))
        second_start = self.day_length(first_pair)
        self.days = [(0, first_pair), (second_start, second_pair)]
        self.night_displays = {0: "default", second_start: "screensaver"}

    def enabled_pair(self, preferred):
        """Replace disabled preset events without changing the enabled choices."""
        reserved = set(preferred) & DAY_LENGTHS.keys()
        replacements = iter(name for name in DAY_LENGTHS if name not in reserved)
        return tuple(name if name in DAY_LENGTHS else next(replacements)
                     for name in preferred)

    @classmethod
    def day_length(cls, pair):
        return sum(DAY_LENGTHS[event] - cls.NIGHT_TICKS for event in pair) + cls.NIGHT_TICKS

    def day_at(self, tick):
        start, pair = self.days[-1]
        while tick >= start + self.day_length(pair):
            start += self.day_length(pair)
            first = self.rng.choice([name for name in DAY_LENGTHS if name != pair[-1]])
            second = self.rng.choice([name for name in DAY_LENGTHS if name != first])
            pair = (first, second)
            self.days.append((start, pair))
            self.night_displays[start] = self.rng.choice(NIGTHT_DISPLAYS)
        for start, pair in reversed(self.days):
            if tick >= start:
                return start, pair, tick - start
        raise ValueError("Animation ticks must be nonnegative")

    def at(self, tick):
        _, pair, phase = self.day_at(tick)
        first_duration = DAY_LENGTHS[pair[0]] - self.NIGHT_TICKS
        if phase < first_duration:
            return pair[0], phase
        return pair[1], phase - first_duration


DAILY_SCHEDULE = DaySchedule()
COLORS = {"b": 94, "B": 130, "k": 180, "e": 16, "s": 245, "d": 24,
          "r": 238, "n": 16, "f": 250, "g": 250,
          "u": 82, "v": 171, "c": 81, "q": 39, "h": 117,
          "a": 94, "w": 52, "R": 196, "T": 160, "!": 196,
          "j": 255, "J": 255, "o": 35, "l": 154, "p": 180, "P": 230}
# Apple's old screen build reduces 256 colors, mapping our browns to red.
# Use native dark yellow for the kiwi and dark red for the desk in split mode.
SCREEN_COLORS = {"b": 43, "B": 43, "k": 103, "e": 40, "s": 47, "d": 44,
                 "r": 100, "n": 40, "f": 47, "g": 47,
                 "u": 42, "v": 45, "c": 46, "q": 46, "h": 106,
                 "a": 43, "w": 41, "R": 101, "T": 41, "!": 101,
                 "j": 107, "J": 107, "o": 42, "l": 102, "p": 103, "P": 107}
ROUND_COLORS = {**COLORS, "k": 226, "s": 252, "d": 21}


def round_scene(tick, sleeping=False, *, sleep_tick=None, bubble_tick=None,
                bubble_stop=None, emergency=False):
    """Animate the kiwi or its duvet beside the running computer."""
    bob_tick = tick * 4 if emergency else tick
    bob = (0, 0, 0, 1, 1, 1, 1, 0)[bob_tick % 8]
    rows = [list(" " * 28) for _ in range(10)]
    if sleeping:
        sleep_clock = tick if sleep_tick is None else sleep_tick
        rise = (sleep_clock // 6) % 2
        # Keep the body filled to the bed while the head rises with breathing.
        for y, row in enumerate(SLEEPING_HEAD, 5 - rise):
            for x, pixel in enumerate(row, 9):
                if pixel != " ":
                    rows[y][x] = pixel
        for y in range(9 - rise, 9):
            rows[y][9:14] = "aaaaa"
        if rise:
            # The sideways face reveals its lower eye above the desk.
            rows[8][10] = "n"
        for y in range(4 - rise, 9):
            left = max(1, 5 - (y - (4 - rise)))
            rows[y][left:9] = "q" * (9 - left)
        rows[8 - rise][6:10] = "kkkk"
        # Bubbles emerge, rise, expand, and pop above the sleeping kiwi.
        bubble_clock = tick if bubble_tick is None else bubble_tick
        for x, offset in ((11, 0), (14, 4)):
            age = (bubble_clock - offset * 3) % 24
            birth = bubble_clock - age
            if bubble_stop is not None and (birth < 0 or birth >= bubble_stop):
                continue
            phase = age // 3
            if phase < 2:
                rows[3 - phase][x] = "h"
            elif phase < 5:
                for dx, dy in ((1, 0), (0, 1), (2, 1), (1, 2)):
                    rows[dy][x - 1 + dx] = "h"
            elif phase == 5:
                rows[0][x - 1] = rows[1][x + 1] = "h"
    else:
        for y, row in enumerate(ROUND_FEET[0], len(ROUND_BODY)):
            rows[y][1:1 + len(row)] = row
        for y, row in enumerate(ROUND_BODY, bob):
            for x, pixel in enumerate(row, 1):
                if pixel != " ":
                    rows[y][x] = pixel
    for y, row in enumerate(LAPTOP):
        for x, pixel in enumerate(row, 14):
            if pixel != " ":
                rows[y][x] = pixel
    monitor_frames = EMERGENCY_MONITOR_FRAMES if emergency else MONITOR_FRAMES
    monitor_tick = tick if emergency else tick // 3
    for y, row in enumerate(monitor_frames[monitor_tick % len(monitor_frames)], 1):
        rows[y][19:27] = row
    gpu = [list(row) for row in GPU]
    for fan_index, top in enumerate((1, 5)):
        phase = (tick + fan_index * 2) % len(FAN_FRAMES)
        for y, row in enumerate(FAN_FRAMES[phase], top):
            gpu[y][5:8] = row
    gpu.append(list(" " * len(GPU[0])))
    scene = ["".join(row) + " " + "".join(gpu_row)
             for row, gpu_row in zip(rows, gpu)]
    scene[9] = "w" * ROUND_SCENE_WIDTH
    scene.append("w" * ROUND_SCENE_WIDTH)
    scene.append("  ww" + " " * (ROUND_SCENE_WIDTH - 10) + "ww" + " " * 4)
    return scene


def bedtime_scene(tick):
    """Cut between poses, pausing before breathing and after the last bubble."""
    phase = tick % BEDTIME_CYCLE_TICKS
    if phase < BEDTIME_AWAKE_TICKS:
        return [" " * ROUND_SCENE_WIDTH] * 4 + round_scene(tick)

    # Enter the complete sleeping pose and hold it for six ticks.
    # Then breathe and emit bubbles, stopping new bubbles after 48 ticks.
    # The final bubble pops at clock 51, vanishes at 54, and wake-up is at 60.
    sleep_clock = phase - (BEDTIME_AWAKE_TICKS + 6)
    return side_sleep_scene(
        tick,
        sleep_tick=max(0, min(sleep_clock, 48)),
        bubble_tick=sleep_clock, bubble_stop=48,
    )


def debugging_display(phase):
    """Scroll, replace a bad line, fail, then rewrite the block successfully."""
    code = terminal_pixels()
    scroll = min(phase, 10) // 2
    display = list(code[scroll:scroll + 6])
    # Keep the edit location visible, with two surrounding lines of context.
    if phase >= 10:
        display[2:5] = ["nuuuuunn", "nnnnnnnn", "nnnnnnnn"]
    if 10 <= phase < 16:
        display[2] = display[2].replace("u", "R")
    elif 16 <= phase < 19:
        display[2] = "n" * 8
    elif 19 <= phase < 28:
        block = ("nuuuuuun", "nnuuuunn", "nnuuuuun")
        written = min(18, (phase - 19 + 1) * 2)
        display[2:5] = _written_block(block, written)
    elif 28 <= phase < 35:
        display[2:5] = ["nuuuuuun", "nnuuuunn", "nnuuuuun"]
        display = [row.replace("u", "R") for row in display]
    elif 35 <= phase < 41:
        block = ("nuuuuuun", "nnuuuunn", "nnuuuuun")
        display[2:5] = _written_block(block, max(0, 15 - (phase - 35 + 1) * 3))
        display = [row.replace("u", "R") for row in display]
    elif phase >= 41:
        block = ("nuuuunnn", "nnuuuuun", "nnuuunnn")
        display[2:5] = _written_block(block, min(12, (phase - 41 + 1) * 2))
        if phase < 48:
            display = [row.replace("u", "R") for row in display]
    return display


def quick_fix_display(phase, event):
    """Fix a missing punctuation pixel or rewrite two faulty code lines."""
    code = terminal_pixels()
    scroll = min(phase, 10) // 2
    display = list(code[scroll:scroll + 6])
    if phase < 10:
        return display
    if event == "semicolon":
        display[3] = "nnuuuunn"
        if phase < 32:
            return [row.replace("u", "R") for row in display]
        # The only change to the code is this one added pixel.
        display[3] = "nnuuuuun"
    else:
        original = ("nnuuuuun", "nnuuuunn")
        replacement = ("nnuuunnn", "nnuuuuun")
        if phase < 24:
            display[2:4] = [row.replace("u", "R") for row in original]
        elif phase < 30:
            display[2:4] = [row.replace("u", "R") for row in
                            _written_block(original, max(0, 9 - (phase - 23) * 2))]
        elif phase < 42:
            display[2:4] = _written_block(replacement, (phase - 29))
        else:
            display[2:4] = replacement
    return display


def _written_block(block, count):
    """Reveal code pixels in typing order, retaining each line's indentation."""
    rows = []
    for row in block:
        pixels = []
        for pixel in row:
            if pixel == "u":
                pixels.append("u" if count > 0 else "n")
                count -= 1
            else:
                pixels.append(pixel)
        rows.append("".join(pixels))
    return rows


def _daily_scene(tick, schedule):
    """Render the chosen daytime event and its sleeping phase."""
    recovery_ticks = 28
    coffee_ticks = 42
    event, phase = schedule.at(tick)
    if event in ("normal", "download", "coffee", "terminal", "debugging",
                 "semicolon", "block_fix"):
        if phase >= BEDTIME_AWAKE_TICKS:
            sleep_clock = phase - BEDTIME_AWAKE_TICKS - 6
            scene = side_sleep_scene(tick,
                                sleep_tick=max(0, min(sleep_clock, 48)),
                                bubble_tick=sleep_clock, bubble_stop=48)
            return ["   " + row for row in scene]
        elif event in ("coffee", "download"):
            scene = coffee_scene(tick, motion_tick=phase,
                                 resting=phase >= BEDTIME_AWAKE_TICKS - 6)
            if event == "download":
                # Fill one pixel at a time, finishing before the quiet pause.
                filled = min(8, phase * 8 // (BEDTIME_AWAKE_TICKS - 7))
                display = ("nnnnnnnn", "nnnnnnnn", "nnnnnnnn", "nnnnnnnn",
                           "u" * filled + "r" * (8 - filled), "nnnnnnnn")
                for y, row in enumerate(display, 3):
                    scene[y] = scene[y][:19] + row + scene[y][27:]
            return ([" " * EMERGENCY_SCENE_WIDTH] * 2 +
                    ["   " + row for row in scene])
        else:
            scene = round_scene(tick)
            if event == "terminal":
                code_rows = terminal_pixels()
                for y in range(6):
                    row = code_rows[(y + phase // 2) % len(code_rows)]
                    scene[y + 1] = scene[y + 1][:19] + row + scene[y + 1][27:]
            elif event == "debugging":
                for y, row in enumerate(debugging_display(phase), 1):
                    scene[y] = scene[y][:19] + row + scene[y][27:]
            elif event in ("semicolon", "block_fix"):
                for y, row in enumerate(quick_fix_display(phase, event), 1):
                    scene[y] = scene[y][:19] + row + scene[y][27:]
        overhead = [" " * EMERGENCY_SCENE_WIDTH] * 4
        return overhead + ["   " + row for row in scene]
    alarm = phase < BEDTIME_AWAKE_TICKS
    recovery = phase - BEDTIME_AWAKE_TICKS
    if alarm:
        scene = round_scene(tick, emergency=True)
        if event == "blue_screen":
            rows = [list(row) for row in scene]
            for y in range(1, 7):
                rows[y][19:27] = "d" * 8
            for top in (1, 5):
                for y, row in enumerate(FAN_FRAMES[0], top):
                    rows[y][34:37] = row
            scene = ["".join(row) for row in rows]
    elif recovery < recovery_ticks:
        rows = [list(row) for row in round_scene(tick)]
        # Hold the display black during shutdown and the initial fan restart.
        if recovery < 16:
            for y in range(1, 7):
                rows[y][19:27] = "nnnnnnnn"
        if recovery < 8:
            for top in (1, 5):
                for y, row in enumerate(FAN_FRAMES[0], top):
                    rows[y][34:37] = row
        scene = ["".join(row) for row in rows]
    elif recovery < recovery_ticks + coffee_ticks:
        coffee_clock = recovery - recovery_ticks
        coffee = coffee_scene(tick, motion_tick=coffee_clock, resting=coffee_clock >= 36)
        return ([" " * EMERGENCY_SCENE_WIDTH] * 2 +
                ["   " + row for row in coffee])
    else:
        sleep_clock = recovery - recovery_ticks - coffee_ticks - 6
        scene = side_sleep_scene(tick,
                            sleep_tick=max(0, min(sleep_clock, 48)),
                            bubble_tick=sleep_clock, bubble_stop=48)
        return ["   " + row for row in scene]
    # Reserve space above for smoke and to the left for the warning.
    overhead = [list(" " * ROUND_SCENE_WIDTH) for _ in range(4)]
    if alarm and event == "overheat":
        # Overlapping bands form a continuous plume anchored to the GPU.
        curl = (0, 1, 1, 0, -1, -1)
        for y in range(4):
            offset = curl[(phase // 2 + y) % len(curl)] if y < 3 else 0
            x = 34 + offset
            width = 3 if y < 2 else 2
            overhead[y][x:x + width] = "j" * width
    frame = ["   " + "".join(row) for row in overhead] + ["   " + row for row in scene]
    if alarm:
        for y in (2, 3, 5):
            frame[y] = frame[y][:19] + "!" + frame[y][20:]
    return frame


def emergency_scene(tick, schedule=None):
    """Run daily events with a randomly selected display for each night."""
    schedule = schedule or DAILY_SCHEDULE
    event, phase = schedule.at(tick)
    frame = _daily_scene(tick, schedule)
    night_start = DAY_LENGTHS[event] - (BEDTIME_CYCLE_TICKS - BEDTIME_AWAKE_TICKS)
    day_start, _, _ = schedule.day_at(tick)
    night_display = schedule.night_displays[day_start]
    if phase >= night_start and night_display != "default":
        # A two-pixel square bounces inside the 8-by-6 display.
        step = (phase - night_start) // 3
        x = 6 - abs(step % 12 - 6)
        y = 4 - abs(step % 8 - 4)
        screen = [list("n" * 8) for _ in range(6)]
        color = ("c", "v", "u")[(step // 6) % 3]
        for dy in (0, 1):
            screen[y + dy][x:x + 2] = color * 2
        if night_display == "download":
            screen = [list("n" * 8) for _ in range(6)]
            filled = min(8, (phase - night_start) * 8 // 59)
            screen[4] = list("u" * filled + "r" * (8 - filled))
        for row_y, row in enumerate(screen, 5):
            frame[row_y] = frame[row_y][:22] + "".join(row) + frame[row_y][30:]
    return frame


def reading_scene(tick):
    """Show the reading sprite beside the laptop, with pages pivoting at its spine."""
    rows = [list(row) for row in round_scene(tick)]
    # Replace the kiwi, preserving the laptop, including its leftmost base.
    for y in range(9):
        end = 14 if y == 8 else 18
        rows[y][:end] = " " * end
    book = [list(row) for row in BOOK]
    phase = tick % 28
    page = 0 if phase < 14 else min(6, 1 + (phase - 14) // 2)
    for x, y in PAGE_TURNS[page]:
        book[y][x] = "P"
    for y, row in enumerate(book):
        rows[y][1:14] = row
    return ["".join(row) for row in rows]


def coffee_scene(tick, *, motion_tick=None, resting=False):
    """Hold a green mug while a white ribbon of steam curls above its rim."""
    rows = [list(row) for row in round_scene(tick)]
    for y in range(9):
        end = 14 if y == 8 else 18
        rows[y][:end] = " " * end
    for y, row in enumerate(COFFEE_KIWI):
        rows[y][1:14] = row
    motion_clock = tick if motion_tick is None else motion_tick
    if not resting and (motion_clock // 6) % 2:
        # Lower the head and compress the body against its fixed bottom edge.
        for y, row in enumerate(COFFEE_KIWI):
            for x, pixel in enumerate(row, 1):
                if pixel in ("a", "e"):
                    rows[y][x] = " "
        for y, row in enumerate(COFFEE_KIWI):
            for x, pixel in enumerate(row, 1):
                target_y = min(y + 1, len(COFFEE_KIWI) - 1)
                if pixel in ("a", "e") and rows[target_y][x] in " ae":
                    rows[target_y][x] = pixel
    rows = [list(" " * ROUND_SCENE_WIDTH) for _ in range(2)] + rows
    if not resting:
        steam = STEAM_FRAMES[(motion_clock // 3) % len(STEAM_FRAMES)]
        for y, row in enumerate(steam):
            for x, pixel in enumerate(row, 2):
                if pixel == "J":
                    rows[y][x] = pixel
    return ["".join(row) for row in rows]


def large_sleep_scene(tick):
    """A full-sized sleeping kiwi, with extra room above for its bubbles."""
    original = round_scene(tick, sleeping=True)
    rows = [list(row) for row in original]
    for y in range(9):
        end = 14 if y == 8 else 18
        rows[y][:end] = " " * end
    rise = (tick // 6) % 2
    for y, row in enumerate(LARGE_SLEEPING_HEAD, 3 - rise):
        for x, pixel in enumerate(row, 7):
            if pixel != " ":
                rows[y][x] = pixel
    if rise:
        rows[8][8:14] = "aaaaaa"
        rows[8][10] = "n"
    for y in range(2 - rise, 9):
        left = max(1, 5 - 2 * (y - (2 - rise)))
        rows[y][left:9] = "q" * (9 - left)
    rows[7 - rise][6:10] = "kkkk"
    rows = [list(" " * ROUND_SCENE_WIDTH) for _ in range(2)] + rows
    for y, row in enumerate(original[:4]):
        for x, pixel in enumerate(row[:18]):
            if pixel == "h":
                rows[y][x] = pixel
    return ["".join(row) for row in rows]


def side_sleep_scene(tick, *, sleep_tick=None, bubble_tick=None, bubble_stop=None):
    """Keep the sideways head still while the pale blue duvet breathes."""
    rows = [list(row) for row in round_scene(tick)]
    for y in range(9):
        end = 14 if y == 8 else 18
        rows[y][:end] = " " * end
    sleep_clock = tick if sleep_tick is None else sleep_tick
    rise = (sleep_clock // 6) % 2
    top = 2 - rise
    # A rounded dome stays broad behind the face instead of tapering away.
    outline = ((5, 8), (4, 10), (3, 11), (2, 11), (2, 11),
               (2, 11), (2, 10), (2, 9))
    for y in range(top, 9):
        left, right = outline[min(y - top, len(outline) - 1)]
        rows[y][left:right] = "h" * (right - left)
    # Draw the face last so the breathing blanket cannot cover or shift it.
    for y, row in enumerate(SIDE_SLEEPING_HEAD, 3):
        for x, pixel in enumerate(row, 8):
            if pixel != " ":
                rows[y][x] = pixel
    # Give the bubbles their own space above the breathing duvet.
    rows = [list(" " * ROUND_SCENE_WIDTH) for _ in range(4)] + rows
    bubbles = round_scene(tick, sleeping=True, bubble_tick=bubble_tick,
                         bubble_stop=bubble_stop)
    for y, row in enumerate(bubbles[:4]):
        for x, pixel in enumerate(row[:18]):
            if pixel == "h":
                rows[y][x] = pixel
    return ["".join(row) for row in rows]


def pixels(row, blink, design="classic"):
    palette = SCREEN_COLORS if os.environ.get("STY") else (
        ROUND_COLORS if design in DESK_DESIGNS else COLORS
    )
    prefix = "" if os.environ.get("STY") else "48;5;"
    return "".join(
        "\033[0m  " if c == " " else
        f"\033[{prefix}{palette['b' if blink and c == 'e' else c]}m  "
        for c in row
    ) + "\033[0m"


def animate(design="classic"):
    if not sys.stdout.isatty():
        sys.exit("Run this pet in an interactive terminal.")
    body, feet = DESIGNS[design]
    sprite_width = ROUND_SCENE_WIDTH if design in DESK_DESIGNS else max(len(row) for row in body)
    if design == "daily":
        sprite_width = EMERGENCY_SCENE_WIDTH
    min_width = max(32, sprite_width * 2)
    min_height = {"daily": 18, "sleep": 18, "sleep_side": 18, "bedtime": 18, "coffee": 16, "sleep_large": 16}.get(design, 14 if design in DESK_DESIGNS else 12)
    x, direction, tick = 0, 1, 0
    try:
        # Alternate screen preserves your shell; hide the cursor while playing.
        sys.stdout.write("\033[?1049h\033[?25l")
        while True:
            width, height = shutil.get_terminal_size()
            if width < min_width or height < min_height:
                frame = f"\033[H\033[2JPlease resize to {min_width} x {min_height} or larger."
            else:
                limit = (width - sprite_width * 2) // 2
                if design in DESK_DESIGNS:
                    x = limit // 2
                    rows = (emergency_scene(tick) if design == "daily" else
                            side_sleep_scene(tick) if design in ("sleep", "sleep_side") else
                            large_sleep_scene(tick) if design == "sleep_large" else
                            coffee_scene(tick) if design == "coffee" else
                            reading_scene(tick) if design == "reading" else
                            bedtime_scene(tick) if design == "bedtime" else
                            round_scene(tick, sleeping=design == "sleep"))
                else:
                    x = max(0, min(limit, x + direction))
                    if x in (0, limit):
                        direction *= -1
                    rows = body + list(feet[tick % 2])
                blink = random.random() < 0.08
                frame = "\033[H\033[2J"
                for y, row in enumerate(rows, 2):
                    row = row.ljust(sprite_width)
                    if direction < 0:
                        row = row[::-1]
                    frame += f"\033[{y};{x * 2 + 1}H" + pixels(row, blink, design)
            sys.stdout.write(frame)
            sys.stdout.flush()
            tick += 1
            time.sleep(0.22)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[0m\033[?25h\033[?1049l")
        sys.stdout.flush()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design", choices=DESIGNS, default="daily",
                        help="kiwi style (default: daily)")
    parser.add_argument("--pet", action="store_true",
                        help="show only the pet; Ctrl-C to quit")
    parser.add_argument("--shell", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.pet:
        return animate(args.design)
    if args.shell:
        try:
            subprocess.call([os.environ.get("SHELL") or "/bin/sh", "-i"])
        finally:
            subprocess.run([shutil.which("screen"), "-S", os.environ["STY"],
                            "-X", "quit"], check=False)
        return
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        sys.exit("Run this pet in an interactive terminal.")
    screen = shutil.which("screen")
    if not screen:
        sys.exit("This mode requires GNU screen. Use --pet for the pet alone.")
    width, height = shutil.get_terminal_size()
    min_width = ROUND_SCENE_WIDTH * 2 if args.design in DESK_DESIGNS else 32
    if args.design == "daily":
        min_width = EMERGENCY_SCENE_WIDTH * 2
    pane_height = {"daily": 18, "sleep": 18, "sleep_side": 18, "bedtime": 18, "coffee": 16, "sleep_large": 16}.get(args.design, 14 if args.design in DESK_DESIGNS else 12)
    if width < min_width or height < pane_height + 8:
        sys.exit(f"Please resize your terminal to at least {min_width} columns by {pane_height + 8} rows.")

    # Screen owns the panes, so shell output and full-screen apps stay separate.
    def quote(value):
        return '"' + value.replace('\\', '\\\\').replace('"', '\\"').replace('$', '\\$') + '"'

    command = f"{quote(sys.executable)} {quote(os.path.abspath(__file__))}"
    config = ("startup_message off\n"
              "vbell off\n"
              f"screen -t kiwi {command} --pet --design {args.design}\n"
              f"split\nresize {pane_height}\nfocus down\n"
              f"screen -t shell {command} --shell\n")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".screenrc") as rc:
        rc.write(config)
        rc.flush()
        subprocess.run([screen, "-m", "-S", f"kiwi-{os.getpid()}",
                        "-c", rc.name], check=False)


if __name__ == "__main__":
    main()
