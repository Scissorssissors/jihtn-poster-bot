"""Theme engine: classify a Tamil verse into a scene family, build a halal
image prompt, and give palette + layout preferences.

No LLM needed. Keyword hits on the Tamil text win; otherwise the surah's
default theme from quran.py is used. Seeded by surah:ayah so a verse always
produces the same poster unless the user asks for a retry."""

import random
import hashlib

# --------------------------------------------------------------------------
# Scene families.  Every scene is creation or architecture only: no humans,
# no faces, no animals, no statues, no calligraphy (AI renders gibberish Arabic).
# --------------------------------------------------------------------------
SCENES = {
    "mercy": {
        "scenes": [
            "soft golden sunrise over a misty green valley, gentle rays through clouds",
            "warm light breaking through clouds over a calm lake, pastel sky",
            "dew-covered meadow at dawn, soft golden haze, rolling hills",
        ],
        "mood": "warm", "tone": "dark",
    },
    "creation": {
        "scenes": [
            "vast mountains and clouds seen from above at golden hour, layered ridges",
            "waterfall in a lush canyon, sunbeams, mist, epic landscape",
            "wide earth horizon with sun rising, fields and rivers below, cinematic",
        ],
        "mood": "earth", "tone": "dark",
    },
    "cosmos": {
        "scenes": [
            "deep space nebula with countless stars, violet and teal gas clouds",
            "milky way galaxy arching over a silent desert at night",
            "crescent moon and stars above thin clouds, deep indigo sky",
        ],
        "mood": "cosmic", "tone": "dark",
    },
    "judgement": {
        "scenes": [
            "dramatic storm clouds with a single shaft of light on a vast plain",
            "dark mountain range under heavy clouds with one bright opening",
            "cracked dry earth under a dramatic twilight sky, wide shot",
        ],
        "mood": "solemn", "tone": "dark",
    },
    "warning": {
        "scenes": [
            "deep red and amber sky over silhouetted dunes, dust haze, cinematic",
            "ominous clouds gathering over an empty rocky valley, moody light",
        ],
        "mood": "ember", "tone": "dark",
    },
    "patience": {
        "scenes": [
            "lone ancient olive tree on a hill under a soft overcast sky",
            "calm sea at dusk with gentle waves, long exposure, muted blue",
            "snow-dusted mountain under a quiet pale sky, minimal",
        ],
        "mood": "calm", "tone": "dark",
    },
    "guidance": {
        "scenes": [
            "a winding path through misty hills leading toward glowing light",
            "sunbeams through a grand mosque arcade of geometric arches, empty, no people",
            "lighthouse beam over a calm night sea, stars above",
        ],
        "mood": "navy", "tone": "dark",
    },
    "gratitude": {
        "scenes": [
            "golden wheat field at sunset with soft clouds, gentle breeze",
            "orchard of fruit trees in warm afternoon light, bokeh, no people",
            "flowing river through green valley, warm golden light",
        ],
        "mood": "gold", "tone": "dark",
    },
    "prayer": {
        "scenes": [
            "interior of a grand mosque with ornate geometric arches and hanging lanterns, empty, no people",
            "mosque dome and minarets silhouetted against a twilight sky, crescent moon",
            "quiet mosque courtyard with marble floor reflecting the evening sky, empty",
        ],
        "mood": "sacred", "tone": "dark",
    },
    "provision": {
        "scenes": [
            "rain falling on lush green fields, rainbow light, fresh atmosphere",
            "date palm oasis with still water reflecting the sky, warm light",
            "ripe grape vines and olive groves in soft morning light",
        ],
        "mood": "green", "tone": "dark",
    },
    "ocean": {
        "scenes": [
            "vast turquoise ocean with white waves from above, sunlight on water",
            "ship-less open sea at sunrise, golden path of light on water",
            "underwater light rays in clear blue sea, no fish, serene",
        ],
        "mood": "teal", "tone": "dark",
    },
    "light": {
        "scenes": [
            "a single glowing lantern niche in a dark stone wall, soft golden glow",
            "radiant light bursting through clouds, luminous white and gold",
            "sunrise light filling an arched marble corridor, no people",
        ],
        "mood": "luminous", "tone": "light",
    },
    "night": {
        "scenes": [
            "starry night sky over desert dunes, deep blue, quiet",
            "crescent moon over a still lake, reflections, midnight blue",
            "mosque silhouette under a starry sky with a thin crescent",
        ],
        "mood": "midnight", "tone": "dark",
    },
    "dawn": {
        "scenes": [
            "first light of dawn over desert dunes, pink and gold sky",
            "sunrise over a calm sea with soft peach and lavender clouds",
            "morning mist over hills with sun just rising, soft pastel",
        ],
        "mood": "rose", "tone": "light",
    },
    "mountain": {
        "scenes": [
            "majestic mountain peaks above a sea of clouds at golden hour",
            "rocky cliffs with a cave opening and warm light inside, no people",
            "towering granite mountains and a still alpine lake, dramatic",
        ],
        "mood": "stone", "tone": "dark",
    },
    "desert": {
        "scenes": [
            "endless sand dunes with wind ripples at golden hour, long shadows",
            "desert canyon with warm orange rock walls and a strip of blue sky",
        ],
        "mood": "sand", "tone": "dark",
    },
    "storm": {
        "scenes": [
            "wind-swept clouds racing over a wide plain, dramatic light",
            "lightning inside towering clouds over the sea at night, wide shot",
        ],
        "mood": "slate", "tone": "dark",
    },
    "garden": {
        "scenes": [
            "lush paradise garden with flowing streams, flowers and fruit trees, soft light, no people",
            "waterfall into a crystal pool surrounded by greenery and blossoms",
        ],
        "mood": "emerald", "tone": "dark",
    },
    "kaaba": {
        "scenes": [
            "the Kaaba in Makkah at dawn, misty golden light, wide empty courtyard, no people",
            "Masjid al-Haram minarets and the Kaaba at twilight, soft glow, no people",
        ],
        "mood": "sacred", "tone": "dark",
    },
    "glory": {
        "scenes": [
            "majestic golden dome and minarets glowing against a dramatic sunset sky",
            "grand geometric islamic arch pattern with light beams, ornate, no text",
            "sun rays bursting over mountains with golden clouds, awe-inspiring",
        ],
        "mood": "royal", "tone": "dark",
    },
    "justice": {
        "scenes": [
            "balanced stone formations under a clear sky, calm desert, symmetry",
            "symmetrical marble courtyard with arches and a reflecting pool, empty",
        ],
        "mood": "navy", "tone": "dark",
    },
    "steadfast": {
        "scenes": [
            "a great rock standing firm against ocean waves, dramatic sky",
            "ancient fortress walls on a hill at sunset, no people",
        ],
        "mood": "stone", "tone": "dark",
    },
    "repentance": {
        "scenes": [
            "rain clearing over a valley with light breaking through, fresh green",
            "quiet dawn after rain, wet stone path, soft light ahead",
        ],
        "mood": "calm", "tone": "dark",
    },
    "hope": {
        "scenes": [
            "rainbow over green hills after rain, bright clearing sky",
            "sunrise bursting over the horizon with birdsless clear sky, golden",
        ],
        "mood": "gold", "tone": "light",
    },
}

# Tamil keyword -> theme (first hit by priority order wins; multiple hits are scored)
KEYWORDS = [
    ("kaaba", ["கஃபா", "காபா", "மக்கா", "ஹஜ்", "பைத்துல்லாஹ்", "ஹரம்"]),
    ("cosmos", ["நட்சத்திர", "வானங்கள்", "கிரக", "சூரிய", "சந்திர", "விண்", "அண்ட"]),
    ("ocean", ["கடல்", "அலை", "கப்பல்", "பெருங்கடல்"]),
    ("garden", ["சுவனம்", "சுவர்க்க", "தோட்ட", "ஆறுகள்", "நதிகள்", "ஜன்னத்"]),
    ("judgement", ["மறுமை", "கியாம", "நரக", "விசாரணை", "நியாயத்தீர்ப்பு", "தண்டனை", "எழுப்ப"]),
    ("warning", ["அழி", "வேதனை", "எச்சரி", "சபி", "நிராகரிப்ப", "பொய்ப்ப"]),
    ("mercy", ["கருணை", "அருள்", "மன்னி", "இரக்க", "ரஹ்மான்", "ரஹீம்", "அன்பு"]),
    ("light", ["ஒளி", "நூர்", "பிரகாச", "விளக்கு"]),
    ("night", ["இரவு", "இருள்"]),
    ("dawn", ["விடியல்", "காலை", "அதிகாலை", "ஃபஜ்ர்", "ளுஹா"]),
    ("provision", ["உணவு", "மழை", "பழ", "ரிஸ்க்", "வாழ்வாதார", "பயிர்", "பேரீச்ச", "திராட்சை", "ஒலிவ"]),
    ("mountain", ["மலை", "குன்று", "குகை", "பாறை"]),
    ("desert", ["பாலைவன", "மணல்"]),
    ("storm", ["காற்று", "புயல்", "இடி", "மின்னல்", "மேகம்"]),
    ("patience", ["பொறுமை", "சகி", "ஸப்ர்"]),
    ("gratitude", ["நன்றி", "அருட்கொடை", "நிஃமத்", "ஷுக்ர்"]),
    ("prayer", ["தொழு", "பிரார்த்த", "துஆ", "ஸலாத்", "ஸஜ்தா", "இறைஞ்ச", "பள்ளிவாசல்"]),
    ("guidance", ["நேர்வழி", "வழிகாட்ட", "ஹிதாயத்", "நேரான பாதை", "வேதம்", "குர்ஆன்"]),
    ("repentance", ["தவ்பா", "பாவமன்னிப்பு", "மீள்", "திரும்பு"]),
    ("justice", ["நீதி", "நியாய", "அநீதி", "அளவு", "நிறு"]),
    ("steadfast", ["உறுதி", "நம்பிக்கை", "ஈமான்", "நிலைத்த", "போராட"]),
    ("hope", ["நற்செய்தி", "வெற்றி", "எளிதாக்க", "நிம்மதி", "சுகம்"]),
    ("glory", ["மகத்துவ", "புகழ்", "பெருமை", "அரச", "ஆட்சி", "தூய", "ஸுப்ஹான"]),
    ("creation", ["படை", "வானம்", "பூமி", "உயிர்", "அறிகுறி", "சான்று"]),
]


def pick_theme(text: str, surah_default: str) -> str:
    scores = {}
    for theme, words in KEYWORDS:
        hits = sum(text.count(w) for w in words)
        if hits:
            scores[theme] = scores.get(theme, 0) + hits
    if not scores:
        return surah_default
    best = max(scores.values())
    for theme, _ in KEYWORDS:  # priority order on ties
        if scores.get(theme) == best:
            return theme
    return surah_default


def seed_for(surah: int, ayah: int, variant: int = 0) -> int:
    h = hashlib.md5(f"{surah}:{ayah}:{variant}".encode()).hexdigest()
    return int(h[:8], 16)


STYLE_SUFFIX = (
    ", photorealistic, cinematic wide shot, 8k, highly detailed, soft volumetric light, "
    "serene, peaceful, empty landscape, no people, no humans, no faces, no figures, "
    "no animals, no birds, no statues, no text, no letters, no calligraphy, no watermark, "
    "composition with calm open space in the upper half for a quote"
)


def build_prompt(theme: str, seed: int) -> str:
    rng = random.Random(seed)
    scene = rng.choice(SCENES[theme]["scenes"])
    return scene + STYLE_SUFFIX
