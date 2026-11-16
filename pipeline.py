"""One call: reference -> finished poster PNG. Used by bot.py and preview.py."""

import asyncio
import hashlib
import random
import time
from pathlib import Path

from quran import QURAN_DIRECTORY, fetch_verse
from themes import SCENES, pick_theme, build_prompt, seed_for, STYLE_SUFFIX
from imagegen import generate_background
from palette import build_palette
from renderer import render_poster

OUT_DIR = Path(__file__).parent / "output"
OUT_DIR.mkdir(exist_ok=True)


async def make_poster(surah: int, ayah: int, *, variant: int = 0, layout: str | None = None,
                      tone: str | None = None, theme_override: str | None = None,
                      progress=None) -> tuple[Path, dict]:
    """progress(stage: str) is awaited at each stage for Telegram status edits."""
    t0 = time.time()

    async def say(stage):
        if progress:
            try:
                await progress(stage)
            except Exception:
                pass

    await say("fetch")
    verse, ref = await fetch_verse(surah, ayah)

    default_theme = QURAN_DIRECTORY[surah][2]
    theme = theme_override if theme_override in SCENES else pick_theme(verse, default_theme)
    seed = seed_for(surah, ayah, variant)
    prompt = build_prompt(theme, seed)

    await say("image")
    image_bytes, source = await generate_background(prompt, theme, seed)

    await say("style")
    tone_pref = tone or SCENES[theme]["tone"]
    palette = build_palette(image_bytes, SCENES[theme]["mood"], tone_pref, seed)

    out = OUT_DIR / f"{surah}_{ayah}_v{variant}.png"
    info = await render_poster(image_bytes=image_bytes, verse=verse, surah_ref=ref,
                               palette=palette, seed=seed, layout=layout, output_path=out)
    info.update(theme=theme, source=source, seed=seed, prompt=prompt, verse=verse, ref=ref,
                tone=palette["tone"], recipe=palette["recipe"], seconds=round(time.time() - t0, 1))
    return out, info


# ---------------------------------------------------------------------------
# Custom text poster (no Quran fetch — user supplies text + optional heading)
# ---------------------------------------------------------------------------

def _custom_seed(text: str, variant: int = 0) -> int:
    h = hashlib.md5(f"custom:{text}:{variant}".encode()).hexdigest()
    return int(h[:8], 16)


def _pick_image_prompt(image_desc: str | None, theme: str, seed: int) -> str:
    if image_desc:
        return image_desc + STYLE_SUFFIX
    return build_prompt(theme, seed)


async def make_custom_poster(*, text: str, heading: str = "",
                             theme: str | None = None, image_desc: str | None = None,
                             layout: str | None = None, tone: str | None = None,
                             variant: int = 0, progress=None) -> tuple[Path, dict]:
    t0 = time.time()

    async def say(stage):
        if progress:
            try: await progress(stage)
            except Exception: pass

    theme = theme if theme and theme in SCENES else "creation"
    seed = _custom_seed(text, variant)
    prompt = _pick_image_prompt(image_desc, theme, seed)

    await say("image")
    image_bytes, source = await generate_background(prompt, theme, seed)

    await say("style")
    tone_pref = tone or SCENES[theme]["tone"]
    palette = build_palette(image_bytes, SCENES[theme]["mood"], tone_pref, seed)

    surah_ref = heading or ""
    out = OUT_DIR / f"custom_{seed}_{variant}.png"
    info = await render_poster(image_bytes=image_bytes, verse=text, surah_ref=surah_ref,
                               palette=palette, seed=seed, layout=layout, output_path=out)
    info.update(theme=theme, source=source, seed=seed, prompt=prompt, verse=text, ref=surah_ref,
                heading=heading, image_desc=image_desc or "",
                tone=palette["tone"], recipe=palette["recipe"], seconds=round(time.time() - t0, 1))
    return out, info
