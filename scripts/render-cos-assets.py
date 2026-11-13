#!/usr/bin/env python3
"""Render Linux-C.O.S raster artwork: wallpapers (one per colour mode), the
Plymouth boot animation, the GRUB/isolinux/greeter backgrounds.

Needs Pillow and the Oxanium + JetBrains Mono fonts (both OFL, packaged in
Kali as fonts-oxanium / fonts-jetbrains-mono):

    python3 scripts/render-cos-assets.py --fonts <dir with oxanium/ and jetbrains-mono/>

Outputs are committed, so the ISO build never needs Pillow.  Colours come from
usr/share/linux-cos/palettes.json -- the same file the desktop, Hub and
terminal use, so everything stays one colour system.
"""
from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
INC = ROOT / "build/config/includes.chroot"
SHARE = INC / "usr/share/linux-cos"
BG_DIR = INC / "usr/share/backgrounds/linux-cos"
LOGO = ROOT / "build/branding/logo/logo-512.png"


def hex_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def font(fonts: Path, family: str, weight: str, size: int) -> ImageFont.FreeTypeFont:
    cands = list((fonts / family).glob(f"*{weight}.ttf")) or list((fonts / family).glob("*.ttf"))
    f = ImageFont.truetype(str(cands[0]), size)
    try:  # variable font (Oxanium ships as one)
        f.set_variation_by_name(weight)
    except Exception:
        pass
    return f


def glow(layer: Image.Image, radius: float, strength: float = 1.0) -> Image.Image:
    """Gaussian glow of an RGBA layer, blurred with premultiplied alpha so the
    transparent black around shapes does not darken the halo."""
    import numpy as np

    a = np.asarray(layer.convert("RGBA"), dtype=np.float32) / 255.0
    pm = a[..., :3] * a[..., 3:4]
    chans = [Image.fromarray((pm[..., i] * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(radius)) for i in range(3)]
    al = Image.fromarray((a[..., 3] * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(radius))
    pmb = np.stack([np.asarray(c, dtype=np.float32) / 255.0 for c in chans], axis=-1)
    ab = np.asarray(al, dtype=np.float32) / 255.0
    rgb = np.where(ab[..., None] > 1e-4, pmb / np.maximum(ab[..., None], 1e-4), 0.0)
    out = np.concatenate([np.clip(rgb, 0, 1), np.clip(ab[..., None] * strength, 0, 1)], axis=-1)
    return Image.fromarray((out * 255).astype("uint8"), "RGBA")


def spaced_text(d, xy, text, fnt, fill, spacing):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=fnt, fill=fill)
        x += d.textlength(ch, font=fnt) + spacing


def text_width(d, text, fnt, spacing):
    return sum(d.textlength(c, font=fnt) + spacing for c in text) - spacing


def draw_arc_ring(d, cx, cy, r, start, sweep, width, fill, dash=None):
    box = [cx - r, cy - r, cx + r, cy + r]
    if dash is None:
        d.arc(box, start, start + sweep, fill=fill, width=width)
    else:
        a = start
        while a < start + sweep:
            d.arc(box, a, min(a + dash[0], start + sweep), fill=fill, width=width)
            a += dash[0] + dash[1]


# --------------------------------------------------------------------------- #
# wallpapers
# --------------------------------------------------------------------------- #
def wallpaper(p: dict, fonts: Path, W=2560, H=1440, S=2, hud: bool = True) -> Image.Image:
    rnd = random.Random(7)
    bg, accent, accent2 = hex_rgb(p["bg"]), hex_rgb(p["accent"]), hex_rgb(p["accent2"])
    w, h = W * S, H * S
    horizon = int(h * 0.60)

    # base gradient + horizon bloom
    img = Image.new("RGBA", (w, h), bg + (255,))
    g = Image.new("RGBA", (1, h))
    for y in range(h):
        t = y / h
        c = mix(mix(bg, (0, 0, 0), 0.55), mix(bg, accent, 0.10), min(1, t * 1.15))
        g.putpixel((0, y), c + (255,))
    img = g.resize((w, h))
    bloom = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(bloom).ellipse([w * 0.12, horizon - h * 0.10, w * 0.88, horizon + h * 0.10], fill=accent + (120,))
    img = Image.alpha_composite(img, glow(bloom, 90 * S))

    # stars
    stars = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stars)
    for _ in range(520):
        x, y = rnd.uniform(0, w), rnd.uniform(0, horizon * 0.95)
        r = rnd.choice([1, 1, 1, 2, 2, 3]) * S / 2
        a = int(rnd.uniform(40, 200) * (1 - y / horizon * 0.5))
        c = rnd.choice([(255, 255, 255), accent, accent2, (255, 255, 255)])
        sd.ellipse([x - r, y - r, x + r, y + r], fill=c + (a,))
    img = Image.alpha_composite(img, stars)

    # perspective grid floor
    grid = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid)
    vx = w / 2
    n = 36
    for i in range(-n, n + 1):
        bx = vx + i * (w * 0.075)
        col = accent2 if i % 6 == 0 else accent
        gd.line([(vx + (bx - vx) * 0.02, horizon), (bx, h)], fill=col + (150 if i % 6 == 0 else 95,), width=2 * S // 2 + 1)
    y, step = horizon, 6.0 * S
    k = 0
    while y < h:
        y += step
        step *= 1.20
        col = accent2 if k % 5 == 0 else accent
        gd.line([(0, y), (w, y)], fill=col + (int(60 + 120 * (y - horizon) / (h - horizon)),), width=max(1, S))
        k += 1
    # fade the grid toward the horizon and the bottom edge
    fade = Image.new("L", (w, h), 0)
    fd = ImageDraw.Draw(fade)
    for yy in range(horizon, h):
        t = (yy - horizon) / (h - horizon)
        fd.line([(0, yy), (w, yy)], fill=int(255 * min(1, t * 3.2) * (1 - 0.55 * t)))
    grid.putalpha(ImageChops.multiply(grid.split()[3], fade))
    img = Image.alpha_composite(img, glow(grid, 3 * S, 0.8))
    img = Image.alpha_composite(img, grid)

    # horizon line
    hl = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(hl).line([(w * 0.08, horizon), (w * 0.92, horizon)], fill=accent + (230,), width=2 * S)
    img = Image.alpha_composite(img, glow(hl, 6 * S, 1.6))
    img = Image.alpha_composite(img, hl)

    cx, cy = w // 2, int(h * 0.37)
    if hud:
        # HUD rings around the emblem
        hud = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        hd = ImageDraw.Draw(hud)
        for r, a, wd in ((330, 70, 2), (410, 50, 2), (520, 28, 2)):
            hd.ellipse([cx - r * S, cy - r * S, cx + r * S, cy + r * S], outline=accent + (a,), width=wd * S)
        draw_arc_ring(hd, cx, cy, 380 * S, 200, 70, 5 * S, accent + (230,))
        draw_arc_ring(hd, cx, cy, 380 * S, 20, 70, 5 * S, accent2 + (230,))
        draw_arc_ring(hd, cx, cy, 460 * S, 300, 90, 3 * S, accent + (170,), dash=(5, 4))
        draw_arc_ring(hd, cx, cy, 460 * S, 100, 90, 3 * S, accent2 + (170,), dash=(5, 4))
        for i in range(120):
            ang = math.radians(i * 3)
            r0, r1 = 548 * S, (566 if i % 5 == 0 else 556) * S
            hd.line([(cx + r0 * math.cos(ang), cy + r0 * math.sin(ang)),
                     (cx + r1 * math.cos(ang), cy + r1 * math.sin(ang))],
                    fill=(accent if i % 10 else accent2) + (140 if i % 5 == 0 else 70,), width=2 * S)
        img = Image.alpha_composite(img, glow(hud, 5 * S, 1.4))
        img = Image.alpha_composite(img, hud)


    # circuit traces in the corners
    tr = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    td = ImageDraw.Draw(tr)
    for ox, oy, sx, sy in ((0, 0, 1, 1), (w, 0, -1, 1), (0, h, 1, -1), (w, h, -1, -1)):
        for j in range(5):
            x, y = ox + sx * (60 + j * 46) * S, oy + sy * (40 + j * 30) * S
            pts = [(x, y)]
            for _ in range(rnd.randint(3, 5)):
                if rnd.random() < 0.5:
                    x += sx * rnd.randint(60, 220) * S
                else:
                    y += sy * rnd.randint(40, 160) * S
                pts.append((x, y))
            c = accent if j % 2 == 0 else accent2
            td.line(pts, fill=c + (60,), width=2 * S)
            ex, ey = pts[-1]
            td.ellipse([ex - 5 * S, ey - 5 * S, ex + 5 * S, ey + 5 * S], outline=c + (140,), width=2 * S)
    img = Image.alpha_composite(img, tr)

    if hud:
        # emblem + title (inside the rings)
        logo = Image.open(LOGO).convert("RGBA")
        ls = int(270 * S)
        logo = logo.resize((ls, ls), Image.LANCZOS)
        ey = cy - 90 * S
        halo = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(halo).ellipse([cx - 170 * S, ey - 170 * S, cx + 170 * S, ey + 170 * S], fill=accent + (90,))
        img = Image.alpha_composite(img, glow(halo, 60 * S))
        em = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        em.paste(logo, (cx - ls // 2, ey - ls // 2), logo)
        img = Image.alpha_composite(img, em)

        big = font(fonts, "oxanium", "Bold", 66 * S)
        sub = font(fonts, "jetbrains-mono", "Regular", 17 * S)
        title, s2 = "LINUX-C.O.S", "CYBER OFFENSIVE & DEFENSIVE SECURITY"
        meas = ImageDraw.Draw(img)
        tw = text_width(meas, title, big, 12 * S)
        ty = cy + 90 * S
        tl = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        spaced_text(ImageDraw.Draw(tl), ((w - tw) / 2, ty), title, big, accent + (255,), 12 * S)
        img = Image.alpha_composite(img, glow(tl, 12 * S, 1.2))
        d = ImageDraw.Draw(img)
        spaced_text(d, ((w - tw) / 2, ty), title, big, hex_rgb(p["fg"]) + (255,), 12 * S)
        sw = text_width(d, s2, sub, 5 * S)
        spaced_text(d, ((w - sw) / 2, ty + 100 * S), s2, sub, hex_rgb(p["dim"]) + (255,), 5 * S)


    # vignette
    vg = Image.new("L", (w, h), 0)
    ImageDraw.Draw(vg).ellipse([-w * 0.25, -h * 0.35, w * 1.25, h * 1.35], fill=255)
    vg = vg.filter(ImageFilter.GaussianBlur(w * 0.12))
    dark = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    dark.putalpha(vg.point(lambda v: 255 - v))
    img = Image.alpha_composite(img, dark)
    return img.convert("RGB").resize((W, H), Image.LANCZOS)


# --------------------------------------------------------------------------- #
# Plymouth boot animation (two-step theme: throbber-%04d.png + watermark.png)
# --------------------------------------------------------------------------- #
def plymouth(p: dict, out: Path, frames=72, size=440, S=3) -> None:
    out.mkdir(parents=True, exist_ok=True)
    accent, accent2 = hex_rgb(p["accent"]), hex_rgb(p["accent2"])
    c = size * S // 2

    def frame(i: int) -> Image.Image:
        th = 360.0 * i / frames
        lay = Image.new("RGBA", (size * S, size * S), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        d.ellipse([c - 150 * S, c - 150 * S, c + 150 * S, c + 150 * S], outline=accent + (45,), width=2 * S)
        for k in range(3):
            draw_arc_ring(d, c, c, 195 * S, th + k * 120, 62, 6 * S, accent + (255,))
        for k in range(2):
            draw_arc_ring(d, c, c, 170 * S, -th * 1.5 + k * 180, 44, 4 * S, accent2 + (255,))
        for t in range(72):
            ang = math.radians(t * 5)
            lit = max(0.0, 1 - ((t * 5 - th * 2) % 360) / 90.0)
            r0, r1 = 208 * S, (219 if t % 6 == 0 else 213) * S
            col = mix((40, 55, 90), accent, 0.25 + 0.75 * lit)
            d.line([(c + r0 * math.cos(ang), c + r0 * math.sin(ang)), (c + r1 * math.cos(ang), c + r1 * math.sin(ang))],
                   fill=col + (int(110 + 145 * lit),), width=2 * S)
        g = glow(lay, 7 * S, 1.5)
        return Image.alpha_composite(g, lay).resize((size, size), Image.LANCZOS)

    for old in out.glob("*.png"):
        old.unlink()
    for i in range(frames):
        frame(i).save(out / f"throbber-{i + 1:04d}.png", optimize=True)

    logo = Image.open(LOGO).convert("RGBA").resize((200, 200), Image.LANCZOS)
    wm = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    halo = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(halo).ellipse([size / 2 - 95, size / 2 - 95, size / 2 + 95, size / 2 + 95], fill=accent + (100,))
    wm = Image.alpha_composite(wm, glow(halo, 34))
    wm.paste(logo, (size // 2 - 100, size // 2 - 100), logo)
    wm.save(out / "watermark.png", optimize=True)


def boot_art(p: dict, fonts: Path) -> None:
    """GRUB (installed + live) and isolinux backgrounds, and the GRUB selection pixmaps."""
    accent = hex_rgb(p["accent"])
    logo_src = Image.open(LOGO).convert("RGBA")

    def compose(W: int, H: int, logo_px: int, title_px: int, sub_px: int | None, panel) -> Image.Image:
        S = 2 if W >= 1280 else 1
        im = wallpaper(p, fonts, W=W, H=H, S=S, hud=False).convert("RGBA")
        d = ImageDraw.Draw(im)
        lg = logo_src.resize((logo_px, logo_px), Image.LANCZOS)
        halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        top = int(H * 0.07)
        ImageDraw.Draw(halo).ellipse([W / 2 - logo_px, top - logo_px * 0.2, W / 2 + logo_px, top + logo_px * 1.2], fill=accent + (80,))
        im = Image.alpha_composite(im, glow(halo, logo_px * 0.35))
        im.paste(lg, ((W - logo_px) // 2, top), lg)
        big = font(fonts, "oxanium", "Bold", title_px)
        d = ImageDraw.Draw(im)
        tw = text_width(d, "LINUX-C.O.S", big, title_px // 6)
        ty = top + logo_px + int(title_px * 0.35)
        tl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        spaced_text(ImageDraw.Draw(tl), ((W - tw) / 2, ty), "LINUX-C.O.S", big, accent + (255,), title_px // 6)
        im = Image.alpha_composite(im, glow(tl, title_px * 0.2, 1.2))
        d = ImageDraw.Draw(im)
        spaced_text(d, ((W - tw) / 2, ty), "LINUX-C.O.S", big, hex_rgb(p["fg"]) + (255,), title_px // 6)
        if sub_px:
            sf = font(fonts, "jetbrains-mono", "Regular", sub_px)
            s2 = "CYBER OFFENSIVE & DEFENSIVE SECURITY"
            sw = text_width(d, s2, sf, sub_px // 3)
            spaced_text(d, ((W - sw) / 2, ty + title_px * 1.35), s2, sf, hex_rgb(p["dim"]) + (255,), sub_px // 3)
        if panel:
            x0, y0, x1, y1 = panel
            pl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            pd = ImageDraw.Draw(pl)
            pd.rounded_rectangle([x0, y0, x1, y1], radius=18, fill=hex_rgb(p["bg"]) + (190,), outline=accent + (120,), width=2)
            im = Image.alpha_composite(im, pl)
        return im.convert("RGB")

    grub = compose(1920, 1080, 150, 56, 18, (int(1920 * 0.28), int(1080 * 0.40), int(1920 * 0.72), int(1080 * 0.84)))
    theme = INC / "usr/share/grub/themes/linux-cos"
    theme.mkdir(parents=True, exist_ok=True)
    grub.save(theme / "background.png", optimize=True)
    live = INC.parent / "includes.binary/boot/grub"
    live.mkdir(parents=True, exist_ok=True)
    grub.save(live / "splash.png", optimize=True)
    iso = INC.parent / "includes.binary/isolinux"
    iso.mkdir(parents=True, exist_ok=True)
    compose(640, 480, 84, 26, None, None).save(iso / "splash.png", optimize=True)
    # selection highlight (9-slice, 1px border): translucent accent fill, solid accent edges
    for name in ("c",):
        Image.new("RGBA", (1, 1), accent + (70,)).save(theme / f"select_{name}.png")
    for name in ("n", "s", "e", "w", "ne", "nw", "se", "sw"):
        Image.new("RGBA", (1, 1), accent + (230,)).save(theme / f"select_{name}.png")
    print("boot art done")


def fetch_logo() -> None:
    """The shield as truecolor half-block text, for `fastfetch` (no image protocol needed)."""
    w, h = 30, 30
    im = Image.open(LOGO).convert("RGBA")
    bbox = im.getbbox()
    im = im.crop(bbox).resize((w, h), Image.LANCZOS)
    px = im.load()
    out = []
    for y in range(0, h, 2):
        row = ""
        for x in range(w):
            top, bot = px[x, y], px[x, y + 1]
            to, bo = top[3] > 90, bot[3] > 90
            if to and bo:
                row += f"\x1b[38;2;{top[0]};{top[1]};{top[2]};48;2;{bot[0]};{bot[1]};{bot[2]}m\u2580\x1b[0m"
            elif to:
                row += f"\x1b[38;2;{top[0]};{top[1]};{top[2]}m\u2580\x1b[0m"
            elif bo:
                row += f"\x1b[38;2;{bot[0]};{bot[1]};{bot[2]}m\u2584\x1b[0m"
            else:
                row += " "
        out.append(row)
    dst = INC / "etc/skel/.config/fastfetch"
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "logo.ansi").write_text("\n".join(out) + "\n", encoding="utf-8")
    old = dst / "logo.txt"
    if old.exists():
        old.unlink()
    print("fastfetch logo done")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fonts", type=Path, required=True)
    ap.add_argument("--only", choices=["wallpapers", "plymouth", "boot", "logo"])
    a = ap.parse_args()
    pal = json.loads((SHARE / "palettes.json").read_text())
    if a.only in (None, "wallpapers"):
        BG_DIR.mkdir(parents=True, exist_ok=True)
        for mode, p in pal.items():
            im = wallpaper(p, a.fonts)
            im.save(BG_DIR / f"{mode}.jpg", quality=90, optimize=True, progressive=True)
            wallpaper(p, a.fonts, hud=False).save(BG_DIR / f"{mode}-base.jpg", quality=90, optimize=True, progressive=True)
            print("wallpaper", mode, (BG_DIR / f"{mode}.jpg").stat().st_size // 1024, "KB")
    if a.only in (None, "logo"):
        fetch_logo()
    if a.only in (None, "boot"):
        boot_art(pal["dual"], a.fonts)
    if a.only in (None, "plymouth"):
        plymouth(pal["dual"], SHARE / "plymouth")
        print("plymouth frames done")


if __name__ == "__main__":
    main()
