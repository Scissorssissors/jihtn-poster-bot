"""Palette engine: dominant colours from the background image -> gradient
overlay harmonised with the picture, plus text colour/shadow and a pixel
contrast check on the final screenshot."""

import colorsys
import io
import random
from PIL import Image

MOOD_HUES = {  # fallback hue anchors (degrees) per mood if image is too grey
    "warm": 35, "earth": 25, "cosmic": 265, "solemn": 220, "ember": 15, "calm": 205,
    "navy": 215, "gold": 42, "sacred": 230, "green": 130, "teal": 185, "luminous": 45,
    "midnight": 235, "rose": 345, "stone": 210, "sand": 38, "slate": 210,
    "emerald": 150, "royal": 40,
}


def _hsl_to_hex(h, s, l):
    r, g, b = colorsys.hls_to_rgb((h % 360) / 360, max(0, min(1, l)), max(0, min(1, s)))
    return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))


def _rgba(h, s, l, a):
    r, g, b = colorsys.hls_to_rgb((h % 360) / 360, max(0, min(1, l)), max(0, min(1, s)))
    return f"rgba({int(r*255)},{int(g*255)},{int(b*255)},{a:.2f})"


def dominant_hue(image_bytes: bytes, fallback_hue: float) -> tuple[float, float, float]:
    """Return (hue, saturation, lightness) of the dominant saturated colour."""
    try:
        im = Image.open(io.BytesIO(image_bytes)).convert("RGB").resize((64, 64))
        q = im.quantize(colors=8, method=Image.Quantize.MEDIANCUT).convert("RGB")
        counts = sorted(q.getcolors(64 * 64), reverse=True)
        best, best_score = None, -1
        avg_l = 0
        for n, (r, g, b) in counts:
            h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
            avg_l += l * n
            score = n * (0.3 + s)
            if score > best_score:
                best, best_score = (h * 360, s, l), score
        avg_l /= 64 * 64
        h, s, l = best
        if s < 0.12:
            h = fallback_hue
        return h, s, avg_l
    except Exception:
        return fallback_hue, 0.5, 0.4


def build_palette(image_bytes: bytes, mood: str, tone_pref: str, seed: int) -> dict:
    """tone_pref: 'dark' overlay + white text, or 'light' overlay + navy text.
    Returns dict(gradient, text_color, shadow, tone, accent)."""
    rng = random.Random(seed)
    h, s, img_l = dominant_hue(image_bytes, MOOD_HUES.get(mood, 220))

    # harmony choice -> second hue
    harmony = rng.choice(["analogous", "analogous", "complement", "split", "duotone"])
    if harmony == "analogous":
        h2 = h + rng.choice([-30, 30])
    elif harmony == "complement":
        h2 = h + 180
    elif harmony == "split":
        h2 = h + rng.choice([150, 210])
    else:
        h2 = h + rng.choice([-15, 15])
    sat = max(0.35, min(0.75, s + 0.1))

    # Very bright images force a dark overlay for readability; light tone only when image is mid/light.
    tone = tone_pref if (tone_pref == "light" and img_l > 0.45) else "dark"

    recipe = rng.choice(["wash", "duotone", "anchor", "diagonal", "radial"])
    if tone == "dark":
        c1 = _rgba(h, sat, 0.14, 0.92); c2 = _rgba(h2, sat, 0.22, 0.55); c3 = _rgba(h, sat, 0.10, 0.0)
        if recipe == "wash":
            g = f"linear-gradient(180deg, {c1} 0%, {c2} 45%, {c3} 100%)"
        elif recipe == "duotone":
            g = f"linear-gradient(160deg, {c1} 0%, {_rgba(h2, sat, 0.18, 0.80)} 50%, {c3} 100%)"
        elif recipe == "anchor":
            g = f"linear-gradient(180deg, {_rgba(h, sat, 0.08, 0.96)} 0%, {c2} 55%, {c3} 100%)"
        elif recipe == "diagonal":
            g = f"linear-gradient(200deg, {c1} 0%, {_rgba(h2, sat, 0.20, 0.70)} 40%, {c3} 100%)"
        else:
            g = f"radial-gradient(120% 90% at 50% 10%, {c1} 0%, {c2} 55%, {c3} 100%)"
        text = "#ffffff"
        shadow = "0 3px 14px rgba(0,0,0,0.65), 0 1px 3px rgba(0,0,0,0.6)"
        accent = _hsl_to_hex(h2, sat, 0.72)
    else:
        c1 = _rgba(h, 0.25, 0.97, 0.94); c2 = _rgba(h2, 0.30, 0.93, 0.70); c3 = _rgba(h, 0.2, 0.95, 0.0)
        if recipe == "radial":
            g = f"radial-gradient(120% 90% at 50% 10%, {c1} 0%, {c2} 55%, {c3} 100%)"
        else:
            g = f"linear-gradient(180deg, {c1} 0%, {c2} 50%, {c3} 100%)"
        text = "#0f2a4a"
        shadow = "0 2px 10px rgba(255,255,255,0.75)"
        accent = _hsl_to_hex(h, 0.5, 0.35)

    return {"gradient": g, "text_color": text, "shadow": shadow, "tone": tone,
            "accent": accent, "hue": round(h), "recipe": recipe, "harmony": harmony}


def _luminance(rgb):
    def ch(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast_in_region(png_bytes: bytes, box: tuple, text_color: str) -> float:
    """Average contrast ratio of the text colour against the background pixels in box.
    Measures the real rendered screenshot, so it accounts for image + gradient."""
    im = Image.open(io.BytesIO(png_bytes)).convert("RGB").crop(box)
    im = im.resize((max(1, im.width // 8), max(1, im.height // 8)))
    tc = tuple(int(text_color.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
    lt = _luminance(tc)
    px = list(im.getdata())
    # use the brighter (for white text) / darker (for navy) 30% of pixels: worst case region
    lums = sorted(_luminance(p) for p in px)
    worst = lums[int(len(lums) * 0.7):] if lt > 0.5 else lums[: max(1, int(len(lums) * 0.3))]
    lb = sum(worst) / len(worst)
    hi, lo = max(lt, lb), min(lt, lb)
    return (hi + 0.05) / (lo + 0.05)
