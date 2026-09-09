#!/usr/bin/env python3
"""Render the actual first daily cycle to GIF. Requires Pillow only for export.

Run from the repository root: python3 scripts/make_demo.py
"""
from pathlib import Path
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import kiwi_pet as pet


def rgb(index):
    if index < 16:
        return [(0, 0, 0), (128, 0, 0), (0, 128, 0), (128, 128, 0),
                (0, 0, 128), (128, 0, 128), (0, 128, 128), (192, 192, 192),
                (128, 128, 128), (255, 0, 0), (0, 255, 0), (255, 255, 0),
                (0, 0, 255), (255, 0, 255), (0, 255, 255), (255, 255, 255)][index]
    if index >= 232:
        return (8 + (index - 232) * 10,) * 3
    index -= 16
    levels = (0, 95, 135, 175, 215, 255)
    return levels[index // 36], levels[index // 6 % 6], levels[index % 6]


def main():
    scale, padding = 8, 24
    schedule = pet.DaySchedule(seed=7)
    frames = []
    for tick in range(schedule.day_length(schedule.days[0][1])):
        frame = Image.new('RGB', (pet.EMERGENCY_SCENE_WIDTH * scale + padding * 2,
                                  16 * scale + padding * 2), '#171b24')
        draw = ImageDraw.Draw(frame)
        for y, row in enumerate(pet.emergency_scene(tick, schedule)):
            for x, pixel in enumerate(row):
                if pixel == ' ':
                    continue
                if pixel == 'e' and tick % 37 == 0:
                    pixel = 'b'
                left, top = padding + x * scale, padding + y * scale
                draw.rectangle((left, top, left + scale - 1, top + scale - 1),
                               fill=rgb(pet.ROUND_COLORS[pixel]))
        frames.append(frame)
    output = Path(__file__).resolve().parents[1] / 'assets' / 'kiwi-demo.gif'
    output.parent.mkdir(exist_ok=True)
    frames[0].save(output, save_all=True, append_images=frames[1:],
                   duration=220, loop=0, optimize=True, disposal=1)
    print(f'{output}: {len(frames)} frames, {output.stat().st_size:,} bytes')


if __name__ == '__main__':
    main()
