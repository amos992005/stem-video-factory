# Project state

## Episode 01 — studio VFX cut

- Final artifact: **ep01-phone-charger-videos** in the [successful render run](https://github.com/amos992005/stem-video-factory/actions/runs/45691178756). The ZIP preserves `output/ep01_phone_charger/` and includes the four MP4s, four SRTs, two contact sheets and the motion report. Artifacts expire after 30 days.
- Verified H.264/AAC videos: landscape 1920×1080, 211.22 seconds; three portrait 1080×1920 Shorts, 39.37, 36.32 and 35.78 seconds. The Shorts have burned-in captions.
- Motion audit passed with **zero flagged windows**: minima are 1.11%, 1.38%, 6.30% and 1.99%, respectively. The audit samples at 5 fps, downsizes to 320×180 grayscale, thresholds adjacent-frame differences at 6/255 and checks the union of changed pixels in overlapping 2-second windows. It is a motion proxy, not proof of creative quality or that every original frame changes.
- `src/vfx_engine.py` and `src/studio_components.py` implement neon layers, updater-driven paths, sparks and projected 3D coils. `src/audio_design.py` synthesizes audio; `src/package_ep01.py` mixes the pad at -20 dB gain and burns captions. `src/visual_audit.py` creates contact sheets and enforces the motion threshold.
- The animated circuit models are simplified teaching diagrams. Narration distinguishes modern switching chargers from the idealized transformer/bridge model, notes the difference between USB output and battery voltage, and warns against connecting a battery to mains. Current-path dots represent conventional current. Review automatic captions and the finished video before publication.
- The sandbox cannot reach Debian mirrors, Edge TTS, or GitHub's artifact blob storage; rendering and downloading the artifact use GitHub Actions. Edge TTS and Whisper model hosting are external dependencies.
