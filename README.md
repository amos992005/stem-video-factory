# Episode 01 — fast vertical pilot

The active GitHub Actions workflow renders **one** 28-second, 1080×1920, 30 fps
pilot and a 4×4 contact sheet. Run it manually with **Actions → Render
28-second fast pilot → Run workflow**. It uploads only
`output/pilot/short_01_pilot_9x16.mp4` and `output/pilot/pilot_contact_sheet.png`
as the `ep01-fast-pilot` artifact.

`src/ai_asset_generator.py` requests the seven specified scene backdrops and
four Dr. Volt poses from Pollinations' legacy image endpoint with `model=flux`,
retries and caches successful images, and extracts the chroma-keyed character
cutouts. The legacy endpoint is deprecated and can fail, rate-limit requests,
return watermarked images or omit the actual model identity. This pipeline
fails rather than substituting geometric artwork if an image is unavailable.
Its cache is ignored by Git and optionally restored by Actions.

`src/pilot_audio.py` synthesizes the exact seven supplied lines with Edge TTS
Andrew Multilingual at +12% and +2 Hz, trims silence, and time-compresses each
clip if needed to fit its four-second beat. Additional acceleration can affect
intelligibility. Edge's word-boundary events are mapped back to the exact
source text for white/gold ASS captions; no Whisper model is downloaded.
Synthesized effects align with beat starts. `src/pilot_compositor.py` layers
camera motion, independently animated cutouts, particle VFX and flash
transitions over the service artwork. Pillow is used for image processing and
compositing, not to draw the backgrounds or the character.

The workflow has no push trigger, so committing changes does not cause extra
runs. Pip, AI-image outputs and the model-cache directory are cached. Network
service latency and availability make the requested two-to-four-minute build a
target, not a guarantee; the job is limited to five minutes. The narration's
claim that the battery will explode in seconds is not guaranteed and should be
fact-checked before publication. See `STATE.md` for verified run status.

Active tests: `python -m unittest tests.test_fast_pilot tests.test_subtitle_engine -v`.
Older episode scripts remain in the repository as historical code and are not
part of this workflow.
