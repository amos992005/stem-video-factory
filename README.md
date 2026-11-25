# STEM video factory

A Manim Community Edition pipeline for STEM animations and narrated video.
Episode 01 covers the ideas behind a phone charger, with five chapters and
three standalone portrait Shorts. The circuit models are educational
simplifications, not instructions for building or modifying a mains device.

## Render and download

The **Render Episode 01** GitHub Actions workflow automatically starts on a
relevant push, or can be started via **Actions → Render Episode 01 → Run
workflow** on the branch with these files. It renders eight scenes in parallel
at 1080p, concatenates the chapters, transcribes with faster-whisper `base.en`,
burns the Shorts' captions, and verifies dimensions and audio streams. Download
**ep01-phone-charger-videos** from the successful run's Artifacts section.
The ZIP contains four MP4s and four SRT subtitle files under
`output/ep01_phone_charger/`, plus this README. Automated captions should be
reviewed before publishing.
Artifacts expire after 30 days; Actions availability and quotas depend on plan.

The render needs outbound access to Microsoft's Edge TTS and Hugging Face's
Whisper model downloads. Edge TTS is an unofficial free service that can change
or become unavailable. Generated assets and videos are excluded from Git.
See `STATE.md` for current pipeline details.

## Local setup (Debian/Ubuntu)

```sh
sudo apt-get update
sudo apt-get install -y ffmpeg libcairo2-dev libpango1.0-dev pkg-config python3-dev \
  texlive-latex-base texlive-latex-extra texlive-fonts-recommended texlive-science dvisvgm fonts-dejavu-core
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python src/generate_ep01_svgs.py
manim -qh src/ep01_long_video.py Ch1_TheHookAndACvsDC
```

The workflow is the authoritative full-suite build recipe: it collects the
five landscape and three portrait scene MP4s in `staging/`, then runs
`python src/package_ep01.py`. Packaging requires FFmpeg with libass/libx264,
and internet access for the initial Whisper model download. The voiceover
service times animations to clip durations; bookmark timing is not implemented.

## Studio visuals and motion audit

The studio version uses `src/vfx_engine.py` and `src/studio_components.py` for
procedural neon, flowing current indicators, sparks and 3D-projected coils.
`src/audio_design.py` synthesizes the underscore and effects; the packaging
job mixes the underscore at -20 dB gain beneath the narration. The final
artifact includes contact sheets and `motion_audit_report.md`. The audit samples
5 fps, thresholds adjacent grayscale frames and checks every overlapping
2-second window; the report describes its metric and limitations. A passing
motion metric is not a substitute for editorial review of images or captions.
