"""Quran directory (114 surahs), verse fetching (async, non-blocking) and
Tamil grammar for the surah reference tag."""

import re
import httpx

# (tamil_name, ayah_count, default_theme)  -- theme keys live in themes.py
QURAN_DIRECTORY = {
    1: ("அல் ஃபாத்திஹா", 7, "guidance"),
    2: ("அல் பகரா", 286, "guidance"),
    3: ("ஆலு இம்ரான்", 200, "steadfast"),
    4: ("அந் நிஸா", 176, "justice"),
    5: ("அல் மாயிதா", 120, "provision"),
    6: ("அல் அன்ஆம்", 165, "creation"),
    7: ("அல் அஃராஃப்", 206, "warning"),
    8: ("அல் அன்ஃபால்", 75, "steadfast"),
    9: ("அத் தவ்பா", 129, "repentance"),
    10: ("யூனுஸ்", 109, "ocean"),
    11: ("ஹூத்", 123, "warning"),
    12: ("யூஸுஃப்", 111, "patience"),
    13: ("அர் ரஃத்", 43, "storm"),
    14: ("இப்ராஹீம்", 52, "gratitude"),
    15: ("அல் ஹிஜ்ர்", 99, "mountain"),
    16: ("அந் நஹ்ல்", 128, "provision"),
    17: ("அல் இஸ்ரா", 111, "night"),
    18: ("அல் கஹ்ஃப்", 110, "mountain"),
    19: ("மர்யம்", 98, "mercy"),
    20: ("தாஹா", 135, "light"),
    21: ("அல் அன்பியா", 112, "cosmos"),
    22: ("அல் ஹஜ்", 78, "kaaba"),
    23: ("அல் முஃமினூன்", 118, "prayer"),
    24: ("அந் நூர்", 64, "light"),
    25: ("அல் ஃபுர்கான்", 77, "guidance"),
    26: ("அஷ் ஷுஅரா", 227, "warning"),
    27: ("அந் நம்ல்", 93, "garden"),
    28: ("அல் கஸஸ்", 88, "patience"),
    29: ("அல் அன்கபூத்", 69, "steadfast"),
    30: ("அர் ரூம்", 60, "creation"),
    31: ("லுக்மான்", 34, "guidance"),
    32: ("அஸ் ஸஜ்தா", 30, "prayer"),
    33: ("அல் அஹ்ஸாப்", 73, "steadfast"),
    34: ("ஸபா", 54, "gratitude"),
    35: ("ஃபாத்திர்", 45, "creation"),
    36: ("யாஸீன்", 83, "cosmos"),
    37: ("அஸ் ஸாஃப்ஃபாத்", 182, "cosmos"),
    38: ("ஸாத்", 88, "patience"),
    39: ("அஸ் ஸுமர்", 75, "mercy"),
    40: ("ஃகாஃபிர்", 85, "repentance"),
    41: ("ஃபுஸ்ஸிலத்", 54, "creation"),
    42: ("அஷ் ஷூரா", 53, "mercy"),
    43: ("அஸ் ஸுக்ருஃப்", 89, "warning"),
    44: ("அத் துகான்", 59, "warning"),
    45: ("அல் ஜாஸியா", 37, "judgement"),
    46: ("அல் அஹ்காஃப்", 35, "desert"),
    47: ("முஹம்மத்", 38, "steadfast"),
    48: ("அல் ஃபத்ஹ்", 29, "hope"),
    49: ("அல் ஹுஜுராத்", 18, "justice"),
    50: ("காஃப்", 45, "judgement"),
    51: ("அத் தாரியாத்", 60, "storm"),
    52: ("அத் தூர்", 49, "mountain"),
    53: ("அந் நஜ்ம்", 62, "cosmos"),
    54: ("அல் கமர்", 55, "night"),
    55: ("அர் ரஹ்மான்", 78, "mercy"),
    56: ("அல் வாகிஆ", 96, "judgement"),
    57: ("அல் ஹதீத்", 29, "light"),
    58: ("அல் முஜாதலா", 22, "justice"),
    59: ("அல் ஹஷ்ர்", 24, "glory"),
    60: ("அல் மும்தஹனா", 13, "justice"),
    61: ("அஸ் ஸஃப்", 14, "steadfast"),
    62: ("அல் ஜுமுஆ", 11, "prayer"),
    63: ("அல் முனாஃபிகூன்", 11, "warning"),
    64: ("அத் தஃகாபுன்", 18, "judgement"),
    65: ("அத் தலாக்", 12, "provision"),
    66: ("அத் தஹ்ரீம்", 12, "repentance"),
    67: ("அல் முல்க்", 30, "cosmos"),
    68: ("அல் கலம்", 52, "patience"),
    69: ("அல் ஹாக்கா", 52, "judgement"),
    70: ("அல் மஆரிஜ்", 44, "patience"),
    71: ("நூஹ்", 28, "ocean"),
    72: ("அல் ஜின்", 28, "night"),
    73: ("அல் முஸ்ஸம்மில்", 20, "night"),
    74: ("அல் முத்தஸ்ஸிர்", 56, "dawn"),
    75: ("அல் கியாமா", 40, "judgement"),
    76: ("அல் இன்ஸான்", 31, "garden"),
    77: ("அல் முர்ஸலாத்", 50, "storm"),
    78: ("அந் நபஃ", 40, "creation"),
    79: ("அந் நாஸிஆத்", 46, "judgement"),
    80: ("அபஸ", 42, "provision"),
    81: ("அத் தக்வீர்", 29, "cosmos"),
    82: ("அல் இன்ஃபிதார்", 19, "cosmos"),
    83: ("அல் முதஃப்ஃபிஃபீன்", 36, "justice"),
    84: ("அல் இன்ஷிகாக்", 25, "judgement"),
    85: ("அல் புரூஜ்", 22, "cosmos"),
    86: ("அத் தாரிக்", 17, "night"),
    87: ("அல் அஃலா", 19, "glory"),
    88: ("அல் ஃகாஷியா", 26, "creation"),
    89: ("அல் ஃபஜ்ர்", 30, "dawn"),
    90: ("அல் பலத்", 20, "kaaba"),
    91: ("அஷ் ஷம்ஸ்", 15, "dawn"),
    92: ("அல் லைல்", 21, "night"),
    93: ("அள் ளுஹா", 11, "dawn"),
    94: ("அஷ் ஷர்ஹ்", 8, "hope"),
    95: ("அத் தீன்", 8, "garden"),
    96: ("அல் அலக்", 19, "light"),
    97: ("அல் கத்ர்", 5, "night"),
    98: ("அல் பய்யினா", 8, "light"),
    99: ("அஸ் ஸல்ஸலா", 8, "judgement"),
    100: ("அல் ஆதியாத்", 11, "desert"),
    101: ("அல் காரிஆ", 11, "judgement"),
    102: ("அத் தகாஸுர்", 8, "warning"),
    103: ("அல் அஸ்ர்", 3, "patience"),
    104: ("அல் ஹுமஸா", 9, "warning"),
    105: ("அல் ஃபீல்", 5, "kaaba"),
    106: ("குறைஷ்", 4, "kaaba"),
    107: ("அல் மாஊன்", 7, "justice"),
    108: ("அல் கவ்ஸர்", 3, "hope"),
    109: ("அல் காஃபிரூன்", 6, "steadfast"),
    110: ("அந் நஸ்ர்", 3, "hope"),
    111: ("அல் லஹப்", 5, "warning"),
    112: ("அல் இஃக்லாஸ்", 4, "glory"),
    113: ("அல் ஃபலக்", 5, "dawn"),
    114: ("அந் நாஸ்", 6, "prayer"),
}

# Arabic definite-article assimilation -> Tamil "ஸூரத்து + X" forms
_PREFIX_MAP = {
    "அல்": "ஸூரத்துல்", "அர்": "ஸூரத்துர்", "அந்": "ஸூரத்துந்", "அத்": "ஸூரத்துத்",
    "அஷ்": "ஸூரத்துஷ்", "அஸ்": "ஸூரத்துஸ்", "அள்": "ஸூரத்துள்",
}


def surah_reference(surah: int, ayah: int) -> str:
    raw, _, _ = QURAN_DIRECTORY[surah]
    parts = raw.split(" ", 1)
    if len(parts) == 2 and parts[0] in _PREFIX_MAP:
        return f"{_PREFIX_MAP[parts[0]]} {parts[1]} || {surah}:{ayah}"
    return f"ஸூரத்து {raw} || {surah}:{ayah}"


def validate(surah: int, ayah: int):
    if surah < 1 or surah > 114:
        raise ValueError("❌ தவறான ஸூரா எண்! (1 முதல் 114 வரை உள்ள ஸூராவைத் தேர்ந்தெடுக்கவும்).")
    raw, max_ayahs, _ = QURAN_DIRECTORY[surah]
    if ayah < 1 or ayah > max_ayahs:
        raise ValueError(
            f"❌ ஸூரா {raw} ({surah})-ல் மொத்தம் {max_ayahs} வசனங்கள் மட்டுமே உள்ளன!\n"
            f"(1 முதல் {max_ayahs} வரை உள்ள வசனத்தை உள்ளிடவும்)."
        )


_REF_RE = re.compile(r"^\s*(\d{1,3})\s*[:\-/.\s]\s*(\d{1,3})\s*$")


def parse_reference(text: str):
    """'88:11', '88 11', '88-11' -> (88, 11) or None."""
    m = _REF_RE.match(text or "")
    return (int(m.group(1)), int(m.group(2))) if m else None


def clean_verse_text(t: str) -> str:
    t = t.strip()
    t = re.sub(r"\s*\(\d+:\d+\)\s*$", "", t)
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[\-–—\s]+$", "", t).strip()
    # Tamil-friendly curly quotes
    t = re.sub(r'"([^"]*)"', r"“\1”", t)
    t = t.replace(" ,", ",").replace(" .", ".").replace(" !", "!").replace(" ?", "?")
    if t and not t.endswith((".", "!", "?", "”", '"', "’")):
        t += "."
    return t


async def fetch_verse(surah: int, ayah: int) -> tuple[str, str]:
    """Returns (tamil_text, reference). Tries two free sources, async."""
    validate(surah, ayah)
    raw, _, _ = QURAN_DIRECTORY[surah]
    text = ""
    headers = {"User-Agent": "Mozilla/5.0"}
    async with httpx.AsyncClient(timeout=8, headers=headers, follow_redirects=True) as c:
        try:
            r = await c.get(f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/ta.tamil")
            d = r.json()
            if d.get("status") == "OK":
                text = d["data"]["text"]
        except Exception:
            pass
        if not text:
            try:
                r = await c.get(
                    "https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/editions/"
                    f"tam-janturstfoundat/{surah}/{ayah}.json"
                )
                text = r.json()["text"]
            except Exception:
                pass
    text = clean_verse_text(text)
    if len(text.strip(" .!?-\"'“”")) < 2:
        raise ValueError(f"❌ ஸூரா {raw} {surah}:{ayah}-ன் உரை கிடைக்கவில்லை!")
    return text, surah_reference(surah, ayah)
