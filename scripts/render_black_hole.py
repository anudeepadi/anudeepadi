"""Render an original character-only black-hole header. Requires Pillow.

Run: python3 scripts/render_black_hole.py
The GIF loops independently of scrolling. The PNG is the reduced-motion fallback.
"""
from pathlib import Path
import math
import random
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets' / 'profile'
OUT.mkdir(parents=True, exist_ok=True)
COLS, ROWS = 96, 28
CELL_W, CELL_H, PAD = 8, 14, 24
W, H = COLS * CELL_W + 2 * PAD, ROWS * CELL_H + 2 * PAD
FRAMES = 96
RAMP = ' .,:;-=+*#%@'
font_paths = [Path('/System/Library/Fonts/Menlo.ttc'),
              Path('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf')]
font_path = next((p for p in font_paths if p.exists()), None)
if font_path is None:
    raise SystemExit('Install Menlo or DejaVu Sans Mono before rendering.')
font = ImageFont.truetype(str(font_path), 12)
rng = random.Random(721)
stars = [(rng.randrange(COLS), rng.randrange(ROWS), rng.choice('.+*'), rng.random())
         for _ in range(28)]
palette = []
for n in range(256):
    v = n / 255
    palette.extend((round(13 + 208 * v), round(17 + 214 * v), round(23 + 216 * v)))
palette_image = Image.new('P', (1, 1))
palette_image.putpalette(palette)
frames = []
for f in range(FRAMES):
    t = f / FRAMES
    grid = [[' ' for _ in range(COLS)] for _ in range(ROWS)]
    strength = [[0.0 for _ in range(COLS)] for _ in range(ROWS)]
    for sx, sy, char, seed in stars:
        # One full drift per loop, with an identical end/start state.
        x = int((sx + t * COLS) % COLS)
        grid[sy][x] = char
        strength[sy][x] = .28 + .12 * math.sin(2 * math.pi * (t + seed))
    for k in range(4):
        y = int((k * 7 + t * ROWS) % ROWS)
        x = (k * 23 + 5 + y // 3) % COLS
        for trail, char in enumerate((':', '.', '.')):
            yy = (y - trail) % ROWS
            grid[yy][x] = char
            strength[yy][x] = .31 / (trail + 1)
    for row in range(ROWS):
        for col in range(COLS):
            x = col - (COLS - 1) / 2
            y = (row - (ROWS - 1) / 2) * 1.75
            radius = math.hypot(x, y)
            if radius < 8.5:
                grid[row][col] = ' '
                strength[row][col] = 0
                continue
            # Photon ring plus a thin, tilted accretion disk, all made of type.
            ring = .9 * math.exp(-((radius - 9.8) / 1.3) ** 2)
            yy = y + x * .07
            disk_r = math.hypot(x, yy * 4.2)
            disk = 0
            if 11 < disk_r < 37:
                edge = max(0, min(1, (disk_r - 11) / 3, (37 - disk_r) / 7))
                azimuth = math.atan2(yy * 4.2, x)
                flow = .72 + .22 * math.sin(azimuth * 3 - t * 2 * math.pi)
                texture = .84 + .16 * math.cos(disk_r * 1.8 - t * 4 * math.pi)
                disk = edge * flow * texture * (.9 if y > 0 else .67)
            glow = .14 * math.exp(-((radius - 10.5) / 2.8) ** 2)
            value = min(1, max(ring, disk) + glow)
            if value > .07:
                grid[row][col] = RAMP[min(len(RAMP) - 1, int(value * (len(RAMP) - 1)))]
                strength[row][col] = .28 + value * .67
    im = Image.new('RGB', (W, H), (13, 17, 23))
    draw = ImageDraw.Draw(im)
    for row in range(ROWS):
        for col in range(COLS):
            char = grid[row][col]
            if char == ' ':
                continue
            v = strength[row][col]
            color = (round(13 + 208 * v), round(17 + 214 * v), round(23 + 216 * v))
            draw.text((PAD + col * CELL_W, PAD + row * CELL_H), char,
                      font=font, fill=color, stroke_width=0)
    if f == 0:
        im.save(OUT / 'black-hole-still.png', optimize=True)
        (OUT / 'black-hole.txt').write_text('\n'.join(''.join(line).rstrip() for line in grid) + '\n')
    frames.append(im.quantize(palette=palette_image, dither=Image.Dither.NONE))
frames[0].save(OUT / 'black-hole.gif', save_all=True, append_images=frames[1:],
               duration=70, loop=0, optimize=True, disposal=1)
print('Header:', W, 'x', H, '/', FRAMES, 'frames / 6.72 second loop')
print('GIF:', (OUT / 'black-hole.gif').stat().st_size, 'bytes')
