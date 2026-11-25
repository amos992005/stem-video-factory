# STEM video factory

A minimal Manim Community Edition pipeline: Schemdraw creates an RC circuit,
SymPy creates the capacitor energy equation, and Edge TTS narrates the scene.
Edge TTS needs internet access to Microsoft's speech service; it is an unofficial
service and availability or behavior may change. No API key is required.

## GitHub Actions (recommended in the restricted sandbox)

The **Render test video** workflow runs automatically after a push that changes
the pipeline, and can also be started manually with **Actions → Render test
video → Run workflow**, selecting the branch containing these files. When it
succeeds, open the run's **Artifacts** section and download **test-video**; the
ZIP contains `test_video.mp4`. Artifacts expire after 30 days. GitHub Actions
availability and free-minute limits depend on the repository's plan. The
workflow doesn't publish generated videos to the repository or a release.

## On a Debian/Ubuntu machine

```sh
sudo apt-get update
sudo apt-get install -y ffmpeg libcairo2-dev libpango1.0-dev pkg-config python3-dev \
  texlive-latex-base texlive-latex-extra texlive-fonts-recommended texlive-science dvisvgm
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
manim -ql src/test_pipeline.py TestScene
mkdir -p output
cp media/videos/test_pipeline/480p15/TestScene.mp4 output/test_video.mp4
```

Run from the repository root. Manim generates the SVG in `assets/svg/`, caches
narration in `media/voiceovers/`, and writes the render to `media/videos/`.
Generated media and the local virtual environment are ignored by Git. The
custom service uses audio duration for scene timing; bookmark-based word timing
is not implemented. Faster Whisper is installed for future transcription use,
but is not needed for this scene and downloads its models separately when used.
