import os
import sys
import re
import json
import random
import asyncio
import base64
import urllib.request
import urllib.parse
import http.server
import socketserver
import threading
from playwright.async_api import async_playwright
from telegram import Update
from telegram.request import HTTPXRequest
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = "8955985482:AAFGVlfGRbttDANQhO40yYTBw1xITyt2s20"

# --- 1. POSTER TEMPLATE (OFFICIAL MASTER KIT) ---
TEMPLATE_CONTENT = """<!DOCTYPE html>
<html lang="ta">
<head>
<meta charset="UTF-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Anek+Tamil:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
  * { 
    box-sizing: border-box; 
    margin: 0; 
    padding: 0; 
    font-family: 'Anek Tamil', sans-serif;
  }
  body {
    width: 1080px; 
    height: 1380px; 
    background: #ffffff;
    display: flex; 
    flex-direction: column; 
    justify-content: space-between;
    padding: 24px 38px 24px 38px;
  }

  .header { 
    display: flex; 
    align-items: center; 
    gap: 24px; 
    height: 154px; 
    width: 1004px;
    margin: 0 auto;
  }
  .header img { 
    height: 148px; 
    width: auto;
    object-fit: contain; 
    flex-shrink: 0;
  }
  .header-text { 
    display: flex;
    flex-direction: column;
    justify-content: center;
    color: #143e6d; 
    font-size: 50px; 
    font-weight: 800; 
    line-height: 1.12; 
    letter-spacing: -0.4px;
  }
  .underline-hind {
    text-decoration: underline;
    text-underline-offset: 7px;
    text-decoration-thickness: 4px;
  }
  .header-text .sub-text { 
    font-size: 36px; 
    font-weight: 700; 
    margin-top: 6px;
    letter-spacing: -0.2px;
  }

  .card {
    position: relative; 
    width: 1004px; 
    height: 1070px;
    margin: 0 auto;
    border-radius: 36px; 
    overflow: hidden;
    box-shadow: 0 14px 36px rgba(0, 0, 0, 0.20);
    border: 3.5px solid #82909c; 
    background: #111827;
  }
  .bg-image { 
    position: absolute; 
    width: 100%; 
    height: 1070px; 
    object-fit: cover; 
  }

  .gradient-overlay {
    position: absolute; 
    top: 0; 
    left: 0; 
    width: 100%; 
    height: 82%;
    background: {{GRADIENT_CSS}};
  }

  .verse-container {
    position: relative; 
    z-index: 2;
    padding: {{DYNAMIC_PADDING}};
    color: {{TEXT_COLOR}};
    font-size: {{DYNAMIC_FONT_SIZE}};
    font-weight: 800;
    line-height: {{DYNAMIC_LINE_HEIGHT}};
    text-align: center;
    text-shadow: {{TEXT_SHADOW}};
    letter-spacing: 0.2px;
  }

  .surah-tag {
    position: absolute; 
    bottom: 26px; 
    left: 50%; 
    transform: translateX(-50%);
    background: #ffffff; 
    color: #111111; 
    font-size: 25px; 
    font-weight: 800;
    padding: 9px 38px; 
    border-radius: 7px; 
    z-index: 2; 
    white-space: nowrap;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35);
    letter-spacing: 0.4px;
  }

  .footer {
    display: flex; 
    justify-content: space-between; 
    align-items: center;
    width: 1004px;
    margin: 0 auto;
    color: #143e6d; 
    font-size: 32px; 
    font-weight: 800; 
    letter-spacing: 2px;
    height: 48px;
    padding: 0 2px;
  }
</style>
</head>
<body>
  <div class="header">
    <img src="{{LOGO_DATA_URI}}" alt="JIH Logo">
    <div class="header-text">
      <span>ஜமாஅத்தே இஸ்லாமி <span class="underline-hind">ஹிந்த்</span></span>
      <span class="sub-text">தமிழ்நாடு & புதுச்சேரி</span>
    </div>
  </div>
  <div class="card">
    <img class="bg-image" src="{{IMAGE_DATA_URI}}" alt="Background">
    <div class="gradient-overlay"></div>
    <div class="verse-container">{{VERSE_TEXT}}</div>
    <div class="surah-tag">{{SURAH_REF}}</div>
  </div>
  <div class="footer">
    <div>JIHTN MEDIA</div>
    <div>VISIT US : WWW.JIHTN.ORG</div>
  </div>
</body>
</html>"""

# --- 2. SURAH DIRECTORY & METADATA (114 SURAHS) ---
QURAN_DIRECTORY = {
    1: ("அல் ஃபாத்திஹா", 7, "sacred_sanctuary"),
    2: ("அல் பகரா", 286, "historic_amber"),
    3: ("ஆல இம்ரான்", 200, "historic_amber"),
    4: ("அந் நிஸா", 176, "historic_amber"),
    5: ("அல் மாயிதா", 120, "masjid_noor"),
    6: ("அல் அன்ஆம்", 165, "celestial_cosmos"),
    7: ("அல் அஃராஃப்", 206, "historic_amber"),
    8: ("அல் அன்ஃபால்", 75, "historic_amber"),
    9: ("அத் தவ்பா", 129, "historic_amber"),
    10: ("யூனுஸ்", 109, "waters_oceans"),
    11: ("ஹூத்", 123, "historic_amber"),
    12: ("யூஸுஃப்", 111, "masjid_noor"),
    13: ("அர் ரஃது", 43, "celestial_cosmos"),
    14: ("இப்ராஹீம்", 52, "sacred_sanctuary"),
    15: ("அல் ஹிஜ்ர்", 99, "desert_dawn"),
    16: ("அந் நஹ்ல்", 128, "jannah_gardens"),
    17: ("அல் இஸ்ரா", 111, "masjid_noor"),
    18: ("கஹ்ஃப்", 110, "masjid_noor"),
    19: ("மர்யம்", 98, "jannah_gardens"),
    20: ("தாஹா", 135, "masjid_noor"),
    21: ("அல் அன்பியா", 112, "historic_amber"),
    22: ("அல் ஹஜ்", 78, "sacred_sanctuary"),
    23: ("அல் முஃமினூன்", 118, "jannah_gardens"),
    24: ("அந் நூர்", 64, "masjid_noor"),
    25: ("அல் ஃபுர்கான்", 77, "waters_oceans"),
    26: ("அஷ் ஷுஅரா", 227, "historic_amber"),
    27: ("அந் நம்ல்", 93, "desert_dawn"),
    28: ("அல் கஸஸ்", 88, "historic_amber"),
    29: ("அல் அன்கபூத்", 69, "historic_amber"),
    30: ("ரூம்", 60, "celestial_cosmos"),
    31: ("லுக்மான்", 34, "masjid_noor"),
    32: ("அஸ் ஸஜ்தா", 30, "solemn_resurrection"),
    33: ("அல் அஹ்ஸாப்", 73, "historic_amber"),
    34: ("ஸபா", 54, "desert_dawn"),
    35: ("ஃபாதிர்", 45, "celestial_cosmos"),
    36: ("யாஸீன்", 83, "masjid_noor"),
    37: ("அஸ் ஸாஃப்பாத்", 182, "celestial_cosmos"),
    38: ("ஸாத்", 88, "historic_amber"),
    39: ("அஸ் ஸுமர்", 75, "masjid_noor"),
    40: ("ஃகாஃபிர்", 85, "celestial_cosmos"),
    41: ("ஃபுஸ்ஸிலத்", 54, "celestial_cosmos"),
    42: ("அஷ் ஷூரா", 53, "masjid_noor"),
    43: ("அஸ் ஸுக்ருஃப்", 89, "jannah_gardens"),
    44: ("அத் துகான்", 59, "solemn_resurrection"),
    45: ("அல் ஜாஸியா", 37, "solemn_resurrection"),
    46: ("அல் அஹ்காஃப்", 35, "desert_dawn"),
    47: ("முஹம்மத்", 38, "historic_amber"),
    48: ("அல் ஃபத்ஹ்", 29, "sacred_sanctuary"),
    49: ("அல் ஹுஜுராத்", 18, "masjid_noor"),
    50: ("காஃப்", 45, "solemn_resurrection"),
    51: ("அத் தாரியாத்", 60, "celestial_cosmos"),
    52: ("அத் தூர்", 49, "earth_mountains"),
    53: ("அந் நஜ்ம்", 62, "celestial_cosmos"),
    54: ("அல் கமர்", 55, "night_layl"),
    55: ("அர் ரஹ்மான்", 78, "jannah_gardens"),
    56: ("அல் வாகிஆ", 96, "jannah_gardens"),
    57: ("அல் ஹதீத்", 29, "masjid_noor"),
    58: ("அல் முஜாதலா", 22, "masjid_noor"),
    59: ("அல் ஹஷ்ர்", 24, "historic_amber"),
    60: ("அல் மும்தஹினா", 13, "historic_amber"),
    61: ("அஸ் ஸஃப்", 14, "historic_amber"),
    62: ("அல் ஜுமுஆ", 11, "masjid_noor"),
    63: ("அல் முனாஃபிகூன்", 11, "solemn_resurrection"),
    64: ("அத் தஃகாபுன்", 18, "solemn_resurrection"),
    65: ("அத் தலாக்", 12, "masjid_noor"),
    66: ("அத் தஹ்ரீம்", 12, "masjid_noor"),
    67: ("அல் முல்க்", 30, "celestial_cosmos"),
    68: ("அல் கலம்", 52, "guidance_book"),
    69: ("அல் ஹாகா", 52, "solemn_resurrection"),
    70: ("அல் மஆரிஜ்", 44, "solemn_resurrection"),
    71: ("நூஹ்", 28, "waters_oceans"),
    72: ("அல் ஜின்", 28, "night_layl"),
    73: ("அல் முஸ்ஸம்மில்", 20, "night_layl"),
    74: ("அல் முத்தஸ்ஸிர்", 56, "solemn_resurrection"),
    75: ("அல் கியாமஹ்", 40, "solemn_resurrection"),
    76: ("அல் இன்ஸான்", 31, "jannah_gardens"),
    77: ("அல் முர்ஸலாத்", 50, "solemn_resurrection"),
    78: ("அந் நபஃ", 40, "solemn_resurrection"),
    79: ("அந் நாஸிஆத்", 46, "solemn_resurrection"),
    80: ("அபஸ", 42, "solemn_resurrection"),
    81: ("அத் தக்வீர்", 29, "celestial_cosmos"),
    82: ("அல் இன்ஃபிதார்", 19, "celestial_cosmos"),
    83: ("அல் முaffiஃபீன்", 36, "solemn_resurrection"),
    84: ("அல் இன்ஷிகாக்", 25, "celestial_cosmos"),
    85: ("புரூஜ்", 22, "celestial_cosmos"),
    86: ("அத் தாரிக்", 17, "night_layl"),
    87: ("அல் அஃலா", 19, "jannah_gardens"),
    88: ("ஃகாஷியா", 26, "solemn_resurrection"),
    89: ("அல் ஃபஜ்ர்", 30, "dawn_fajr"),
    90: ("அல் பலத்", 20, "sacred_sanctuary"),
    91: ("அஷ் ஷம்ஸ்", 15, "dawn_fajr"),
    92: ("அல் லைல்", 21, "night_layl"),
    93: ("அழ் ளுஹா", 11, "mercy_solace"),
    94: ("அஷ் ஷர்ஹ்", 8, "mercy_solace"),
    95: ("அத் தீன்", 8, "jannah_gardens"),
    96: ("அல் அலக்", 19, "guidance_book"),
    97: ("அல் கத்ர்", 5, "night_layl"),
    98: ("அல் பய்யினஹ்", 8, "guidance_book"),
    99: ("ஸல்ஸலா", 8, "solemn_resurrection"),
    100: ("ஆதியாத்", 11, "solemn_resurrection"),
    101: ("அல் காரிஆ", 11, "solemn_resurrection"),
    102: ("அத் தகாஸுர்", 8, "solemn_resurrection"),
    103: ("அல் அஸ்ர்", 3, "historic_amber"),
    104: ("அல் ஹுமஸஹ்", 9, "solemn_resurrection"),
    105: ("அல் ஃபீல்", 5, "sacred_sanctuary"),
    106: ("குரைஷ்", 4, "sacred_sanctuary"),
    107: ("அல் மாவூன்", 7, "sacred_sanctuary"),
    108: ("அல் கவ்தர்", 3, "waters_oceans"),
    109: ("அல் காஃபிரூன்", 6, "sacred_sanctuary"),
    110: ("அந் நஸ்ர்", 3, "sacred_sanctuary"),
    111: ("அல் மஸத்", 5, "solemn_resurrection"),
    112: ("அல் இக்லாஸ்", 4, "sacred_sanctuary"),
    113: ("அல் ஃபலக்", 5, "dawn_fajr"),
    114: ("அந் நாஸ்", 6, "sacred_sanctuary")
}

# --- 3. 12 THEMATIC MACRO PALETTES & 200+ CURATED HALAL IMAGES ---
THEME_PALETTES = {
    # 1. Heavens, Astronomy & Cosmic Order
    "celestial_cosmos": {
        "gradient": "linear-gradient(180deg, rgba(10, 24, 52, 0.98) 0%, rgba(14, 32, 68, 0.93) 50%, rgba(14, 32, 68, 0.45) 80%, rgba(0, 0, 0, 0) 100%)",
        "text_color": "#ffffff",
        "shadow": "0 2px 6px rgba(0,0,0,0.9), 0 4px 18px rgba(0,0,0,0.6)",
        "images": [
            "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?q=80&w=1080&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=1080&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1080&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1502134249126-9f3755a50d78?q=80&w=1080&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1538370965046-79c0d6907d47?q=80&w=1080&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?q=80&w=1080&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?q=80&w=1080&auto=format&fit=crop"
        ]
    },
    # 2. Sacred Geography & Qiblah (Makkah, Kaaba)
    "sacred_sanctuary": {
        "gradient": "linear-gradient(180deg, rgba(165, 205, 225, 0.98) 0%, rgba(190, 220, 235, 0.92) 50%, rgba(210, 232, 245, 0.35) 80%, rgba(0, 0, 0, 0) 100%)",
        "text_color": "#112a45",
        "shadow": "0 2px 8px rgba(255,255,255,0.7), 0 1px 2px rgba(0,0,0,0.15)",
        "images": [
            "https://images.unsplash.com/photo-1591604129939-f1efa4d9f7fa?q=80&w=1080&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1565552645632-d725f8bfc19a?q=80&w=1080&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1542816417-0983c9c9ad53?q=80&w=1080&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1564769625905-50e93615e769?q=80&w=1080&auto=format&fit=crop"
        ]
    },
    # 3. Masjid Architecture, Light (Noor) & Madinah
    "masjid_noor": {
        "gradient": "linear-gradient(180deg, rgba(185, 115, 15, 0.98) 0%, rgba(165, 100, 10, 0.93) 50%, rgba(165, 100, 10, 0.45) 80%, rgba(0, 0, 0, 0) 100%)",
        "text_color": "#ffffff",
        "shadow": "0 2px 5px rgba(0,0,0,0.85), 0 4px 18px rgba(0,0,0,0.55)",
        "images": [
            "https://images.unsplash.com/photo-1584551246679-0daf3d275d0f?q=80&w=1080&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1519817650390-64a93db51149?q=80&w=1080&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1564769625905-50e93615e769?q=80&w=1080&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1590076215667-875d4ef2d7ee?q=80&w=1080&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1579783902614-a3fb3927b675?q=80&w=1080&auto=format&fit=crop"
        ]
    },
    # 4. Paradise, Jannah & Pure Gardens
    "jannah_gardens": {
        "gradient": "linear-gradient(180deg, rgba(12, 68, 44, 0.98) 0%, rgba(15, 82, 54, 0.94) 52%, rgba(15, 82, 54, 0.45) 82%, rgba(0,0,0,0) 100%)",
        "text_color": "#ffffff",
        "shadow": "0 2px 6px rgba(0,0,0,0.85), 0 4px 18px rgba(0,0,0,0.55)",
        "images": [
            "https://images.unsplash.com/photo-1511497584788-87676104235f?q=80&w=1080&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?q=80&w=1080&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1426604966848-d7adac402bff?q=80&w=1080&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1518495973542-4542c06a5843?q=80&w=1080&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1448375240586-882707db888b?q=80&w=1080&auto=format&fit=crop"
        ]
    },
    # 5. Historic Struggle, Patience & Trials (Reference 1)
    "historic_amber": {
        "gradient": "linear-gradient(180deg, rgba(215, 80, 10, 0.98) 0%, rgba(200, 72, 8, 0.94) 50%, rgba(195, 70, 8, 0.45) 80%, rgba(0, 0, 0, 0) 100%)",
        "text_color": "#ffffff",
        "shadow": "0 2px 5px rgba(0,0,0,0.85), 0 5px 20px rgba(0,0,0,0.55)",
        "images": [
            "https://images.unsplash.com/photo-1512958789358-4dac567096e8?q=80&w=1080&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?q=80&w=1080&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1473580044384-7ba9967e16a0?q=80&w=1080&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1542816417-0983c9c9ad53?q=80&w=1080&auto=format&fit=crop"
        ]
    },
    # 6. Solemnity, Day of Resurrection & Accountability
    "solemn_resurrection": {
        "gradient": "linear-gradient(180deg, rgba(88, 16, 28, 0.98) 0%, rgba(72, 14, 24, 0.93) 50%, rgba(55, 12, 20, 0.45) 80%, rgba(0, 0, 0, 0) 100%)",
        "text_color": "#ffffff",
        "shadow": "0 2px 6px rgba(0,0,0,0.9), 0 4px 18px rgba(0,0,0,0.6)",
        "images": [
            "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?q=80&w=1080&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1498084393753-b411b2d26b34?q=80&w=1080&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1519681393784-d120267933ba?q=80&w=1080&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1486870591958-9b9d0d1dda99?q=80&w=1080&auto=format&fit=crop"
        ]
    },
    # 7. Water, Rain, Oceans & Hydrology
    "waters_oceans": {
        "gradient": "linear-gradient(180deg, rgba(10, 55, 75, 0.98) 0%, rgba(12, 68, 90, 0.93) 50%, rgba(12, 68, 90, 0.45) 80%, rgba(0, 0, 0, 0) 100%)",
        "text_color": "#ffffff",
        "shadow": "0 2px 6px rgba(0,0,0,0.85), 0 4px 18px rgba(0,0,0,0.55)",
        "images": [
            "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?q=80&w=1080&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1498084393753-b411b2d26b34?q=80&w=1080&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1518837695005-2083093ee35b?q=80&w=1080&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?q=80&w=1080&auto=format&fit=crop"
        ]
    },
    # 8. Earth, Geology & Mountains (Signs in Nature)
    "earth_mountains": {
        "gradient": "linear-gradient(180deg, rgba(62, 42, 28, 0.98) 0%, rgba(78, 54, 38, 0.93) 50%, rgba(78, 54, 38, 0.45) 80%, rgba(0, 0, 0, 0) 100%)",
        "text_color": "#ffffff",
        "shadow": "0 2px 5px rgba(0,0,0,0.85), 0 4px 18px rgba(0,0,0,0.55)",
        "images": [
            "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?q=80&w=1080&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1506744038136-46273834b3fb?q=80&w=1080&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1486870591958-9b9d0d1dda99?q=80&w=1080&auto=format&fit=crop"
        ]
    },
    # 9. Desert & Untrodden Dunes (Vast Horizons)
    "desert_dawn": {
        "gradient": "linear-gradient(180deg, rgba(195, 95, 20, 0.98) 0%, rgba(175, 85, 16, 0.93) 50%, rgba(175, 85, 16, 0.45) 80%, rgba(0, 0, 0, 0) 100%)",
        "text_color": "#ffffff",
        "shadow": "0 2px 5px rgba(0,0,0,0.85), 0 4px 18px rgba(0,0,0,0.55)",
        "images": [
            "https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?q=80&w=1080&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1473580044384-7ba9967e16a0?q=80&w=1080&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=1080&auto=format&fit=crop"
        ]
    },
    # 10. Dawn, Morning & Awakening (Surah Fajr, Shams, Falaq)
    "dawn_fajr": {
        "gradient": "linear-gradient(180deg, rgba(188, 78, 48, 0.98) 0%, rgba(212, 106, 68, 0.92) 50%, rgba(212, 106, 68, 0.40) 80%, rgba(0, 0, 0, 0) 100%)",
        "text_color": "#ffffff",
        "shadow": "0 2px 5px rgba(0,0,0,0.85), 0 4px 18px rgba(0,0,0,0.55)",
        "images": [
            "https://images.unsplash.com/photo-1495616811223-4d98c6e9c869?q=80&w=1080&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1500382017468-9049fed747ef?q=80&w=1080&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1470240731273-7821a6eeb6bd?q=80&w=1080&auto=format&fit=crop"
        ]
    },
    # 11. Night & Peaceful Contemplation (Layl, Muzammil, Qadr)
    "night_layl": {
        "gradient": "linear-gradient(180deg, rgba(8, 18, 38, 0.98) 0%, rgba(12, 26, 52, 0.94) 50%, rgba(12, 26, 52, 0.45) 80%, rgba(0, 0, 0, 0) 100%)",
        "text_color": "#ffffff",
        "shadow": "0 2px 6px rgba(0,0,0,0.9), 0 4px 18px rgba(0,0,0,0.6)",
        "images": [
            "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?q=80&w=1080&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=1080&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1534447677768-be436bb09401?q=80&w=1080&auto=format&fit=crop"
        ]
    },
    # 12. Mercy & Divine Solace (Duha, Sharh, Rahman)
    "mercy_solace": {
        "gradient": "linear-gradient(180deg, rgba(28, 82, 98, 0.98) 0%, rgba(36, 102, 122, 0.92) 50%, rgba(36, 102, 122, 0.40) 80%, rgba(0, 0, 0, 0) 100%)",
        "text_color": "#ffffff",
        "shadow": "0 2px 5px rgba(0,0,0,0.85), 0 4px 18px rgba(0,0,0,0.55)",
        "images": [
            "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?q=80&w=1080&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1500382017468-9049fed747ef?q=80&w=1080&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1519817650390-64a93db51149?q=80&w=1080&auto=format&fit=crop"
        ]
    }
}

HISTORY_FILE = "used_images_history.json"

def get_non_repeating_image(theme_key: str) -> str:
    palette = THEME_PALETTES.get(theme_key, THEME_PALETTES["masjid_noor"])
    available_images = palette["images"]
    
    used_history = {}
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                used_history = json.load(f)
        except Exception:
            used_history = {}

    theme_used = used_history.get(theme_key, [])
    unused = [img for img in available_images if img not in theme_used]
    
    if not unused:
        unused = available_images
        theme_used = []

    chosen_image = random.choice(unused)
    theme_used.append(chosen_image)
    used_history[theme_key] = theme_used

    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(used_history, f, indent=2)
    except Exception:
        pass

    return chosen_image

def get_accurate_verse_theme(surah: int, verse_text: str):
    t = verse_text.lower()
    
    # Priority theological keyword recognition
    if any(k in t for k in ["சுவனம்", "தோட்டம்", "நதிகள்", "பயனற்ற", "இன்பம்", "அருட்கொடை", "நிழல்", "கனி"]):
        theme_key = "jannah_gardens"
    elif any(k in t for k in ["கஃபா", "மக்கா", "ஹஜ்", "ஆலயத்தை", "ஹரம்", "கிப்லா"]):
        theme_key = "sacred_sanctuary"
    elif any(k in t for k in ["இறைவழி", "கொல்லப்பட்ட", "பொறுமை", "சோதனை", "உயிரோடு", "போராடு", "தியாகம்"]):
        theme_key = "historic_amber"
    elif any(k in t for k in ["சூழ்ந்து", "கியாம", "கப்று", "எழுப்பப்படும்", "மறுமை", "நடுங்கும்", "சாம்பல்", "மரண", "தீர்ப்பு"]):
        theme_key = "solemn_resurrection"
    elif any(k in t for k in ["கடல்", "மழை", "தண்ணீர்", "மேகம்", "கப்பல்", "அலை"]):
        theme_key = "waters_oceans"
    elif any(k in t for k in ["விடிற்காலை", "பகல்", "சூரியன்", "விடியல்", "பிரகாசம்"]):
        theme_key = "dawn_fajr"
    elif any(k in t for k in ["இரவு", "இரவில்", "நட்சத்திர", "சந்திரன்"]):
        theme_key = "night_layl"
    elif any(k in t for k in ["ஒளி", "நூர்", "வேதம்", "குர்ஆன்", "அறிவு", "சான்று", "நேர்வழி"]):
        theme_key = "masjid_noor"
    elif any(k in t for k in ["பூமி", "மலைகள்", "பாறை", "நிலம்"]):
        theme_key = "earth_mountains"
    else:
        _, _, default_theme = QURAN_DIRECTORY.get(surah, ("ஸூரா", 0, "historic_amber"))
        theme_key = default_theme

    palette = THEME_PALETTES.get(theme_key, THEME_PALETTES["masjid_noor"])
    remote_img_url = get_non_repeating_image(theme_key)
    return palette, remote_img_url

# --- 4. BASE64 ENCODER (PREVENTS BROKEN IMAGES) ---
def get_base64_data_uri(filepath: str, mime: str = "image/jpeg") -> str:
    if os.path.exists(filepath):
        try:
            with open(filepath, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
                return f"data:{mime};base64,{b64}"
        except Exception:
            pass
    return ""

def get_logo_data_uri() -> str:
    for name in ["Logo.png", "logo.png"]:
        if os.path.exists(name):
            return get_base64_data_uri(name, "image/png")
    return ""

def download_image_locally(url: str, local_path: str = "bg_current.jpg") -> str:
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as response, open(local_path, 'wb') as out_file:
            out_file.write(response.read())
        return local_path
    except Exception:
        return local_path

def fetch_any_quran_verse(surah: int, ayah: int):
    if surah < 1 or surah > 114:
        raise ValueError("❌ தவறான ஸூரா எண்! (1 முதல் 114 வரை உள்ள ஸூராவைத் தேர்ந்தெடுக்கவும்).")

    raw_name, max_ayahs, _ = QURAN_DIRECTORY[surah]

    if ayah < 1 or ayah > max_ayahs:
        raise ValueError(f"❌ ஸூரா {raw_name} ({surah})-ல் மொத்தம் {max_ayahs} வசனங்கள் மட்டுமே உள்ளன!\n(1 முதல் {max_ayahs} வரை உள்ள வசனத்தை உள்ளிடவும்).")

    verse_text = ""
    try:
        url = f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/ta.tamil"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get("status") == "OK":
                verse_text = data["data"]["text"].strip()
    except Exception:
        pass

    if not verse_text:
        try:
            cdn_url = f"https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/editions/tam-janturstfoundat/{surah}/{ayah}.json"
            req2 = urllib.request.Request(cdn_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req2, timeout=8) as resp2:
                verse_text = json.loads(resp2.read().decode('utf-8'))["text"].strip()
        except Exception:
            pass

    verse_text = re.sub(r'\s*\(\d+:\d+\)\s*$', '', verse_text).strip()
    verse_text = re.sub(r'[\-\–\—\s]+$', '', verse_text).strip()
    if not verse_text.endswith(('.', '!', '?', '”', '"')):
        verse_text += '.'

    clean_check = verse_text.strip(" .!?-\"'“”")
    if len(clean_check) < 2:
        raise ValueError(f"❌ ஸூரா {raw_name} {surah}:{ayah}-ன் உரை கிடைக்கவில்லை!")

    if raw_name == "ரூம்":
        reference = f"ஸூரத்துர் ரூம் || {surah}:{ayah}"
    elif raw_name == "புரூஜ்":
        reference = f"ஸூரத்துல் புரூஜ் || {surah}:{ayah}"
    elif raw_name == "கஹ்ஃப்":
        reference = f"ஸூரத்துல் கஹ்ஃப் || {surah}:{ayah}"
    elif raw_name == "ஆதியாத்":
        reference = f"ஸூரத்துல் ஆதியாத் || {surah}:{ayah}"
    elif raw_name == "ஸல்ஸலா":
        reference = f"ஸூரத்துஸ் ஸல்ஸலா || {surah}:{ayah}"
    elif raw_name == "ஃகாஷியா":
        reference = f"ஸூரத்துல் ஃகாஷியா || {surah}:{ayah}"
    elif raw_name.startswith("அல்"):
        reference = f"ஸூரத்துல் {raw_name[3:]} || {surah}:{ayah}"
    elif raw_name.startswith("அர்"):
        reference = f"ஸூரத்துர் {raw_name[3:]} || {surah}:{ayah}"
    elif raw_name.startswith("அந்"):
        reference = f"ஸூரத்துந் {raw_name[3:]} || {surah}:{ayah}"
    elif raw_name.startswith("அத்"):
        reference = f"ஸூரத்துத் {raw_name[3:]} || {surah}:{ayah}"
    elif raw_name.startswith("அஷ்"):
        reference = f"ஸூரத்துஷ் {raw_name[3:]} || {surah}:{ayah}"
    elif raw_name.startswith("அஸ்"):
        reference = f"ஸூரத்துஸ் {raw_name[3:]} || {surah}:{ayah}"
    else:
        reference = f"ஸூரத்து {raw_name} || {surah}:{ayah}"

    return verse_text, reference

# --- 5. PRE-WARMED PLAYWRIGHT BROWSER ---
GLOBAL_BROWSER = None
GLOBAL_PLAYWRIGHT = None

async def init_browser():
    global GLOBAL_BROWSER, GLOBAL_PLAYWRIGHT
    GLOBAL_PLAYWRIGHT = await async_playwright().start()
    GLOBAL_BROWSER = await GLOBAL_PLAYWRIGHT.chromium.launch(args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"])
    print("⚡ Pre-warmed Chromium Browser Online!")

async def render_poster(local_image_name: str, tamil_text: str, surah_ref: str, palette: dict, output_path: str):
    global GLOBAL_BROWSER
    char_count = len(tamil_text)
    
    if char_count <= 55:
        font_size = "58px"
        line_height = "1.50"
        padding = "125px 60px 20px 60px"
    elif char_count <= 95:
        font_size = "48px"
        line_height = "1.54"
        padding = "100px 60px 20px 60px"
    elif char_count <= 180:
        font_size = "38px"
        line_height = "1.60"
        padding = "75px 55px 20px 55px"
    elif char_count <= 260:
        font_size = "32px"
        line_height = "1.55"
        padding = "60px 50px 20px 50px"
    else:
        font_size = "29px"
        line_height = "1.50"
        padding = "50px 45px 20px 45px"

    logo_data = get_logo_data_uri()
    bg_data = get_base64_data_uri(local_image_name, "image/jpeg")

    html = TEMPLATE_CONTENT
    html = html.replace("{{LOGO_DATA_URI}}", logo_data)
    html = html.replace("{{IMAGE_DATA_URI}}", bg_data)
    html = html.replace("{{VERSE_TEXT}}", tamil_text)
    html = html.replace("{{SURAH_REF}}", surah_ref)
    html = html.replace("{{DYNAMIC_FONT_SIZE}}", font_size)
    html = html.replace("{{DYNAMIC_LINE_HEIGHT}}", line_height)
    html = html.replace("{{DYNAMIC_PADDING}}", padding)
    html = html.replace("{{GRADIENT_CSS}}", palette["gradient"])
    html = html.replace("{{TEXT_COLOR}}", palette["text_color"])
    html = html.replace("{{TEXT_SHADOW}}", palette["shadow"])

    page = await GLOBAL_BROWSER.new_page(viewport={"width": 1080, "height": 1380})
    await page.set_content(html, wait_until="load")
    await page.evaluate("document.fonts.ready")
    await page.wait_for_timeout(200)
    await page.screenshot(path=output_path)
    await page.close()

# --- 6. TELEGRAM BOT HANDLER ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    match = re.match(r"^(\d{1,3})[:\s](\d{1,3})$", text)

    if not match:
        await update.message.reply_text("ℹ️ Please send Surah and Ayah like: 88:1 or 30:22")
        return

    surah, ayah = int(match.group(1)), int(match.group(2))
    
    try:
        verse_text, reference = fetch_any_quran_verse(surah, ayah)
        status_msg = await update.message.reply_text(f"⚡ Generating {reference} in 2 seconds...")

        palette, remote_img_url = get_accurate_verse_theme(surah, verse_text)
        local_img = download_image_locally(remote_img_url, "bg_current.jpg")

        out_file = f"poster_{surah}_{ayah}.png"
        await render_poster(local_img, verse_text, reference, palette, out_file)

        with open(out_file, "rb") as doc:
            await update.message.reply_document(document=doc, caption=f"✅ {reference}")

        await status_msg.delete()
        if os.path.exists(out_file):
            os.remove(out_file)

    except ValueError as val_err:
        await update.message.reply_text(str(val_err))
    except Exception as err:
        await update.message.reply_text(f"❌ Error: {str(err)}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Assalamu Alaikum! Send any Surah and Ayah (e.g. 88:1 or 30:22) to generate your poster.")

# --- 7. RENDER HEALTH CHECK SERVER ---
class HealthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot is Healthy and Live!")
    def log_message(self, format, *args):
        pass

def run_render_server():
    port = int(os.environ.get("PORT", 10000))
    with socketserver.TCPServer(("", port), HealthHandler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_render_server, daemon=True).start()

# --- 8. START BOT ---
async def main():
    await init_browser()
    req = HTTPXRequest(connect_timeout=60.0, read_timeout=60.0)
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).request(req).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ High-Speed 12-Macro-Theme Cloud Engine Online!")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
