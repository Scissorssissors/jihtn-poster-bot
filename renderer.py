"""Playwright renderer: pre-warmed Chromium, embedded fonts, measured
fit-to-box Tamil typography, layout recipes and a pixel contrast retry."""

import base64
import random
from pathlib import Path
from playwright.async_api import async_playwright

from tamil_text import to_html, grapheme_count, word_count, size_class
from palette import contrast_in_region

BASE = Path(__file__).parent
ASSETS = BASE / "assets"
TEMPLATE = (BASE / "template.html").read_text(encoding="utf-8")


def _data_uri(path: Path, mime: str) -> str:
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def _bytes_uri(data: bytes, mime: str = "image/jpeg") -> str:
    return f"data:{mime};base64," + base64.b64encode(data).decode()


FONT_ANEK = _data_uri(ASSETS / "fonts" / "AnekTamil.ttf", "font/ttf")
FONT_NOTO = _data_uri(ASSETS / "fonts" / "NotoSansTamil.ttf", "font/ttf")
FRAME = _data_uri(ASSETS / "frame.png", "image/png")
_logo = ASSETS / "logo.png"
LOGO = _data_uri(_logo, "image/png") if _logo.exists() else \
    "data:image/svg+xml;base64," + base64.b64encode(
        b'<svg xmlns="http://www.w3.org/2000/svg" width="148" height="148"><circle cx="74" cy="74" r="70" fill="#143e6d"/>'
        b'<text x="74" y="92" font-size="52" text-anchor="middle" fill="#fff" font-family="sans-serif" font-weight="700">JIH</text></svg>'
    ).decode()

# starting font size per size class; fit loop may step it down
START_SIZE = {"hero": 60, "large": 50, "medium": 41, "small": 34, "dense": 30}
MIN_SIZE = 26
LAYOUTS_BY_CLASS = {
    "hero": ["layout-hero", "layout-center", "layout-frame", "layout-rule"],
    "large": ["layout-hero", "layout-center", "layout-frame", "layout-glass", "layout-rule"],
    "medium": ["layout-center", "layout-glass", "layout-frame", "layout-bottom"],
    "small": ["layout-center", "layout-glass", "layout-bottom"],
    "dense": ["layout-center", "layout-glass"],
}
# glass panels & bottom layouts read fine on light tones too; otherwise keep the palette's tone
CONTRAST_TARGET = 4.6

_PW = None
_BROWSER = None


async def init_browser():
    global _PW, _BROWSER
    if _BROWSER:
        return
    _PW = await async_playwright().start()
    _BROWSER = await _PW.chromium.launch(args=[
        "--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage",
        "--font-render-hinting=none", "--disable-font-subpixel-positioning",
    ])


async def close_browser():
    global _PW, _BROWSER
    if _BROWSER:
        await _BROWSER.close()
    if _PW:
        await _PW.stop()
    _PW = _BROWSER = None


def choose_layout(text: str, seed: int, forced: str | None = None) -> str:
    if forced:
        return f"layout-{forced}"
    return random.Random(seed + 7).choice(LAYOUTS_BY_CLASS[size_class(text)])


_FIT_JS = """
([minSize]) => {
  const v = document.getElementById('verse');
  const wrap = v.parentElement;
  const cs = getComputedStyle(wrap);
  const avail = wrap.clientHeight - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom) - 40; // ornament
  let size = parseFloat(getComputedStyle(v).fontSize);
  const fits = () => v.getBoundingClientRect().height <= avail && v.scrollWidth <= v.clientWidth + 1;
  while (!fits() && size > minSize) { size -= 1; v.style.fontSize = size + 'px'; }
  // widow control: if last line is a single short word, shrink one more step (max 3 tries)
  const lineH = parseFloat(getComputedStyle(v).lineHeight);
  const lines = Math.round(v.getBoundingClientRect().height / lineH);
  let tries = 0;
  const words = v.innerText.trim().split(/\\s+/);
  while (lines > 1 && words.length > 4 && tries < 3) {
    const r = document.createRange(); r.selectNodeContents(v);
    const rects = Array.from(r.getClientRects());
    const lastTop = Math.max(...rects.map(x => x.top));
    const lastW = rects.filter(x => Math.abs(x.top - lastTop) < 2).reduce((a, x) => a + x.width, 0);
    if (lastW > v.clientWidth * 0.28) break;
    size -= 1; v.style.fontSize = size + 'px'; tries++;
    if (size <= minSize) break;
  }
  const b = v.getBoundingClientRect();
  const card = document.querySelector('.card').getBoundingClientRect();
  return {size, box: [b.left, b.top, b.right, b.bottom], lines};
}
"""


async def render_poster(*, image_bytes: bytes, verse: str, surah_ref: str, palette: dict,
                        seed: int, layout: str | None = None, output_path: str | Path) -> dict:
    """Render and save PNG. Returns info dict (font size, layout, contrast, retried)."""
    await init_browser()
    layout_cls = choose_layout(verse, seed, layout)
    text_color = palette["text_color"]
    size = START_SIZE[size_class(verse)]

    def build(boost: float, tc: str, shadow: str) -> str:
        h = TEMPLATE
        for k, v in {
            "{{FONT_ANEK}}": FONT_ANEK, "{{FONT_NOTO}}": FONT_NOTO, "{{FRAME_DATA_URI}}": FRAME,
            "{{IMAGE_DATA_URI}}": _bytes_uri(image_bytes), "{{VERSE_HTML}}": to_html(verse),
            "{{SURAH_REF}}": surah_ref, "{{GRADIENT_CSS}}": palette["gradient"], "{{TEXT_COLOR}}": tc,
            "{{TEXT_SHADOW}}": shadow, "{{ACCENT}}": palette["accent"], "{{LAYOUT_CLASS}}": layout_cls,
            "{{FONT_SIZE}}": str(size), "{{BOOST}}": f"{boost:.2f}",
        }.items():
            h = h.replace(k, v)
        return h

    page = await _BROWSER.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
    info = {"layout": layout_cls, "graphemes": grapheme_count(verse), "words": word_count(verse), "retried": 0}
    try:
        boost, tc, shadow = 0.0, text_color, palette["shadow"]
        for attempt in range(3):
            await page.set_content(build(boost, tc, shadow), wait_until="load")
            await page.evaluate("document.fonts.ready")
            fit = await page.evaluate(_FIT_JS, [MIN_SIZE])
            # measure contrast on the background only (text hidden), then capture the real poster
            await page.evaluate("document.getElementById('verse').style.visibility='hidden'")
            bg_png = await page.screenshot(type="png")
            await page.evaluate("document.getElementById('verse').style.visibility='visible'")
            png = await page.screenshot(type="png")
            box = tuple(int(x) for x in fit["box"])
            box = (max(0, box[0]), max(0, box[1]), min(1080, box[2]), min(1350, box[3]))
            ratio = contrast_in_region(bg_png, box, tc)
            info.update(font_size=fit["size"], lines=fit["lines"], contrast=round(ratio, 2))
            if ratio >= CONTRAST_TARGET or attempt == 2:
                break
            # retry: darken overlay; if the palette was light and still fails, switch to white text
            info["retried"] = attempt + 1
            if tc != "#ffffff" and ratio < 3.0:
                tc, shadow = "#ffffff", "0 3px 14px rgba(0,0,0,0.65), 0 1px 3px rgba(0,0,0,0.6)"
                boost = 0.35
            else:
                boost += 0.22
        Path(output_path).write_bytes(png)
    finally:
        await page.close()
    return info
