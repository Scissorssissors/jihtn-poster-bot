# Quran Poster Bot (JIH Tamil Nadu & Puducherry)

Send `88:11` to the Telegram bot and get a 1080x1350 (Instagram 4:5) branded poster with an
AI-generated halal background, verse-matched colours, and precise Tamil typography.
Everything in the stack is free.

## Files
| file | job |
|---|---|
| `bot.py` | Telegram bot, progress messages, keep-alive HTTP server on `PORT` |
| `pipeline.py` | reference -> verse -> theme -> image -> palette -> PNG |
| `quran.py` | 114-surah table, async verse fetch (two free sources), Tamil surah grammar |
| `themes.py` | 24 scene families, Tamil keyword classifier, halal prompt builder |
| `imagegen.py` | free providers: Hugging Face, Cloudflare Workers AI, Pollinations, stock fallback. Disk cache |
| `palette.py` | dominant colour of the image -> harmonised gradient, text colour, pixel contrast check |
| `renderer.py` | pre-warmed Chromium, embedded fonts, fit-to-box font sizing, 6 layouts, contrast retry |
| `template.html` | card HTML/CSS placed over the frame |
| `preview.py` | render samples locally into `output/` |
| `assets/fonts/` | Anek Tamil + Noto Sans Tamil (embedded as base64, no network needed) |
| `assets/frame.png` | the master frame (logo, header, footer). Every poster is drawn on top of it; the card sits in the blank band (rows 214-1266) |
| `assets/stock/` | optional fallback photos (`assets/stock/<theme>/*.jpg` or flat) |

## Run locally
```
pip install -r requirements.txt
playwright install chromium
python preview.py                 # ten sample posters -> output/
python preview.py 2:255 --layout glass --tone light
set TELEGRAM_TOKEN=...  && python bot.py
```

## Deploy on Render (free)
1. Push this folder to GitHub.
2. Render -> New Web Service -> Docker. `render.yaml` is included.
3. Env vars: `TELEGRAM_TOKEN` (required). Optional free backups: `HF_TOKEN`,
   `CF_ACCOUNT_ID` + `CF_API_TOKEN`, `POLLINATIONS_TOKEN`.
4. Point UptimeRobot at the service URL (GET `/`).

## Free image provider notes
* **Pollinations** needs no key: 1 image / 45 s per IP. The bot waits out the window
  automatically (the Telegram status message shows progress). A free Pollinations
  token removes the wait.
* **Hugging Face** free token: used first when set (FLUX.1-schnell, ~3 s).
* **Cloudflare Workers AI** free tier: 10k neurons/day, FLUX.1-schnell.
* If every provider fails the bot still answers using `assets/stock/`.
* Generated backgrounds are cached in `cache/`, so repeating a verse is instant.

## Chat options
```
88:11               normal
88:11 retry         new background and layout for the same verse
88:11 dark|light    force text tone
88:11 glass|hero|center|bottom|frame|rule
88:11 theme=night   force scene family  (/themes lists all)
```

## Halal guardrails
Prompts are built only from an allow list of creation and architecture scenes and
always end with "no people, no faces, no animals, no statues, no text, no calligraphy".
Calligraphy is never requested because image models produce gibberish Arabic.
