"""Free AI background generation with a provider chain and disk cache.

Chain (all free):
  1. Pollinations.ai  - no API key at all (FLUX)           ~3-8 s
  2. Hugging Face Inference API (FLUX.1-schnell) - free token optional
  3. Curated stock image from assets/stock/<theme>/ or assets/stock/
Nothing here raises: you always get image bytes."""

import os
import re
import base64
import asyncio
import hashlib
import random
import urllib.parse
from pathlib import Path
import httpx
import logging
log = logging.getLogger("imagegen")

BASE = Path(__file__).parent
CACHE_DIR = BASE / "cache"
STOCK_DIR = BASE / "assets" / "stock"
CACHE_DIR.mkdir(exist_ok=True)

HF_TOKEN = os.environ.get("HF_TOKEN", "").strip()
POLLINATIONS_TOKEN = os.environ.get("POLLINATIONS_TOKEN", "").strip()  # optional, raises rate limit
IMAGE_TIMEOUT = float(os.environ.get("IMAGE_TIMEOUT", "90"))
CF_ACCOUNT_ID = os.environ.get("CF_ACCOUNT_ID", "").strip()
CF_API_TOKEN = os.environ.get("CF_API_TOKEN", "").strip()

# Card is 1004x1070 -> generate close to that ratio (multiples of 16 keep FLUX happy)
GEN_W, GEN_H = 1024, 1088


def _cache_path(prompt: str, seed: int) -> Path:
    key = hashlib.sha1(f"{prompt}|{seed}".encode()).hexdigest()[:20]
    return CACHE_DIR / f"{key}.jpg"


def _looks_like_image(data: bytes) -> bool:
    return len(data) > 8_000 and (data[:3] == b"\xff\xd8\xff" or data[:8] == b"\x89PNG\r\n\x1a\n" or data[:4] == b"RIFF")


async def _pollinations(client: httpx.AsyncClient, prompt: str, seed: int) -> bytes | None:
    q = urllib.parse.quote(prompt)
    url = (f"https://image.pollinations.ai/prompt/{q}?width={GEN_W}&height={GEN_H}"
           f"&seed={seed % 1_000_000}&model=flux&nologo=true")
    headers = {"Authorization": f"Bearer {POLLINATIONS_TOKEN}"} if POLLINATIONS_TOKEN else {}
    waited = 0.0
    for attempt in range(4):
        try:
            r = await client.get(url, headers=headers)
        except Exception as e:
            log.warning("pollinations error: %s", e)
            return None
        if r.status_code == 200 and _looks_like_image(r.content):
            return _strip_watermark(r.content)
        log.warning("pollinations %s: %s", r.status_code, r.text[:600])
        if r.status_code == 402 and waited < 100:
            # free tier: 1 image / 45 s per IP. Wait out the window and retry.
            m = re.search(r"Retry after (\d+)s", r.text)
            wait = (int(m.group(1)) if m else 45) + 3
            waited += wait
            await asyncio.sleep(wait)
            continue
        return None
    return None


async def _cloudflare(client: httpx.AsyncClient, prompt: str, seed: int) -> bytes | None:
    """Cloudflare Workers AI free tier (10k neurons/day) - FLUX.1 schnell."""
    if not (CF_ACCOUNT_ID and CF_API_TOKEN):
        return None
    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/@cf/black-forest-labs/flux-1-schnell"
    try:
        r = await client.post(url, headers={"Authorization": f"Bearer {CF_API_TOKEN}"},
                              json={"prompt": prompt, "steps": 4, "seed": seed % 2_000_000})
        if r.status_code == 200:
            b64 = r.json().get("result", {}).get("image")
            if b64:
                data = base64.b64decode(b64)
                if _looks_like_image(data):
                    return data
    except Exception:
        pass
    return None


async def _huggingface(client: httpx.AsyncClient, prompt: str, seed: int) -> bytes | None:
    if not HF_TOKEN:
        return None
    url = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
    try:
        r = await client.post(
            url,
            headers={"Authorization": f"Bearer {HF_TOKEN}", "Accept": "image/jpeg"},
            json={"inputs": prompt,
                  "parameters": {"width": GEN_W, "height": GEN_H, "num_inference_steps": 4, "seed": seed}},
        )
        if r.status_code == 200 and _looks_like_image(r.content):
            return r.content
    except Exception:
        pass
    return None


def _strip_watermark(data: bytes) -> bytes:
    """Free-tier Pollinations stamps a logo bottom-right: crop the bottom 8% away."""
    try:
        from PIL import Image
        import io
        im = Image.open(io.BytesIO(data)).convert("RGB")
        w, h = im.size
        im = im.crop((0, 0, w, int(h * 0.92)))
        buf = io.BytesIO(); im.save(buf, "JPEG", quality=92)
        return buf.getvalue()
    except Exception:
        return data


def stock_image(theme: str, seed: int) -> bytes:
    rng = random.Random(seed)
    candidates = []
    themed = STOCK_DIR / theme
    if themed.is_dir():
        candidates = [p for p in themed.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")]
    if not candidates:
        candidates = [p for p in STOCK_DIR.glob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")]
    if not candidates:
        # last resort: a generated gradient PNG so rendering never fails
        from PIL import Image
        import io
        im = Image.new("RGB", (GEN_W, GEN_H), (18, 32, 56))
        buf = io.BytesIO(); im.save(buf, "JPEG", quality=85)
        return buf.getvalue()
    return rng.choice(candidates).read_bytes()


async def generate_background(prompt: str, theme: str, seed: int, progress=None) -> tuple[bytes, str]:
    """Returns (image_bytes, source) where source in {'cache','pollinations','huggingface','stock'}."""
    cp = _cache_path(prompt, seed)
    if cp.exists():
        return cp.read_bytes(), "cache"

    async with httpx.AsyncClient(timeout=IMAGE_TIMEOUT, follow_redirects=True) as client:
        for name, fn in (("huggingface", _huggingface), ("cloudflare", _cloudflare), ("pollinations", _pollinations)):
            if progress:
                await progress(name)
            data = await fn(client, prompt, seed)
            if data:
                try:
                    cp.write_bytes(data)
                except Exception:
                    pass
                return data, name
    return stock_image(theme, seed), "stock"
