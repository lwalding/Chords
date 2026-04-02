#!/usr/bin/env python3
"""
Daily Voicing Generator — pulls from engine, renders via designer, outputs full HTML.
Includes Tone.js audio playback and rating UI.
"""

import json
import os
import sys
from datetime import date, timedelta
from engine import (
    generate_day, NOTE_TO_SEMI, NOTES,
    CHORD_QUALITIES, get_voicings_for_chord, get_guitar_voicings,
)
from voicing_designer import piano_svg, guitar_svg, THEMES


def note_to_midi_number(note_str):
    """Convert 'C4' to MIDI number for Tone.js."""
    name = note_str[0].upper()
    rest = note_str[1:]
    acc = 0
    i = 0
    while i < len(rest) and rest[i] in '#b':
        acc += 1 if rest[i] == '#' else -1
        i += 1
    octave = int(rest[i:])
    return (octave + 1) * 12 + NOTE_TO_SEMI.get(name, 0) + acc


def note_to_tone_name(note_str):
    """Convert our note format to Tone.js format (e.g., 'Bb3' stays 'Bb3')."""
    return note_str


def generate_day_html(target_date=None, theme="midnight"):
    """Generate the full HTML page for a day."""
    if target_date is None:
        target_date = date.today()

    day_data = generate_day(target_date)
    t = THEMES[theme]

    # Collect all voicing data for Tone.js
    audio_data = []  # [{id, notes, type}, ...]
    card_id = 0

    # Build piano card HTML
    piano_sections_html = ""
    for pc in day_data['piano_chords']:
        chord = pc['chord']
        voicings = pc['voicings']
        if not voicings:
            continue

        cards_html = ""
        for v in voicings:
            cid = f"p{card_id}"
            notes = v['piano_notes']
            tone_notes = [note_to_tone_name(n) for n in notes]
            audio_data.append({'id': cid, 'notes': tone_notes, 'type': 'piano'})

            svg = piano_svg(chord['symbol'], notes, theme, v['name'])
            note_str = " · ".join(notes)

            cards_html += f'''      <div class="card" id="card-{cid}">
        {svg}
        <div class="notes-row">{note_str}</div>
        <div class="voicing-desc">{v['description']}</div>
        <div class="audio-controls">
          <button class="play-btn" onclick="playChord('{cid}')" title="Play chord">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><polygon points="5,3 19,12 5,21"/></svg>
          </button>
          <button class="arp-btn" onclick="arpeggiateChord('{cid}')" title="Arpeggiate">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M3,4h4v4H3V4 M9,8h4v4H9V8 M15,12h4v4h-4V12 M3,16h4v4H3V16"/></svg>
          </button>
        </div>
        <div class="rating-row" data-card="{cid}">
          <button class="tag-btn" onclick="rate('{cid}','love')">love</button>
          <button class="tag-btn" onclick="rate('{cid}','fine')">fine</button>
          <button class="tag-btn" onclick="rate('{cid}','awkward')">awkward</button>
          <button class="tag-btn" onclick="rate('{cid}','muddy')">muddy</button>
          <button class="tag-btn" onclick="rate('{cid}','too basic')">too basic</button>
          <button class="tag-btn" onclick="rate('{cid}','too complex')">too complex</button>
        </div>
      </div>
'''
            card_id += 1

        piano_sections_html += f'''    <div class="chord-group">
      <div class="chord-group-label">{chord['symbol']} <span class="degree">({chord['degree']})</span></div>
      <div class="cards">
{cards_html}      </div>
    </div>
'''

    # Build guitar card HTML
    guitar_sections_html = ""
    for gc in day_data['guitar_chords']:
        chord = gc['chord']
        voicings = gc['voicings']
        if not voicings:
            continue

        cards_html = ""
        for v in voicings:
            cid = f"g{card_id}"
            # For guitar, compute MIDI notes from frets for audio
            guitar_tuning = [40, 45, 50, 55, 59, 64]
            guitar_midi_notes = []
            for i, f in enumerate(v['frets']):
                val = f[0] if isinstance(f, tuple) else f
                if isinstance(val, int) and val >= 0:
                    midi = guitar_tuning[i] + val
                    octave = (midi // 12) - 1
                    note_name = NOTES[midi % 12]
                    guitar_midi_notes.append(f"{note_name}{octave}")

            audio_data.append({'id': cid, 'notes': guitar_midi_notes, 'type': 'guitar'})

            svg = guitar_svg(chord['symbol'], v['frets'], theme, v['name'])

            cards_html += f'''      <div class="card" id="card-{cid}">
        {svg}
        <div class="voicing-desc">{v['description']}</div>
        <div class="audio-controls">
          <button class="play-btn" onclick="playChord('{cid}')" title="Play chord">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><polygon points="5,3 19,12 5,21"/></svg>
          </button>
          <button class="arp-btn" onclick="arpeggiateChord('{cid}')" title="Arpeggiate">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M3,4h4v4H3V4 M9,8h4v4H9V8 M15,12h4v4h-4V12 M3,16h4v4H3V16"/></svg>
          </button>
        </div>
        <div class="rating-row" data-card="{cid}">
          <button class="tag-btn" onclick="rate('{cid}','love')">love</button>
          <button class="tag-btn" onclick="rate('{cid}','fine')">fine</button>
          <button class="tag-btn" onclick="rate('{cid}','awkward')">awkward</button>
          <button class="tag-btn" onclick="rate('{cid}','muddy')">muddy</button>
          <button class="tag-btn" onclick="rate('{cid}','too basic')">too basic</button>
          <button class="tag-btn" onclick="rate('{cid}','too complex')">too complex</button>
        </div>
      </div>
'''
            card_id += 1

        guitar_sections_html += f'''    <div class="chord-group">
      <div class="chord-group-label">{chord['symbol']} <span class="degree">({chord['degree']})</span></div>
      <div class="cards">
{cards_html}      </div>
    </div>
'''

    # Audio data as JSON
    audio_json = json.dumps(audio_data)

    date_str = target_date.strftime("%B %-d, %Y")
    day_info = f"Day {day_data['day_number']} · Week {day_data['week_number']} · {date_str}"

    html = f'''<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Day {day_data['day_number']} — {day_data['progression']['name']} in {day_data['key']}</title>
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

  .container {{ max-width: 1200px; margin: 0 auto; }}

  .header {{
    text-align: center;
    margin-bottom: 50px;
  }}
  .header h1 {{
    font-size: 32px; font-weight: 700; color: {t['title']};
    letter-spacing: -0.5px; margin-bottom: 8px;
  }}
  .header .subtitle {{
    font-size: 15px; color: {t['subtitle']};
    font-weight: 300; letter-spacing: 2px; text-transform: uppercase;
  }}
  .header .day-info {{
    font-family: 'JetBrains Mono', monospace; font-size: 12px;
    color: {t['accent']}; margin-top: 12px; letter-spacing: 1px;
  }}
  .header .stage-badge {{
    display: inline-block; margin-top: 14px; padding: 6px 16px;
    background: {t['card_bg']}; border: 1px solid {t['card_border']};
    border-radius: 20px; font-size: 11px; color: {t['accent']};
    letter-spacing: 2px; text-transform: uppercase; font-weight: 600;
  }}
  .header .prog-desc {{
    font-size: 13px; color: {t['text_muted']}; margin-top: 10px;
    font-style: italic;
  }}

  .section {{
    margin-bottom: 50px;
  }}
  .section-label {{
    font-size: 11px; font-weight: 600; color: {t['subtitle']};
    letter-spacing: 3px; text-transform: uppercase;
    margin-bottom: 24px; padding-left: 4px;
  }}

  .chord-group {{
    margin-bottom: 30px;
  }}
  .chord-group-label {{
    font-size: 16px; font-weight: 600; color: {t['title']};
    margin-bottom: 14px; padding-left: 4px;
  }}
  .chord-group-label .degree {{
    font-weight: 300; color: {t['subtitle']}; font-size: 13px;
  }}

  .cards {{
    display: flex; gap: 20px; flex-wrap: wrap;
  }}
  .card {{
    background: {t['card_bg']}; border: 1px solid {t['card_border']};
    border-radius: 16px; padding: 20px;
    transition: transform 0.2s, box-shadow 0.2s;
    box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    display: flex; flex-direction: column; align-items: center;
  }}
  .card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 8px 30px rgba(0,0,0,0.3), 0 0 15px {t['accent_glow']};
  }}

  .notes-row {{
    text-align: center; margin-top: 10px;
    font-family: 'JetBrains Mono', monospace; font-size: 11px;
    color: {t['text_muted']}; letter-spacing: 1px;
  }}
  .voicing-desc {{
    text-align: center; margin-top: 6px; font-size: 11px;
    color: {t['text_muted']}; max-width: 220px;
  }}

  /* Audio controls */
  .audio-controls {{
    display: flex; gap: 8px; margin-top: 12px; justify-content: center;
  }}
  .play-btn, .arp-btn {{
    width: 36px; height: 36px; border-radius: 50%;
    border: 1px solid {t['card_border']}; background: {t['bg']};
    color: {t['accent']}; cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    transition: all 0.2s;
  }}
  .play-btn:hover, .arp-btn:hover {{
    background: {t['accent']}; color: {t['bg']};
    box-shadow: 0 0 12px {t['accent_glow']};
  }}
  .play-btn:active, .arp-btn:active {{
    transform: scale(0.9);
  }}

  /* Rating tags */
  .rating-row {{
    display: flex; gap: 6px; margin-top: 12px; flex-wrap: wrap;
    justify-content: center;
  }}
  .tag-btn {{
    padding: 3px 10px; border-radius: 12px; border: 1px solid {t['card_border']};
    background: transparent; color: {t['text_muted']};
    font-size: 10px; cursor: pointer; transition: all 0.2s;
    font-family: 'Inter', sans-serif; letter-spacing: 0.5px;
  }}
  .tag-btn:hover {{
    border-color: {t['accent']}; color: {t['accent']};
  }}
  .tag-btn.active {{
    background: {t['accent']}; color: {t['bg']};
    border-color: {t['accent']}; font-weight: 600;
  }}

  /* Overall rating */
  .day-rating {{
    text-align: center; margin-top: 40px; padding: 30px;
    background: {t['card_bg']}; border: 1px solid {t['card_border']};
    border-radius: 16px;
  }}
  .day-rating-label {{
    font-size: 13px; color: {t['subtitle']}; margin-bottom: 12px;
    letter-spacing: 1px; text-transform: uppercase; font-weight: 500;
  }}
  .stars {{
    display: flex; gap: 8px; justify-content: center;
  }}
  .star-btn {{
    width: 40px; height: 40px; border-radius: 8px;
    border: 1px solid {t['card_border']}; background: transparent;
    color: {t['text_muted']}; font-size: 20px; cursor: pointer;
    transition: all 0.2s;
  }}
  .star-btn:hover, .star-btn.active {{
    color: {t['accent']}; border-color: {t['accent']};
    box-shadow: 0 0 10px {t['accent_glow']};
  }}
  .notes-field {{
    margin-top: 16px;
  }}
  .notes-field textarea {{
    width: 100%; max-width: 500px; height: 60px; padding: 10px;
    background: {t['bg']}; border: 1px solid {t['card_border']};
    border-radius: 8px; color: {t['text']}; font-family: 'Inter', sans-serif;
    font-size: 13px; resize: vertical;
  }}
  .notes-field textarea::placeholder {{ color: {t['text_muted']}; }}
  .save-btn {{
    margin-top: 12px; padding: 8px 24px; border-radius: 8px;
    border: 1px solid {t['accent']}; background: transparent;
    color: {t['accent']}; cursor: pointer; font-family: 'Inter', sans-serif;
    font-size: 12px; letter-spacing: 1px; text-transform: uppercase;
    transition: all 0.2s;
  }}
  .save-btn:hover {{
    background: {t['accent']}; color: {t['bg']};
  }}
  .save-status {{
    margin-top: 8px; font-size: 11px; color: {t['accent']};
    opacity: 0; transition: opacity 0.3s;
  }}
  .save-status.show {{ opacity: 1; }}

  .nav-link {{
    display: inline-block; margin-top: 20px; color: {t['accent']};
    text-decoration: none; font-size: 13px; letter-spacing: 1px;
  }}
  .nav-link:hover {{ text-decoration: underline; }}

  .footer {{
    text-align: center; margin-top: 60px; padding-top: 30px;
    border-top: 1px solid {t['card_border']};
    font-size: 11px; color: {t['text_muted']}; letter-spacing: 1px;
  }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>{day_data['progression']['name']} in {day_data['key']}</h1>
    <div class="subtitle">{day_data['stage_description']}</div>
    <div class="day-info">{day_info}</div>
    <div class="stage-badge">Levels: {' · '.join(day_data['levels'])}</div>
    <div class="prog-desc">{day_data['progression']['description']}</div>
  </div>

  <div class="section">
    <div class="section-label">Piano Voicings</div>
{piano_sections_html}
  </div>

  <div class="section">
    <div class="section-label">Guitar Voicings</div>
{guitar_sections_html}
  </div>

  <div class="day-rating">
    <div class="day-rating-label">How was today's session?</div>
    <div class="stars">
      <button class="star-btn" onclick="starRate(1)">1</button>
      <button class="star-btn" onclick="starRate(2)">2</button>
      <button class="star-btn" onclick="starRate(3)">3</button>
      <button class="star-btn" onclick="starRate(4)">4</button>
      <button class="star-btn" onclick="starRate(5)">5</button>
    </div>
    <div class="notes-field">
      <textarea id="day-notes" placeholder="Any notes about today's voicings..."></textarea>
    </div>
    <button class="save-btn" onclick="saveRatings()">Save Ratings</button>
    <div class="save-status" id="save-status">Saved to localStorage</div>
  </div>

  <div style="text-align:center; margin-top: 30px;">
    <a class="nav-link" href="index.html">← Back to catalog</a>
  </div>

  <div class="footer">VOICING TRAINER</div>
</div>

<!-- Tone.js -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/tone/14.8.49/Tone.js"></script>
<script>
const AUDIO_DATA = {audio_json};

// Synths
let pianoSynth = null;
let guitarSynth = null;

function initAudio() {{
  if (pianoSynth) return;
  pianoSynth = new Tone.PolySynth(Tone.Synth, {{
    oscillator: {{ type: "triangle8" }},
    envelope: {{ attack: 0.02, decay: 0.8, sustain: 0.3, release: 1.5 }},
    volume: -8,
  }}).toDestination();

  guitarSynth = new Tone.PolySynth(Tone.Synth, {{
    oscillator: {{ type: "sawtooth8" }},
    envelope: {{ attack: 0.005, decay: 0.5, sustain: 0.15, release: 0.8 }},
    volume: -12,
  }}).toDestination();
}}

function getSynth(type) {{
  return type === 'guitar' ? guitarSynth : pianoSynth;
}}

async function playChord(id) {{
  await Tone.start();
  initAudio();
  const data = AUDIO_DATA.find(d => d.id === id);
  if (!data || !data.notes.length) return;
  const synth = getSynth(data.type);
  synth.releaseAll();
  synth.triggerAttackRelease(data.notes, "2n");

  // Visual feedback
  const card = document.getElementById('card-' + id);
  card.style.boxShadow = '0 0 30px {t["accent_glow"]}';
  setTimeout(() => card.style.boxShadow = '', 600);
}}

async function arpeggiateChord(id) {{
  await Tone.start();
  initAudio();
  const data = AUDIO_DATA.find(d => d.id === id);
  if (!data || !data.notes.length) return;
  const synth = getSynth(data.type);
  synth.releaseAll();

  const now = Tone.now();
  const spacing = data.type === 'guitar' ? 0.06 : 0.12;
  data.notes.forEach((note, i) => {{
    synth.triggerAttackRelease(note, "2n", now + i * spacing);
  }});

  const card = document.getElementById('card-' + id);
  card.style.boxShadow = '0 0 30px {t["accent_glow"]}';
  setTimeout(() => card.style.boxShadow = '', 600 + data.notes.length * spacing * 1000);
}}

// ─── Ratings ────────────────────────────────────────────────────

const DAY_KEY = '{day_data["date"]}';

function loadRatings() {{
  const raw = localStorage.getItem('voicing-ratings-' + DAY_KEY);
  return raw ? JSON.parse(raw) : {{ tags: {{}}, stars: 0, notes: '' }};
}}

function saveToStorage(ratings) {{
  localStorage.setItem('voicing-ratings-' + DAY_KEY, JSON.stringify(ratings));
}}

function rate(cardId, tag) {{
  const ratings = loadRatings();
  if (!ratings.tags[cardId]) ratings.tags[cardId] = [];
  const idx = ratings.tags[cardId].indexOf(tag);
  if (idx >= 0) {{
    ratings.tags[cardId].splice(idx, 1);
  }} else {{
    ratings.tags[cardId] = [tag]; // one tag per card
  }}
  saveToStorage(ratings);
  renderTags();
}}

function starRate(n) {{
  const ratings = loadRatings();
  ratings.stars = n;
  saveToStorage(ratings);
  renderStars();
}}

function saveRatings() {{
  const ratings = loadRatings();
  ratings.notes = document.getElementById('day-notes').value;
  saveToStorage(ratings);
  const el = document.getElementById('save-status');
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), 2000);
}}

function renderTags() {{
  const ratings = loadRatings();
  document.querySelectorAll('.tag-btn').forEach(btn => {{
    const row = btn.closest('.rating-row');
    const cardId = row.dataset.card;
    const tag = btn.textContent;
    const tags = ratings.tags[cardId] || [];
    btn.classList.toggle('active', tags.includes(tag));
  }});
}}

function renderStars() {{
  const ratings = loadRatings();
  document.querySelectorAll('.star-btn').forEach((btn, i) => {{
    btn.classList.toggle('active', i < ratings.stars);
  }});
}}

function initRatings() {{
  const ratings = loadRatings();
  renderTags();
  renderStars();
  if (ratings.notes) document.getElementById('day-notes').value = ratings.notes;
}}

document.addEventListener('DOMContentLoaded', initRatings);
</script>
</body></html>'''

    return html, day_data


def generate_and_save(target_date=None, theme="midnight"):
    """Generate day HTML and update manifest."""
    if target_date is None:
        target_date = date.today()

    html, day_data = generate_day_html(target_date, theme)

    # Save day file
    filename = f"{target_date}.html"
    filepath = os.path.join("days", filename)
    os.makedirs("days", exist_ok=True)
    with open(filepath, 'w') as f:
        f.write(html)

    # Update manifest
    manifest_path = "manifest.json"
    if os.path.exists(manifest_path):
        with open(manifest_path) as f:
            manifest = json.load(f)
    else:
        manifest = {"days": []}

    # Remove existing entry for this date if any
    manifest["days"] = [d for d in manifest["days"] if d["date"] != str(target_date)]

    # Add new entry
    chord_symbols = [c['symbol'] for c in day_data['progression']['chords']]
    manifest["days"].append({
        "date": str(target_date),
        "day_number": day_data["day_number"],
        "week_number": day_data["week_number"],
        "key": day_data["key"],
        "progression": day_data["progression"]["name"],
        "stage": day_data["stage_description"],
        "levels": day_data["levels"],
        "chords": chord_symbols,
        "file": filepath,
    })

    # Sort by date
    manifest["days"].sort(key=lambda d: d["date"])

    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"Generated: {filepath}")
    print(f"  Key: {day_data['key']} | {day_data['progression']['name']}")
    print(f"  Stage: {day_data['stage_description']}")
    print(f"  Chords: {', '.join(chord_symbols)}")
    return filepath


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Generate for specific date
        target = date.fromisoformat(sys.argv[1])
    else:
        target = date.today()

    generate_and_save(target)
