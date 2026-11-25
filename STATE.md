# Project state

## Episode 01 — phone charger

- Source: `src/ep01_long_video.py` (five chapters), `src/ep01_shorts.py`
  (three portrait videos), shared visuals, SymPy models and Schemdraw assets.
- Render: **Render Episode 01** in `.github/workflows/render.yml`. Eight
  parallel 1080p Manim jobs feed a packaging job; the latter uses FFmpeg and
  faster-whisper `base.en` for captions and validates the four output streams.
- Final artifact: `ep01-phone-charger-videos`. It contains four MP4 files and
  four corresponding SRT files under `output/ep01_phone_charger/`. Captions
  are burned into the three Shorts; review transcription before publishing.
- The final rendered cut was validated at 1920x1080 (3:54.32) and three
  1080x1920 Shorts (42.50, 39.77 and 42.02 seconds); all have AAC audio.
  A representative set of frames was also visually spot-checked.
  GitHub artifacts expire after 30 days.
- The circuit models are intentionally idealized: the narration distinguishes
  them from real switch-mode chargers, notes USB output versus battery voltage,
  and warns against connecting batteries to mains. Current-path dots represent
  conventional current, not electrons.
- The sandbox cannot reach Debian mirrors, Edge TTS, or GitHub's artifact blob
  storage; rendering and downloading the final artifact are done via GitHub.
  Edge TTS and Hugging Face model availability are external dependencies.
