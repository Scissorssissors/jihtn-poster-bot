"""Telegram bot: send '88:11' -> branded poster. Free-only stack.

Commands:
  88:11              render the verse (same verse = same design, cached)
  88:11 retry        new background / layout for the same verse
  88:11 dark|light   force text tone
  88:11 glass|hero|center|bottom|frame|rule   force a layout
  88:11 theme=night  force a scene family (see /themes)
  /themes            list scene families
"""

import os
import re
import asyncio
import http.server
import socketserver
import threading
import logging
from collections import defaultdict

# load .env (simple, no dependency) before anything reads os.environ
_env = __import__("pathlib").Path(__file__).parent / ".env"
if _env.exists():
    for _line in _env.read_text(encoding="utf-8").splitlines():
        _line = _line.split("#", 1)[0].strip()
        if "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

from telegram import Update
from telegram.error import Conflict
from telegram.request import HTTPXRequest
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from quran import parse_reference
from themes import SCENES
from pipeline import make_poster
from renderer import init_browser

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("bot")
logging.getLogger("httpx").setLevel(logging.WARNING)   # never print the token-bearing URLs
logging.getLogger("httpcore").setLevel(logging.WARNING)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
MAX_PARALLEL = int(os.environ.get("MAX_PARALLEL", "2"))

_variants: dict[tuple[int, int], int] = defaultdict(int)   # retry counter per verse
_sem = asyncio.Semaphore(MAX_PARALLEL)

STAGES = {
    "fetch": "📖 வசனம் பெறப்படுகிறது...",
    "image": "🎨 AI பின்னணி உருவாக்கப்படுகிறது... (சில நொடிகள்)",
    "style": "✨ வடிவமைப்பு & எழுத்து அமைக்கப்படுகிறது...",
}

LAYOUTS = {"glass", "hero", "center", "bottom", "frame", "rule"}


async def start(update: Update, _: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "அஸ்ஸலாமு அலைக்கும்! 🌙\n\nஸூரா:வசன எண்ணை அனுப்புங்கள். உதாரணம்: 88:11\n\n"
        "கூடுதல்:\n• 88:11 retry  – புதிய வடிவமைப்பு\n• 88:11 dark / light\n"
        "• 88:11 glass / hero / center / bottom / frame / rule\n• 88:11 theme=night\n• /themes"
    )


async def themes_cmd(update: Update, _: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Themes: " + ", ".join(sorted(SCENES)))


async def handle(update: Update, _: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    log.info("message from %s: %r", update.effective_user.id if update.effective_user else "?", text[:40])
    m = re.match(r"^\s*(\d{1,3}\s*[:\-/.\s]\s*\d{1,3})(.*)$", text)
    if not m:
        await update.message.reply_text("❌ தவறான வடிவம்! உதாரணம்: 88:11")
        return
    ref = parse_reference(m.group(1))
    opts = m.group(2).lower().split()
    surah, ayah = ref

    layout = next((o for o in opts if o in LAYOUTS), None)
    tone = next((o for o in opts if o in ("dark", "light")), None)
    theme = next((o[6:] for o in opts if o.startswith("theme=")), None)
    key = (surah, ayah)
    if "retry" in opts or "new" in opts:
        _variants[key] += 1
    variant = _variants[key]

    status = await update.message.reply_text("⏳ தயாராகிறது...")

    async def progress(stage):
        try:
            await status.edit_text(STAGES.get(stage, stage))
        except Exception:
            pass

    try:
        async with _sem:
            path, info = await make_poster(surah, ayah, variant=variant, layout=layout,
                                           tone=tone, theme_override=theme, progress=progress)
        caption = f"{info['ref']}\n🎨 {info['theme']} · {info['layout'][7:]} · {info['seconds']}s"
        with open(path, "rb") as f:
            await update.message.reply_document(document=f, filename=path.name, caption=caption)
        try:
            await status.delete()
        except Exception:
            pass
        log.info("OK %s:%s %s", surah, ayah, {k: info[k] for k in ("theme", "source", "font_size", "contrast", "seconds")})
    except ValueError as e:
        await status.edit_text(str(e))
    except Exception as e:
        log.exception("render failed")
        await status.edit_text(f"⚠️ பிழை: {type(e).__name__}. மீண்டும் முயற்சிக்கவும்.")


# ---- keep-alive HTTP server for Render + UptimeRobot ----
class HealthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"Bot is Healthy and Live!")
    def do_HEAD(self):
        self.send_response(200); self.end_headers()
    def log_message(self, *a): pass


def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), HealthHandler) as httpd:
        httpd.serve_forever()


async def on_error(update, context):
    err = context.error
    if isinstance(err, Conflict):
        log.error("Another instance is polling this token (stop the old Render/other bot). Retrying...")
    else:
        log.error("Unhandled error: %r", err)


async def post_init(app):
    await init_browser()
    log.info("Chromium pre-warmed")


def main():
    if not TELEGRAM_TOKEN:
        raise SystemExit("Set TELEGRAM_TOKEN env var")
    threading.Thread(target=run_health_server, daemon=True).start()
    req = HTTPXRequest(connect_timeout=20, read_timeout=60, write_timeout=60, pool_timeout=20)
    app = (ApplicationBuilder().token(TELEGRAM_TOKEN).request(req)
           .concurrent_updates(True).post_init(post_init).build())
    app.add_error_handler(on_error)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("themes", themes_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.run_polling(drop_pending_updates=False)


if __name__ == "__main__":
    main()
