#!/usr/bin/env python3
"""
Voicing Designer — generates beautiful chord voicing diagrams.
Outputs polished HTML/SVG for both piano and guitar diagrams.
"""

import sys
import json
from dataclasses import dataclass

# ─── Color Themes ────────────────────────────────────────────────

THEMES = {
    "midnight": {
        "bg": "#0f0f1a",
        "card_bg": "#1a1a2e",
        "card_border": "#2a2a4a",
        "title": "#e8e8f0",
        "subtitle": "#8888aa",
        "text": "#ccccdd",
        "text_muted": "#666680",
        "accent": "#6c63ff",
        "accent_glow": "rgba(108, 99, 255, 0.3)",
        "highlight_white_key": "#6c63ff",
        "highlight_black_key": "#ff6b6b",
        "white_key": "#f0f0f5",
        "white_key_border": "#d0d0dd",
        "black_key": "#1a1a2e",
        "black_key_border": "#000",
        "fret_line": "#444466",
        "string_line": "#555577",
        "fret_dot": "#6c63ff",
        "fret_dot_open": "#6c63ff",
        "fret_dot_muted": "#ff6b6b",
        "nut": "#e8e8f0",
    },
    "warm": {
        "bg": "#1a1410",
        "card_bg": "#2a2018",
        "card_border": "#3d3028",
        "title": "#f0e6d8",
        "subtitle": "#aa9580",
        "text": "#ddd0c0",
        "text_muted": "#807060",
        "accent": "#e8a84c",
        "accent_glow": "rgba(232, 168, 76, 0.3)",
        "highlight_white_key": "#e8a84c",
        "highlight_black_key": "#e85c4c",
        "white_key": "#f5f0e8",
        "white_key_border": "#d8d0c4",
        "black_key": "#2a2018",
        "black_key_border": "#000",
        "fret_line": "#4a3d30",
        "string_line": "#5a4d40",
        "fret_dot": "#e8a84c",
        "fret_dot_open": "#e8a84c",
        "fret_dot_muted": "#e85c4c",
        "nut": "#f0e6d8",
    },
    "ocean": {
        "bg": "#0a1628",
        "card_bg": "#122040",
        "card_border": "#1e3460",
        "title": "#e0eaf8",
        "subtitle": "#6890bb",
        "text": "#b0c8e8",
        "text_muted": "#4a6888",
        "accent": "#00d4aa",
        "accent_glow": "rgba(0, 212, 170, 0.25)",
        "highlight_white_key": "#00d4aa",
        "highlight_black_key": "#ff7eb3",
        "white_key": "#e8f0f8",
        "white_key_border": "#c8d8e8",
        "black_key": "#122040",
        "black_key_border": "#000",
        "fret_line": "#2a4060",
        "string_line": "#3a5070",
        "fret_dot": "#00d4aa",
        "fret_dot_open": "#00d4aa",
        "fret_dot_muted": "#ff7eb3",
        "nut": "#e0eaf8",
    },
}

# ─── Note Parsing ────────────────────────────────────────────────

NOTE_SEMITONES = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
BLACK_SEMITONES = {1, 3, 6, 8, 10}
BLACK_X_OFFSETS = {1: 0.58, 3: 1.72, 6: 3.58, 8: 4.63, 10: 5.72}


def parse_note(note_str):
    """Parse 'C#4' -> (display_name, midi_number)."""
    name = note_str[0].upper()
    rest = note_str[1:]
    acc = 0
    i = 0
    while i < len(rest) and rest[i] in '#b':
        acc += 1 if rest[i] == '#' else -1
        i += 1
    octave = int(rest[i:])
    midi = (octave + 1) * 12 + NOTE_SEMITONES[name] + acc
    return note_str, midi


# ─── Piano Keyboard SVG ─────────────────────────────────────────

def piano_svg(chord_name, notes, theme, subtitle=""):
    t = THEMES[theme]
    parsed = [parse_note(n) for n in notes]
    midis = {m for _, m in parsed}
    midi_to_label = {}
    for label, m in parsed:
        midi_to_label[m] = label

    min_m, max_m = min(midis), max(midis)
    start = ((min_m // 12) - 1) * 12
    end = ((max_m // 12) + 1) * 12 + 12
    start, end = max(start, 24), min(end, 96)

    WK_W, WK_H = 30, 110
    BK_W, BK_H = 20, 68

    white_keys = []
    all_keys = []
    for midi in range(start, end):
        semi = midi % 12
        is_black = semi in BLACK_SEMITONES
        all_keys.append((midi, semi, is_black))
        if not is_black:
            white_keys.append(midi)

    num_white = len(white_keys)
    kb_w = num_white * WK_W
    pad = 30
    total_w = kb_w + pad * 2
    total_h = WK_H + 100

    s = []
    s.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="{total_h}" viewBox="0 0 {total_w} {total_h}">')

    # Defs for glow filter and gradients
    s.append('''<defs>
      <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur stdDeviation="4" result="blur"/>
        <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
      </filter>
      <linearGradient id="whiteKeyGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#ffffff"/>
        <stop offset="100%" stop-color="#e8e8ee"/>
      </linearGradient>
      <linearGradient id="blackKeyGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#333"/>
        <stop offset="100%" stop-color="#111"/>
      </linearGradient>
    </defs>''')

    # Title
    s.append(f'<text x="{total_w/2}" y="28" text-anchor="middle" '
             f'font-family="\'SF Pro Display\', \'Helvetica Neue\', sans-serif" '
             f'font-size="20" font-weight="600" fill="{t["title"]}" '
             f'letter-spacing="1">{chord_name}</text>')
    if subtitle:
        s.append(f'<text x="{total_w/2}" y="46" text-anchor="middle" '
                 f'font-family="\'SF Pro Text\', \'Helvetica Neue\', sans-serif" '
                 f'font-size="12" fill="{t["subtitle"]}" letter-spacing="0.5">{subtitle}</text>')

    kb_x, kb_y = pad, 58

    # Shadow under keyboard
    s.append(f'<rect x="{kb_x - 2}" y="{kb_y + 2}" width="{kb_w + 4}" height="{WK_H + 4}" '
             f'rx="4" fill="rgba(0,0,0,0.3)" filter="url(#glow)"/>')

    # White keys
    white_positions = {}
    for i, midi in enumerate(white_keys):
        x = kb_x + i * WK_W
        white_positions[midi] = x
        if midi in midis:
            fill = t["highlight_white_key"]
            s.append(f'<rect x="{x}" y="{kb_y}" width="{WK_W - 1}" height="{WK_H}" '
                     f'rx="3" fill="{fill}" filter="url(#glow)"/>')
            # Label
            s.append(f'<text x="{x + WK_W/2 - 0.5}" y="{kb_y + WK_H - 12}" text-anchor="middle" '
                     f'font-family="\'SF Mono\', \'Fira Code\', monospace" font-size="10" '
                     f'fill="white" font-weight="600">{midi_to_label[midi]}</text>')
        else:
            s.append(f'<rect x="{x}" y="{kb_y}" width="{WK_W - 1}" height="{WK_H}" '
                     f'rx="3" fill="url(#whiteKeyGrad)" stroke="{t["white_key_border"]}" stroke-width="0.5"/>')

    # Black keys
    for midi, semi, is_black in all_keys:
        if not is_black:
            continue
        oct_c = (midi // 12) * 12
        if oct_c not in white_positions:
            continue
        ox = white_positions[oct_c]
        x = ox + BLACK_X_OFFSETS[semi] * WK_W - BK_W / 2
        if midi in midis:
            fill = t["highlight_black_key"]
            s.append(f'<rect x="{x}" y="{kb_y}" width="{BK_W}" height="{BK_H}" '
                     f'rx="3" fill="{fill}" filter="url(#glow)"/>')
            s.append(f'<text x="{x + BK_W/2}" y="{kb_y + BK_H - 10}" text-anchor="middle" '
                     f'font-family="\'SF Mono\', \'Fira Code\', monospace" font-size="8" '
                     f'fill="white" font-weight="600">{midi_to_label[midi]}</text>')
        else:
            s.append(f'<rect x="{x}" y="{kb_y}" width="{BK_W}" height="{BK_H}" '
                     f'rx="3" fill="url(#blackKeyGrad)" stroke="{t["black_key_border"]}" stroke-width="0.5"/>')

    s.append('</svg>')
    return '\n'.join(s)


# ─── Guitar Fretboard SVG ───────────────────────────────────────

def guitar_svg(chord_name, frets, theme, subtitle=""):
    """
    frets: list of 6 values (low E to high E).
           int = fret number, 'x' = muted, 0 = open.
           Can also be tuple (fret, finger_label).
    """
    t = THEMES[theme]

    NUM_STRINGS = 6
    NUM_FRETS = 5
    STR_SPACING = 24
    FRET_SPACING = 30
    PAD_X, PAD_Y = 40, 70
    DOT_R = 8

    grid_w = (NUM_STRINGS - 1) * STR_SPACING
    grid_h = NUM_FRETS * FRET_SPACING
    total_w = grid_w + PAD_X * 2
    total_h = grid_h + PAD_Y + 60

    # Determine min fret for position indicator
    fret_nums = []
    for f in frets:
        val = f[0] if isinstance(f, tuple) else f
        if isinstance(val, int) and val > 0:
            fret_nums.append(val)

    min_fret = min(fret_nums) if fret_nums else 1
    max_fret = max(fret_nums) if fret_nums else 1
    start_fret = 1
    if max_fret > NUM_FRETS:
        start_fret = min_fret

    show_nut = (start_fret == 1)

    s = []
    s.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="{total_h}" viewBox="0 0 {total_w} {total_h}">')

    # Glow filter
    s.append('''<defs>
      <filter id="dotglow" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur stdDeviation="3" result="blur"/>
        <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
      </filter>
      <radialGradient id="dotGrad" cx="40%" cy="35%" r="60%">
        <stop offset="0%" stop-color="#fff" stop-opacity="0.3"/>
        <stop offset="100%" stop-color="#fff" stop-opacity="0"/>
      </radialGradient>
    </defs>''')

    # Title
    s.append(f'<text x="{total_w/2}" y="24" text-anchor="middle" '
             f'font-family="\'SF Pro Display\', \'Helvetica Neue\', sans-serif" '
             f'font-size="20" font-weight="600" fill="{t["title"]}" '
             f'letter-spacing="1">{chord_name}</text>')
    if subtitle:
        s.append(f'<text x="{total_w/2}" y="42" text-anchor="middle" '
                 f'font-family="\'SF Pro Text\', \'Helvetica Neue\', sans-serif" '
                 f'font-size="12" fill="{t["subtitle"]}" letter-spacing="0.5">{subtitle}</text>')

    gx = PAD_X
    gy = PAD_Y

    # Nut or position indicator
    if show_nut:
        s.append(f'<rect x="{gx - 2}" y="{gy - 4}" width="{grid_w + 4}" height="5" '
                 f'rx="2" fill="{t["nut"]}"/>')
    else:
        s.append(f'<text x="{gx - 18}" y="{gy + FRET_SPACING/2 + 5}" text-anchor="middle" '
                 f'font-family="\'SF Mono\', monospace" font-size="12" '
                 f'fill="{t["text_muted"]}">{start_fret}fr</text>')

    # Fret lines
    for i in range(NUM_FRETS + 1):
        y = gy + i * FRET_SPACING
        opacity = "0.6" if i == 0 else "0.3"
        s.append(f'<line x1="{gx}" y1="{y}" x2="{gx + grid_w}" y2="{y}" '
                 f'stroke="{t["fret_line"]}" stroke-width="1.5" opacity="{opacity}"/>')

    # Strings (thicker for lower strings)
    for i in range(NUM_STRINGS):
        x = gx + i * STR_SPACING
        width = 2.2 - i * 0.25
        s.append(f'<line x1="{x}" y1="{gy}" x2="{x}" y2="{gy + grid_h}" '
                 f'stroke="{t["string_line"]}" stroke-width="{max(width, 0.8)}" opacity="0.5"/>')

    # Dots (open, muted, fretted)
    for i, f in enumerate(frets):
        string_x = gx + i * STR_SPACING
        val = f[0] if isinstance(f, tuple) else f
        label = f[1] if isinstance(f, tuple) else None

        if val == 'x':
            # Muted X
            sz = 5
            y = gy - 14
            s.append(f'<line x1="{string_x - sz}" y1="{y - sz}" x2="{string_x + sz}" y2="{y + sz}" '
                     f'stroke="{t["fret_dot_muted"]}" stroke-width="2.5" stroke-linecap="round"/>')
            s.append(f'<line x1="{string_x + sz}" y1="{y - sz}" x2="{string_x - sz}" y2="{y + sz}" '
                     f'stroke="{t["fret_dot_muted"]}" stroke-width="2.5" stroke-linecap="round"/>')
        elif val == 0:
            # Open circle
            y = gy - 14
            s.append(f'<circle cx="{string_x}" cy="{y}" r="{DOT_R - 2}" '
                     f'fill="none" stroke="{t["fret_dot_open"]}" stroke-width="2"/>')
        else:
            # Fretted dot
            display_fret = val - start_fret + 1
            y = gy + (display_fret - 0.5) * FRET_SPACING
            # Glow
            s.append(f'<circle cx="{string_x}" cy="{y}" r="{DOT_R + 2}" '
                     f'fill="{t["accent_glow"]}" filter="url(#dotglow)"/>')
            # Dot
            s.append(f'<circle cx="{string_x}" cy="{y}" r="{DOT_R}" '
                     f'fill="{t["fret_dot"]}" />')
            # Shine
            s.append(f'<circle cx="{string_x}" cy="{y}" r="{DOT_R}" '
                     f'fill="url(#dotGrad)"/>')
            # Label
            if label:
                s.append(f'<text x="{string_x}" y="{y + 4}" text-anchor="middle" '
                         f'font-family="\'SF Mono\', monospace" font-size="10" '
                         f'fill="white" font-weight="600">{label}</text>')

    s.append('</svg>')
    return '\n'.join(s)


# ─── Page Assembly ───────────────────────────────────────────────

def generate_page(title, subtitle, piano_chords, guitar_chords, theme="midnight", day_info=""):
    t = THEMES[theme]

    html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    font-family: 'Inter', -apple-system, sans-serif;
    background: {t['bg']};
    color: {t['text']};
    min-height: 100vh;
    padding: 50px 30px;
  }}

  .container {{
    max-width: 1100px;
    margin: 0 auto;
  }}

  .header {{
    text-align: center;
    margin-bottom: 50px;
  }}

  .header h1 {{
    font-size: 32px;
    font-weight: 700;
    color: {t['title']};
    letter-spacing: -0.5px;
    margin-bottom: 8px;
  }}

  .header .subtitle {{
    font-size: 15px;
    color: {t['subtitle']};
    font-weight: 300;
    letter-spacing: 2px;
    text-transform: uppercase;
  }}

  .header .day-info {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: {t['accent']};
    margin-top: 12px;
    letter-spacing: 1px;
  }}

  .section-label {{
    font-size: 11px;
    font-weight: 600;
    color: {t['subtitle']};
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 20px;
    padding-left: 4px;
  }}

  .section {{
    margin-bottom: 50px;
  }}

  .cards {{
    display: flex;
    justify-content: center;
    gap: 24px;
    flex-wrap: wrap;
  }}

  .card {{
    background: {t['card_bg']};
    border: 1px solid {t['card_border']};
    border-radius: 16px;
    padding: 24px;
    transition: transform 0.2s, box-shadow 0.2s;
    box-shadow: 0 4px 20px rgba(0,0,0,0.2);
  }}

  .card:hover {{
    transform: translateY(-4px);
    box-shadow: 0 8px 30px rgba(0,0,0,0.3), 0 0 20px {t['accent_glow']};
  }}

  .notes-row {{
    text-align: center;
    margin-top: 12px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: {t['text_muted']};
    letter-spacing: 1px;
  }}

  .footer {{
    text-align: center;
    margin-top: 60px;
    padding-top: 30px;
    border-top: 1px solid {t['card_border']};
    font-size: 11px;
    color: {t['text_muted']};
    letter-spacing: 1px;
  }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>{title}</h1>
    <div class="subtitle">{subtitle}</div>
    {"<div class='day-info'>" + day_info + "</div>" if day_info else ""}
  </div>
"""

    # Piano section
    if piano_chords:
        html += '  <div class="section">\n'
        html += '    <div class="section-label">Piano Voicings</div>\n'
        html += '    <div class="cards">\n'
        for chord_name, notes, sub in piano_chords:
            svg = piano_svg(chord_name, notes, theme, sub)
            note_str = " · ".join(notes)
            html += f'      <div class="card">{svg}<div class="notes-row">{note_str}</div></div>\n'
        html += '    </div>\n  </div>\n'

    # Guitar section
    if guitar_chords:
        html += '  <div class="section">\n'
        html += '    <div class="section-label">Guitar Voicings</div>\n'
        html += '    <div class="cards">\n'
        for chord_name, fret_data, sub in guitar_chords:
            svg = guitar_svg(chord_name, fret_data, theme, sub)
            html += f'      <div class="card">{svg}</div>\n'
        html += '    </div>\n  </div>\n'

    html += f"""  <div class="footer">VOICING DESIGNER</div>
</div>
</body></html>"""

    return html


# ─── Demo / Test ─────────────────────────────────────────────────

def demo():
    """Generate demo pages in all three themes."""
    piano_chords = [
        ("Dm7", ["D3", "F3", "A3", "C4"], "root position"),
        ("G7", ["G2", "B3", "D4", "F4"], "shell voicing"),
        ("Cmaj7", ["C3", "E3", "G3", "B3"], "root position"),
    ]

    guitar_chords = [
        ("Dm7", ['x', (5, 'R'), (7, '5'), (5, 'b7'), (6, 'b3'), (5, 'R')], "5th string root"),
        ("G7", [(3, 'R'), (2, 'b7'), 0, 0, 0, (1, 'b7')], "open position"),
        ("Cmaj7", ['x', (3, 'R'), (2, '3'), 0, 0, 0], "open position"),
    ]

    for theme in THEMES:
        html = generate_page(
            "ii – V – I in C Major",
            "Basic Shell Voicings",
            piano_chords,
            guitar_chords,
            theme=theme,
            day_info="Day 1 · April 2, 2026"
        )
        filename = f"demo_{theme}.html"
        with open(filename, 'w') as f:
            f.write(html)
        print(f"Generated: {filename}")


if __name__ == "__main__":
    demo()
