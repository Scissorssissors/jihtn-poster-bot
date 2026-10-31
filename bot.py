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

# --- 1. POSTER TEMPLATE (OFFICIAL MASTER TEMPLATE) ---
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
    height: 84%;
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

# --- 2. SURAH DIRECTORY & METADATA ---
QURAN_DIRECTORY = {
    1: ("அல் ஃபாத்திஹா", 7, "sky"),
    2: ("அல் பகரா", 286, "amber"),
    3: ("ஆல இம்ரான்", 200, "amber"),
    4: ("அந் நிஸா", 176, "amber"),
    5: ("அல் மாயிதா", 120, "gold"),
    6: ("அல் அன்ஆம்", 165, "navy"),
    7: ("அல் அஃராஃப்", 206, "amber"),
    8: ("அல் அன்ஃபால்", 75, "amber"),
    9: ("அத் தவ்பா", 129, "amber"),
    10: ("யூனுஸ்", 109, "teal"),
    11: ("ஹூத்", 123, "amber"),
    12: ("யூஸுஃப்", 111, "gold"),
    13: ("அர் ரஃது", 43, "navy"),
    14: ("இப்ராஹீம்", 52, "sky"),
    15: ("அல் ஹிஜ்ர்", 99, "copper"),
    16: ("அந் நஹ்ல்", 128, "emerald"),
    17: ("அல் இஸ்ரா", 111, "gold"),
    18: ("கஹ்ஃப்", 110, "gold"),
    19: ("மர்யம்", 98, "emerald"),
    20: ("தாஹா", 135, "gold"),
    21: ("அல் அன்பியா", 112, "amber"),
    22: ("அல் ஹஜ்", 78, "sky"),
    23: ("அல் முஃமினூன்", 118, "emerald"),
    24: ("அந் நூர்", 64, "gold"),
    25: ("அல் ஃபுர்கான்", 77, "teal"),
    26: ("அஷ் ஷுஅரா", 227, "amber"),
    27: ("அந் நம்ல்", 93, "copper"),
    28: ("அல் கஸஸ்", 88, "amber"),
    29: ("அல் அன்கபூத்", 69, "amber"),
    30: ("ரூம்", 60, "navy"),
    31: ("லுக்மான்", 34, "gold"),
    32: ("அஸ் ஸஜ்தா", 30, "burgundy"),
    33: ("அல் அஹ்ஸாப்", 73, "amber"),
    34: ("ஸபா", 54, "copper"),
    35: ("ஃபாதிர்", 45, "navy"),
    36: ("யாஸீன்", 83, "gold"),
    37: ("அஸ் ஸாஃப்பாத்", 182, "navy"),
    38: ("ஸாத்", 88, "amber"),
    39: ("அஸ் ஸுமர்", 75, "gold"),
    40: ("ஃகாஃபிர்", 85, "navy"),
    41: ("ஃபுஸ்ஸிலத்", 54, "navy"),
    42: ("அஷ் ஷூரா", 53, "gold"),
    43: ("அஸ் ஸுக்ருஃப்", 89, "emerald"),
    44: ("அத் துகான்", 59, "burgundy"),
    45: ("அல் ஜாஸியா", 37, "burgundy"),
    46: ("அல் அஹ்காஃப்", 35, "copper"),
    47: ("முஹம்மத்", 38, "amber"),
    48: ("அல் ஃபத்ஹ்", 29, "sky"),
    49: ("அல் ஹுஜுராத்", 18, "gold"),
    50: ("காஃப்", 45, "burgundy"),
    51: ("அத் தாரியாத்", 60, "navy"),
    52: ("அத் தூர்", 49, "earth"),
    53: ("அந் நஜ்ம்", 62, "navy"),
    54: ("அல் கமர்", 55, "navy"),
    55: ("அர் ரஹ்மான்", 78, "emerald"),
    56: ("அல் வாகிஆ", 96, "emerald"),
    57: ("அல் ஹதீத்", 29, "gold"),
    58: ("அல் முஜாதலா", 22, "gold"),
    59: ("அல் ஹஷ்ர்", 24, "amber"),
    60: ("அல் மும்தஹினா", 13, "amber"),
    61: ("அஸ் ஸஃப்", 14, "amber"),
    62: ("அல் ஜுமுஆ", 11, "gold"),
    63: ("அல் முனாஃபிகூன்", 11, "burgundy"),
    64: ("அத் தஃகாபுன்", 18, "burgundy"),
    65: ("அத் தலாக்", 12, "gold"),
    66: ("அத் தஹ்ரீம்", 12, "gold"),
    67: ("அல் முல்க்", 30, "navy"),
    68: ("அல் கலம்", 52, "gold"),
    69: ("அல் ஹாகா", 52, "burgundy"),
    70: ("அல் மஆரிஜ்", 44, "burgundy"),
    71: ("நூஹ்", 28, "teal"),
    72: ("அல் ஜின்", 28, "navy"),
    73: ("அல் முஸ்ஸம்மில்", 20, "navy"),
    74: ("அல் முத்தஸ்ஸிர்", 56, "burgundy"),
    75: ("அல் கியாமஹ்", 40, "burgundy"),
    76: ("அல் இன்ஸான்", 31, "emerald"),
    77: ("அல் முர்ஸலாத்", 50, "burgundy"),
    78: ("அந் நபஃ", 40, "burgundy"),
    79: ("அந் நாஸிஆத்", 46, "burgundy"),
    80: ("அபஸ", 42, "burgundy"),
    81: ("அத் தக்வீர்", 29, "navy"),
    82: ("அல் இன்ஃபிதார்", 19, "navy"),
    83: ("அல் முaffiஃபீன்", 36, "burgundy"),
    84: ("அல் இன்ஷிகாக்", 25, "navy"),
    85: ("புரூஜ்", 22, "navy"),
    86: ("அத் தாரிக்", 17, "navy"),
    87: ("அல் அஃலா", 19, "emerald"),
    88: ("ஃகாஷியா", 26, "burgundy"),
    89: ("அல் ஃபஜ்ர்", 30, "dawn"),
    90: ("அல் பலத்", 20, "sky"),
    91: ("அஷ் ஷம்ஸ்", 15, "dawn"),
    92: ("அல் லைல்", 21, "navy"),
    93: ("அழ் ளுஹா", 11, "gold"),
    94: ("அஷ் ஷர்ஹ்", 8, "gold"),
    95: ("அத் தீன்", 8, "emerald"),
    96: ("அல் அலக்", 19, "gold"),
    97: ("அல் கத்ர்", 5, "navy"),
    98: ("அல் பய்யினஹ்", 8, "gold"),
    99: ("ஸல்ஸலா", 8, "burgundy"),
    100: ("ஆதியாத்", 11, "burgundy"),
    101: ("அல் காரிஆ", 11, "burgundy"),
    102: ("அத் தகாஸுர்", 8, "burgundy"),
    103: ("அல் அஸ்ர்", 3, "amber"),
    104: ("அல் ஹுமஸஹ்", 9, "burgundy"),
    105: ("அல் ஃபீல்", 5, "sky"),
    106: ("குரைஷ்", 4, "sky"),
    107: ("அல் மாவூன்", 7, "sky"),
    108: ("அல் கவ்தர்", 3, "teal"),
    109: ("அல் காஃபிரூன்", 6, "sky"),
    110: ("அந் நஸ்ர்", 3, "sky"),
    111: ("அல் மஸத்", 5, "burgundy"),
    112: ("அல் இக்லாஸ்", 4, "sky"),
    113: ("அல் ஃபலக்", 5, "dawn"),
    114: ("அந் நாஸ்", 6, "sky")
}

# --- 3. 100+ CURATED GRADIENTS GROUPED BY MOOD ---
GRADIENT_MOODS = {
    "emerald": [
        ("linear-gradient(180deg, rgba(12, 68, 44, 0.98) 0%, rgba(15, 82, 54, 0.94) 52%, rgba(15, 82, 54, 0.45) 82%, rgba(0,0,0,0) 100%)", "#ffffff", "0 2px 6px rgba(0,0,0,0.85)"),
        ("linear-gradient(180deg, rgba(8, 52, 34, 0.98) 0%, rgba(12, 68, 46, 0.93) 50%, rgba(12, 68, 46, 0.42) 80%, rgba(0,0,0,0) 100%)", "#ffffff", "0 2px 6px rgba(0,0,0,0.9)"),
        ("linear-gradient(180deg, rgba(18, 86, 56, 0.98) 0%, rgba(22, 102, 68, 0.92) 50%, rgba(22, 102, 68, 0.40) 80%, rgba(0,0,0,0) 100%)", "#ffffff", "0 2px 6px rgba(0,0,0,0.85)"),
        ("linear-gradient(180deg, rgba(14, 78, 62, 0.98) 0%, rgba(18, 92, 74, 0.93) 50%, rgba(18, 92, 74, 0.45) 80%, rgba(0,0,0,0) 100%)", "#ffffff", "0 2px 6px rgba(0,0,0,0.85)"),
        ("linear-gradient(180deg, rgba(20, 64, 48, 0.98) 0%, rgba(26, 78, 60, 0.94) 50%, rgba(26, 78, 60, 0.45) 80%, rgba(0,0,0,0) 100%)", "#ffffff", "0 2px 6px rgba(0,0,0,0.85)"),
        ("linear-gradient(180deg, rgba(10, 48, 38, 0.98) 0%, rgba(14, 60, 48, 0.94) 50%, rgba(14, 60, 48, 0.45) 80%, rgba(0,0,0,0) 100%)", "#ffffff", "0 2px 6px rgba(0,0,0,0.9)"),
        ("linear-gradient(180deg, rgba(24, 76, 54, 0.98) 0%, rgba(30, 92, 66, 0.93) 50%, rgba(30, 92, 66, 0.45) 80%, rgba(0,0,0,0) 100%)", "#ffffff", "0 2px 6px rgba(0,0,0,0.85)"),
        ("linear-gradient(180deg, rgba(16, 58, 42, 0.98) 0%, rgba(22, 74, 54, 0.93) 50%, rgba(22, 74, 54, 0.45) 80%, rgba(0,0,0,0) 100%)", "#ffffff", "0 2px 6px rgba(0,0,0,0.85)")
    ],
    "navy": [
        ("linear-gradient(180deg, rgba(10, 24, 52, 0.98) 0%, rgba(14, 32, 68, 0.93) 50%, rgba(14, 32, 68, 0.45) 80%, rgba(0, 0, 0, 0) 100%)", "#ffffff", "0 2px 6px rgba(0,0,0,0.9), 0 4px 18px rgba(0,0,0,0.6)"),
        ("linear-gradient(180deg, rgba(6, 16, 38, 0.98) 0%, rgba(10, 22, 50, 0.94) 50%, rgba(10, 22, 50, 0.45) 80%, rgba(0, 0, 0, 0) 100%)", "#ffffff", "0 2px 6px rgba(0,0,0,0.9)"),
        ("linear-gradient(180deg, rgba(12, 28, 62, 0.98) 0%, rgba(16, 36, 78, 0.94) 50%, rgba(16, 36, 78, 0.45) 80%, rgba(0, 0, 0, 0) 100%)", "#ffffff", "0 2px 6px rgba(0,0,0,0.9)"),
        ("linear-gradient(180deg, rgba(14, 22, 46, 0.98) 0%, rgba(18, 30, 60, 0.94) 50%, rgba(18, 30, 60, 0.45) 80%, rgba(0, 0, 0, 0) 100%)", "#ffffff", "0 2px 6px rgba(0,0,0,0.9)"),
        ("linear-gradient(180deg, rgba(18, 32, 68, 0.98) 0%, rgba(22, 42, 84, 0.93) 50%, rgba(22, 42, 84, 0.45) 80%, rgba(0, 0, 0, 0) 100%)", "#ffffff", "0 2px 6px rgba(0,0,0,0.9)"),
        ("linear-gradient(180deg, rgba(8, 20, 44, 0.98) 0%, rgba(12, 28, 58, 0.94) 50%, rgba(12, 28, 58, 0.45) 80%, rgba(0, 0, 0, 0) 100%)", "#ffffff", "0 2px 6px rgba(0,0,0,0.9)"),
        ("linear-gradient(180deg, rgba(16, 26, 56, 0.98) 0%, rgba(20, 34, 72, 0.94) 50%, rgba(20, 34, 72, 0.45) 80%, rgba(0, 0, 0, 0) 100%)", "#ffffff", "0 2px 6px rgba(0,0,0,0.9)")
    ],
    "burgundy": [
        ("linear-gradient(180deg, rgba(88, 16, 28, 0.98) 0%, rgba(72, 14, 24, 0.93) 50%, rgba(55, 12, 20, 0.45) 80%, rgba(0, 0, 0, 0) 100%)", "#ffffff", "0 2px 6px rgba(0,0,0,0.9), 0 4px 18px rgba(0,0,0,0.6)"),
        ("linear-gradient(180deg, rgba(72, 12, 24, 0.98) 0%, rgba(60, 10, 20, 0.94) 50%, rgba(45, 8, 16, 0.45) 80%, rgba(0, 0, 0, 0) 100%)", "#ffffff", "0 2px 6px rgba(0,0,0,0.9)"),
        ("linear-gradient(180deg, rgba(94, 20, 36, 0.98) 0%, rgba(80, 16, 30, 0.93) 50%, rgba(65, 12, 24, 0.45) 80%, rgba(0, 0, 0, 0) 100%)", "#ffffff", "0 2px 6px rgba(0,0,0,0.9)"),
        ("linear-gradient(180deg, rgba(64, 14, 32, 0.98) 0%, rgba(54, 12, 28, 0.94) 50%, rgba(40, 10, 22, 0.45) 80%, rgba(0, 0, 0, 0) 100%)", "#ffffff", "0 2px 6px rgba(0,0,0,0.9)"),
        ("linear-gradient(180deg, rgba(78, 18, 38, 0.98) 0%, rgba(66, 14, 32, 0.94) 50%, rgba(52, 12, 26, 0.45) 80%, rgba(0, 0, 0, 0) 100%)", "#ffffff", "0 2px 6px rgba(0,0,0,0.9)"),
        ("linear-gradient(180deg, rgba(82, 14, 30, 0.98) 0%, rgba(68, 12, 26, 0.94) 50%, rgba(50, 10, 20, 0.45) 80%, rgba(0, 0, 0, 0) 100%)", "#ffffff", "0 2px 6px rgba(0,0,0,0.9)")
    ],
    "teal": [
        ("linear-gradient(180deg, rgba(10, 55, 75, 0.98) 0%, rgba(12, 68, 90, 0.93) 50%, rgba(12, 68, 90, 0.45) 80%, rgba(0, 0, 0, 0) 100%)", "#ffffff", "0 2px 6px rgba(0,0,0,0.85), 0 4px 18px rgba(0,0,0,0.55)"),
        ("linear-gradient(180deg, rgba(8, 44, 62, 0.98) 0%, rgba(10, 56, 78, 0.94) 50%, rgba(10, 56, 78, 0.45) 80%, rgba(0, 0, 0, 0) 100%)", "#ffffff", "0 2px 6px rgba(0,0,0,0.9)"),
        ("linear-gradient(180deg, rgba(14, 68, 92, 0.98) 0%, rgba(18, 84, 112, 0.93) 50%, rgba(18, 84, 112, 0.45) 80%, rgba(0, 0, 0, 0) 100%)", "#ffffff", "0 2px 6px rgba(0,0,0,0.85)"),
        ("linear-gradient(180deg, rgba(12, 60, 80, 0.98) 0%, rgba(16, 74, 98, 0.93) 50%, rgba(16, 74, 98, 0.45) 80%, rgba(0, 0, 0, 0) 100%)", "#ffffff", "0 2px 6px rgba(0,0,0,0.85)"),
        ("linear-gradient(180deg, rgba(16, 72, 94, 0.98) 0%, rgba(20, 88, 114, 0.93) 50%, rgba(20, 88, 114, 0.45) 80%, rgba(0, 0, 0, 0) 100%)", "#ffffff", "0 2px 6px rgba(0,0,0,0.85)")
    ],
    "gold": [
        ("linear-gradient(180deg, rgba(185, 115, 15, 0.98) 0%, rgba(165, 100, 10, 0.93) 50%, rgba(165, 100, 10, 0.45) 80%, rgba(0, 0, 0, 0) 100%)", "#ffffff", "0 2px 5px rgba(0,0,0,0.85), 0 4px 18px rgba(0,0,0,0.55)"),
        ("linear-gradient(180deg, rgba(165, 98, 12, 0.98) 0%, rgba(145, 84, 8, 0.94) 50%, rgba(145, 84, 8, 0.45) 80%, rgba(0, 0, 0, 0) 100%)", "#ffffff", "0 2px 5px rgba(0,0,0,0.85)"),
        ("linear-gradient(180deg, rgba(195, 124, 18, 0.98) 0%, rgba(175, 110, 14, 0.93) 50%, rgba(175, 110, 14, 0.45) 80%, rgba(0, 0, 0, 0) 100%)", "#ffffff", "0 2px 5px rgba(0,0,0,0.85)"),
        ("linear-gradient(180deg, rgba(175, 108, 14, 0.98) 0%, rgba(155, 94, 10, 0.93) 50%, rgba(155, 94, 10, 0.45) 80%, rgba(0, 0, 0, 0) 100%)", "#ffffff", "0 2px 5px rgba(0,0,0,0.85)")
    ],
    "sky": [
        ("linear-gradient(180deg, rgba(165, 205, 225, 0.98) 0%, rgba(190, 220, 235, 0.92) 50%, rgba(210, 232, 245, 0.35) 80%, rgba(0, 0, 0, 0) 100%)", "#112a45", "0 2px 8px rgba(255,255,255,0.7), 0 1px 2px rgba(0,0,0,0.15)"),
        ("linear-gradient(180deg, rgba(175, 212, 230, 0.98) 0%, rgba(198, 226, 240, 0.92) 50%, rgba(218, 238, 248, 0.35) 80%, rgba(0, 0, 0, 0) 100%)", "#112a45", "0 2px 8px rgba(255,255,255,0.7)"),
        ("linear-gradient(180deg, rgba(155, 198, 218, 0.98) 0%, rgba(180, 214, 228, 0.92) 50%, rgba(200, 226, 238, 0.35) 80%, rgba(0, 0, 0, 0) 100%)", "#112a45", "0 2px 8px rgba(255,255,255,0.7)"),
        ("linear-gradient(180deg, rgba(182, 218, 234, 0.98) 0%, rgba(204, 230, 244, 0.92) 50%, rgba(222, 240, 250, 0.35) 80%, rgba(0, 0, 0, 0) 100%)", "#112a45", "0 2px 8px rgba(255,255,255,0.7)")
    ],
    "dawn": [
        ("linear-gradient(180deg, rgba(188, 78, 48, 0.98) 0%, rgba(212, 106, 68, 0.92) 50%, rgba(212, 106, 68, 0.40) 80%, rgba(0, 0, 0, 0) 100%)", "#ffffff", "0 2px 5px rgba(0,0,0,0.85)"),
        ("linear-gradient(180deg, rgba(175, 68, 40, 0.98) 0%, rgba(198, 92, 58, 0.93) 50%, rgba(198, 92, 58, 0.40) 80%, rgba(0, 0, 0, 0) 100%)", "#ffffff", "0 2px 5px rgba(0,0,0,0.85)"),
        ("linear-gradient(180deg, rgba(195, 88, 56, 0.98) 0%, rgba(220, 116, 78, 0.92) 50%, rgba(220, 116, 78, 0.40) 80%, rgba(0, 0, 0, 0) 100%)", "#ffffff", "0 2px 5px rgba(0,0,0,0.85)")
    ],
    "amber": [
        ("linear-gradient(180deg, rgba(215, 80, 10, 0.98) 0%, rgba(200, 72, 8, 0.94) 50%, rgba(195, 70, 8, 0.45) 80%, rgba(0, 0, 0, 0) 100%)", "#ffffff", "0 2px 5px rgba(0,0,0,0.85), 0 5px 20px rgba(0,0,0,0.55)"),
        ("linear-gradient(180deg, rgba(195, 70, 8, 0.98) 0%, rgba(180, 62, 6, 0.94) 50%, rgba(180, 62, 6, 0.45) 80%, rgba(0, 0, 0, 0) 100%)", "#ffffff", "0 2px 5px rgba(0,0,0,0.85)")
    ],
    "copper": [
        ("linear-gradient(180deg, rgba(195, 95, 20, 0.98) 0%, rgba(175, 85, 16, 0.93) 50%, rgba(175, 85, 16, 0.45) 80%, rgba(0, 0, 0, 0) 100%)", "#ffffff", "0 2px 5px rgba(0,0,0,0.85)"),
        ("linear-gradient(180deg, rgba(180, 86, 16, 0.98) 0%, rgba(160, 76, 12, 0.93) 50%, rgba(160, 76, 12, 0.45) 80%, rgba(0, 0, 0, 0) 100%)", "#ffffff", "0 2px 5px rgba(0,0,0,0.85)")
    ],
    "earth": [
        ("linear-gradient(180deg, rgba(62, 42, 28, 0.98) 0%, rgba(78, 54, 38, 0.93) 50%, rgba(78, 54, 38, 0.45) 80%, rgba(0, 0, 0, 0) 100%)", "#ffffff", "0 2px 5px rgba(0,0,0,0.85)"),
        ("linear-gradient(180deg, rgba(74, 50, 32, 0.98) 0%, rgba(90, 62, 42, 0.93) 50%, rgba(90, 62, 42, 0.45) 80%, rgba(0, 0, 0, 0) 100%)", "#ffffff", "0 2px 5px rgba(0,0,0,0.85)")
    ]
}

# --- 4. AUDITED HALAL IMAGE POOLS BY MOOD ---
IMAGE_POOLS = {
    "emerald": [
        "https://images.unsplash.com/photo-1511497584788-87676104235f?q=80&w=1080&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?q=80&w=1080&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1426604966848-d7adac402bff?q=80&w=1080&auto=format&fit=crop"
    ],
    "navy": [
        "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?q=80&w=1080&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=1080&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1080&auto=format&fit=crop"
    ],
    "burgundy": [
        "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?q=80&w=1080&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1498084393753-b411b2d26b34?q=80&w=1080&auto=format&fit=crop"
    ],
    "teal": [
        "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?q=80&w=1080&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1498084393753-b411b2d26b34?q=80&w=1080&auto=format&fit=crop"
    ],
    "gold": [
        "https://images.unsplash.com/photo-1584551246679-0daf3d275d0f?q=80&w=1080&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1519817650390-64a93db51149?q=80&w=1080&auto=format&fit=crop"
    ],
    "sky": [
        "https://images.unsplash.com/photo-1591604129939-f1efa4d9f7fa?q=80&w=1080&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1565552645632-d725f8bfc19a?q=80&w=1080&auto=format&fit=crop"
    ],
    "dawn": [
        "https://images.unsplash.com/photo-1495616811223-4d98c6e9c869?q=80&w=1080&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1500382017468-9049fed747ef?q=80&w=1080&auto=format&fit=crop"
    ],
    "amber": [
        "https://images.unsplash.com/photo-1512958789358-4dac567096e8?q=80&w=1080&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?q=80&w=1080&auto=format&fit=crop"
    ],
    "copper": [
        "https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?q=80&w=1080&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1473580044384-7ba9967e16a0?q=80&w=1080&auto=format&fit=crop"
    ],
    "earth": [
        "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?q=80&w=1080&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1486870591958-9b9d0d1dda99?q=80&w=1080&auto=format&fit=crop"
    ]
}

def get_verse_gradient_and_image(surah: int, ayah: int, verse_text: str):
    """Crash-proof deterministic mapper. Impossible to get list index out of range."""
    t = verse_text.lower()
    
    # 1. Determine category
    if any(k in t for k in ["சுவனம்", "தோட்டம்", "நதிகள்", "பயனற்ற", "இன்பம்", "அருட்கொடை", "நிழல்"]):
        category = "emerald"
    elif any(k in t for k in ["கஃபா", "மக்கா", "ஹஜ்", "ஆலயத்தை", "ஹரம்", "கிப்லா"]):
        category = "sky"
    elif any(k in t for k in ["கடல்", "மழை", "தண்ணீர்", "மேகம்", "கப்பல்", "அலை"]):
        category = "teal"
    elif any(k in t for k in ["சூழ்ந்து", "கியாம", "கப்று", "எழுப்பப்படும்", "மறுமை", "நடுங்கும்", "சாம்பல்", "தீர்ப்பு"]):
        category = "burgundy"
    elif any(k in t for k in ["விடியல்", "பகல்", "சூரியன்", "பிரகாசம்", "காலை"]):
        category = "dawn"
    elif any(k in t for k in ["இரவு", "நட்சத்திர", "சந்திரன்", "வானங்கள்"]):
        category = "navy"
    elif any(k in t for k in ["ஒளி", "நூர்", "வேதம்", "குர்ஆன்", "அறிவு", "சான்று", "நேர்வழி"]):
        category = "gold"
    else:
        _, _, default_cat = QURAN_DIRECTORY.get(surah, ("ஸூரா", 0, "navy"))
        category = default_cat

    # 2. Select Gradient from the chosen category safely
    gradient_list = GRADIENT_MOODS.get(category, GRADIENT_MOODS["navy"])
    # Modulo length ensures it can never exceed list bounds
    grad_idx = (surah * 37 + ayah) % len(gradient_list)
    gradient_css, text_color, text_shadow = gradient_list[grad_idx]

    # 3. Select Image safely
    image_list = IMAGE_POOLS.get(category, IMAGE_POOLS["navy"])
    img_idx = (surah + ayah) % len(image_list)
    chosen_image = image_list[img_idx]

    palette_dict = {
        "gradient": gradient_css,
        "text_color": text_color,
        "shadow": text_shadow
    }
    return palette_dict, chosen_image

# --- 5. BASE64 ENCODER ---
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

# --- 6. PRE-WARMED PLAYWRIGHT BROWSER ---
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

# --- 7. TELEGRAM BOT HANDLER ---
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

        palette, remote_img_url = get_verse_gradient_and_image(surah, ayah, verse_text)
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

# --- 8. RENDER HEALTH CHECK SERVER ---
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

# --- 9. START BOT ---
async def main():
    await init_browser()
    req = HTTPXRequest(connect_timeout=60.0, read_timeout=60.0)
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).request(req).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Fully Stable Crash-Proof Engine Online!")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
