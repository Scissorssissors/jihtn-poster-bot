"""Local preview: render sample verses to ./output and print a summary.
Usage:  python preview.py            (default sample set)
        python preview.py 88:11 2:255 55:13
        python preview.py 88:11 --layout glass --tone light --theme night --retry
"""

import sys
import asyncio
from pipeline import make_poster
from renderer import close_browser
from quran import parse_reference

SAMPLES = ["88:11", "30:22", "2:255", "55:13", "94:5", "103:1", "24:35", "3:139", "2:286", "67:3"]


async def main(argv):
    refs = [a for a in argv if parse_reference(a)]
    refs = refs or SAMPLES
    layout = argv[argv.index("--layout") + 1] if "--layout" in argv else None
    tone = argv[argv.index("--tone") + 1] if "--tone" in argv else None
    theme = argv[argv.index("--theme") + 1] if "--theme" in argv else None
    variant = 1 if "--retry" in argv else 0
    try:
        for r in refs:
            s, a = parse_reference(r)
            try:
                path, info = await make_poster(s, a, variant=variant, layout=layout, tone=tone, theme_override=theme)
                print(f"{r:>7}  {info['theme']:<11} {info['layout']:<14} font={info['font_size']} lines={info['lines']} "
                      f"contrast={info['contrast']} src={info['source']:<12} {info['seconds']}s -> {path.name}")
            except Exception as e:
                print(f"{r:>7}  FAILED: {e}")
    finally:
        await close_browser()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
