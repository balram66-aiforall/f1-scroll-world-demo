#!/usr/bin/env python3
import math
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
VID = ASSETS / "vid"
TMP = ROOT / ".frames"

WIDE = (1536, 1024)
DESKTOP = (1280, 720)
MOBILE = (720, 1280)
FPS = 24
CLIP_SECONDS = 4
CONN_SECONDS = 2

BG = "#F4EBDD"
INK = "#161616"
CARBON = "#242326"
GRAPHITE = "#5D6067"
RED = "#D51F2A"
GOLD = "#D8A431"
BLUE = "#A9D7E8"
CREAM = "#FFF6EA"
GREEN = "#6EA96A"


SCENES = [
    {
        "id": "engine",
        "accent": RED,
        "props": "garage",
    },
    {
        "id": "tires",
        "accent": BLUE,
        "props": "aero",
    },
    {
        "id": "body",
        "accent": GOLD,
        "props": "pit",
    },
    {
        "id": "assembly",
        "accent": GREEN,
        "props": "circuit",
    },
    {
        "id": "finale",
        "accent": RED,
        "props": "finale",
    },
]


def hex_to_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def lerp(a, b, t):
    return int(a + (b - a) * t)


def lerp_rgb(a, b, t):
    ar, ag, ab = hex_to_rgb(a) if isinstance(a, str) else a
    br, bg, bb = hex_to_rgb(b) if isinstance(b, str) else b
    return (lerp(ar, br, t), lerp(ag, bg, t), lerp(ab, bb, t))


def polygon_offset(points, dx, dy):
    return [(x + dx, y + dy) for x, y in points]


def draw_shadow(draw, points, blur=26):
    layer = Image.new("RGBA", WIDE, (0, 0, 0, 0))
    sh = ImageDraw.Draw(layer)
    sh.polygon(polygon_offset(points, 0, 28), fill=(40, 30, 24, 54))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    return layer


def draw_island(base, accent):
    draw = ImageDraw.Draw(base, "RGBA")
    top = [(330, 560), (760, 320), (1190, 560), (760, 805)]
    base.alpha_composite(draw_shadow(draw, top))
    side_l = [(330, 560), (760, 805), (760, 875), (330, 628)]
    side_r = [(1190, 560), (760, 805), (760, 875), (1190, 628)]
    draw.polygon(side_l, fill=lerp_rgb(CREAM, GRAPHITE, 0.24))
    draw.polygon(side_r, fill=lerp_rgb(CREAM, accent, 0.24))
    draw.polygon(top, fill=CREAM, outline=lerp_rgb(accent, INK, 0.25))
    for i in range(7):
        x0 = 440 + i * 80
        draw.line([(x0, 505), (x0 + 420, 745)], fill=(80, 80, 80, 22), width=3)
    return top


def iso_rect(draw, cx, cy, w, h, fill, outline=None):
    pts = [(cx, cy - h // 2), (cx + w // 2, cy), (cx, cy + h // 2), (cx - w // 2, cy)]
    draw.polygon(pts, fill=fill, outline=outline)
    return pts


def draw_f1_car(draw, cx, cy, scale, accent=RED, angle=0):
    # A compact toy-like F1 silhouette assembled from rounded clay parts.
    def p(x, y):
        ca, sa = math.cos(angle), math.sin(angle)
        return (cx + (x * ca - y * sa) * scale, cy + (x * sa + y * ca) * scale)

    body = [p(-150, -18), p(-80, -52), p(70, -42), p(150, -12), p(132, 22), p(-95, 48)]
    draw.polygon(body, fill=accent, outline=lerp_rgb(accent, INK, 0.32))
    nose = [p(55, -12), p(230, -5), p(230, 18), p(55, 22)]
    draw.polygon(nose, fill=lerp_rgb(accent, CREAM, 0.12), outline=lerp_rgb(accent, INK, 0.28))
    cockpit = [p(-20, -32), p(42, -28), p(70, 4), p(4, 20)]
    draw.polygon(cockpit, fill=CARBON)
    for wx, wy in [(-102, -66), (92, -58), (-104, 64), (96, 54)]:
        x, y = p(wx, wy)
        draw.ellipse((x - 24 * scale, y - 24 * scale, x + 24 * scale, y + 24 * scale), fill=INK)
        draw.ellipse((x - 10 * scale, y - 10 * scale, x + 10 * scale, y + 10 * scale), fill=GRAPHITE)
    wing1 = [p(198, -46), p(255, -38), p(250, -16), p(190, -22)]
    wing2 = [p(-175, 46), p(-224, 36), p(-220, 58), p(-166, 70)]
    draw.polygon(wing1, fill=CARBON)
    draw.polygon(wing2, fill=CARBON)
    draw.line([p(-20, 42), p(70, 28)], fill=GOLD, width=max(2, int(5 * scale)))


def draw_garage(draw, accent):
    draw.rectangle((500, 330, 1035, 580), fill=lerp_rgb(GRAPHITE, CREAM, 0.38), outline=GRAPHITE, width=4)
    draw.rectangle((540, 372, 980, 580), fill=lerp_rgb(CARBON, CREAM, 0.18))
    for x in (590, 710, 830, 950):
        draw.rounded_rectangle((x, 610, x + 54, 700), radius=18, fill=accent)
        draw.ellipse((x + 9, 584, x + 45, 620), fill=CREAM)
    draw_f1_car(draw, 750, 650, 1.1, accent, -0.06)
    for x in (455, 1070):
        draw.rounded_rectangle((x, 500, x + 55, 690), radius=20, fill=GRAPHITE)
        draw.rectangle((x + 14, 460, x + 41, 515), fill=GOLD)


def draw_aero(draw, accent):
    draw.rounded_rectangle((445, 405, 1075, 680), radius=70, fill=lerp_rgb(BLUE, CREAM, 0.45), outline=BLUE, width=5)
    draw.rectangle((500, 455, 1020, 635), fill=lerp_rgb(BLUE, CREAM, 0.72))
    for y in range(455, 650, 34):
        pts = []
        for x in range(410, 1130, 40):
            pts.append((x, y + math.sin(x * 0.025) * 16))
        draw.line(pts, fill=(60, 160, 190, 130), width=5)
    draw_f1_car(draw, 765, 580, 1.0, RED, 0.0)
    draw.ellipse((1115, 500, 1220, 610), fill=GRAPHITE)
    draw.ellipse((1140, 524, 1194, 584), fill=CARBON)


def draw_pit(draw, accent):
    draw.rectangle((470, 385, 1030, 475), fill=lerp_rgb(accent, CREAM, 0.25))
    draw_f1_car(draw, 780, 610, 1.0, RED, 0.03)
    positions = [(525, 590), (620, 530), (665, 705), (910, 532), (1000, 625), (870, 710)]
    for x, y in positions:
        draw.rounded_rectangle((x - 26, y - 18, x + 26, y + 58), radius=16, fill=accent)
        draw.ellipse((x - 17, y - 50, x + 17, y - 16), fill=CREAM)
        draw.line((x - 18, y + 10, x - 55, y + 30), fill=CARBON, width=7)
        draw.line((x + 18, y + 10, x + 52, y + 28), fill=CARBON, width=7)
    for x, y in [(545, 735), (980, 744)]:
        draw.ellipse((x - 42, y - 18, x + 42, y + 18), fill=INK)


def draw_circuit(draw, accent):
    track = [(430, 565), (550, 425), (760, 390), (1045, 455), (1135, 610), (990, 740), (730, 740), (520, 670)]
    draw.line(track + [track[0]], fill=CARBON, width=88, joint="curve")
    draw.line(track + [track[0]], fill=GRAPHITE, width=50, joint="curve")
    for i, (x, y) in enumerate(track):
        draw.ellipse((x - 8, y - 8, x + 8, y + 8), fill=CREAM if i % 2 else RED)
    draw_f1_car(draw, 838, 487, 0.76, RED, 0.22)
    draw.rectangle((590, 700, 710, 735), fill=CREAM)
    for i in range(6):
        draw.rectangle((596 + i * 19, 703, 606 + i * 19, 732), fill=INK if i % 2 else CREAM)


def draw_finale(draw, accent):
    draw_f1_car(draw, 760, 560, 1.45, accent, -0.02)
    for x, h, c in [(520, 120, GRAPHITE), (665, 170, GOLD), (810, 140, GRAPHITE)]:
        draw.rounded_rectangle((x, 715 - h, x + 120, 715), radius=22, fill=c)
    draw.ellipse((1020, 540, 1115, 635), fill=GOLD)
    draw.rectangle((1060, 623, 1076, 708), fill=GOLD)
    draw.ellipse((1040, 702, 1097, 722), fill=GRAPHITE)
    for r in range(4):
        draw.arc((380 - r * 14, 310 - r * 10, 1160 + r * 14, 850 + r * 10), 200, 340, fill=(213, 31, 42, 55), width=6)


def render_scene(scene):
    source = ASSETS / "source" / f"{scene['id']}.png"
    if source.exists():
        img = Image.open(source).convert("RGB")
        img.save(ASSETS / f"{scene['id']}.webp", quality=88, method=6)
        return img

    img = Image.new("RGBA", WIDE, BG)
    draw = ImageDraw.Draw(img, "RGBA")
    for i in range(12):
        draw.ellipse((110 + i * 120, 130 + (i % 3) * 72, 130 + i * 120, 150 + (i % 3) * 72), fill=(255, 255, 255, 65))
    draw_island(img, scene["accent"])
    draw = ImageDraw.Draw(img, "RGBA")
    {
        "garage": draw_garage,
        "aero": draw_aero,
        "pit": draw_pit,
        "circuit": draw_circuit,
        "finale": draw_finale,
    }[scene["props"]](draw, scene["accent"])
    img = img.convert("RGB")
    img.save(ASSETS / f"{scene['id']}.webp", quality=88, method=6)
    return img


def fit_cover(img, size, zoom=1.0, pan=(0, 0)):
    tw, th = size
    scale = max(tw / img.width, th / img.height) * zoom
    nw, nh = int(img.width * scale), int(img.height * scale)
    resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
    x = (tw - nw) // 2 + int(pan[0])
    y = (th - nh) // 2 + int(pan[1])
    out = Image.new("RGB", size, BG)
    out.paste(resized, (x, y))
    return out


def fit_contain(img, size, zoom=1.0, y_bias=0):
    tw, th = size
    scale = min(tw * 0.94 / img.width, th * 0.72 / img.height) * zoom
    nw, nh = int(img.width * scale), int(img.height * scale)
    resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
    out = Image.new("RGB", size, BG)
    x = (tw - nw) // 2
    y = int(th * 0.42 - nh / 2 + y_bias)
    out.paste(resized, (x, y))
    return out


def write_video_frames(frames_dir, frames, output):
    frames_dir.mkdir(parents=True, exist_ok=True)
    for i, frame in enumerate(frames):
        frame.save(frames_dir / f"frame_{i:04d}.png")
    cmd = [
        "ffmpeg",
        "-v",
        "error",
        "-y",
        "-framerate",
        str(FPS),
        "-i",
        str(frames_dir / "frame_%04d.png"),
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "slow",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
        "-g",
        "8",
        "-keyint_min",
        "8",
        "-sc_threshold",
        "0",
        "-movflags",
        "+faststart",
        str(output),
    ]
    subprocess.run(cmd, check=True)


def make_clip(scene, img, mobile=False):
    total = FPS * CLIP_SECONDS
    size = MOBILE if mobile else DESKTOP
    frames = []
    for i in range(total):
        t = i / max(1, total - 1)
        ease = t * t * (3 - 2 * t)
        if mobile:
            frame = fit_contain(img, size, zoom=1.0 + 0.18 * ease, y_bias=-34 * ease)
        else:
            frame = fit_cover(img, size, zoom=1.0 + 0.16 * ease, pan=(-28 * ease, -18 * ease))
        overlay = Image.new("RGBA", size, (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay, "RGBA")
        ax = int(size[0] * (0.08 + 0.78 * t))
        od.line([(ax - 120, size[1] * 0.18), (ax + 80, size[1] * 0.82)], fill=hex_to_rgb(scene["accent"]) + (36,), width=9)
        frame = Image.alpha_composite(frame.convert("RGBA"), overlay).convert("RGB")
        frames.append(frame)
    suffix = "-m" if mobile else ""
    write_video_frames(TMP / f"{scene['id']}{suffix}", frames, VID / f"{scene['id']}{suffix}.mp4")


def make_connector(index, a, b, mobile=False):
    total = FPS * CONN_SECONDS
    size = MOBILE if mobile else DESKTOP
    frames = []
    for i in range(total):
        t = i / max(1, total - 1)
        ease = t * t * (3 - 2 * t)
        fa = fit_contain(a, size, zoom=1.06 - 0.05 * ease) if mobile else fit_cover(a, size, zoom=1.09 - 0.05 * ease)
        fb = fit_contain(b, size, zoom=1.01 + 0.05 * ease) if mobile else fit_cover(b, size, zoom=1.01 + 0.05 * ease)
        frame = Image.blend(fa, fb, ease)
        overlay = Image.new("RGBA", size, (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay, "RGBA")
        for k in range(4):
            y = int(size[1] * (0.2 + k * 0.16) + math.sin((t + k) * math.pi) * 20)
            od.arc((-120, y - 100, size[0] + 120, y + 180), 195, 345, fill=(255, 255, 255, 42), width=5)
        frame = Image.alpha_composite(frame.convert("RGBA"), overlay).convert("RGB")
        frames.append(frame)
    suffix = "-m" if mobile else ""
    write_video_frames(TMP / f"conn{index}{suffix}", frames, VID / f"conn{index}{suffix}.mp4")


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    VID.mkdir(parents=True, exist_ok=True)
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir()

    stills = [render_scene(scene) for scene in SCENES]
    for scene, img in zip(SCENES, stills):
        portrait = fit_contain(img, MOBILE)
        portrait.save(ASSETS / f"{scene['id']}-m.webp", quality=86, method=6)
        make_clip(scene, img, mobile=False)
        make_clip(scene, img, mobile=True)

    for i in range(len(stills) - 1):
        make_connector(i + 1, stills[i], stills[i + 1], mobile=False)
        make_connector(i + 1, stills[i], stills[i + 1], mobile=True)

    shutil.rmtree(TMP)


if __name__ == "__main__":
    main()
