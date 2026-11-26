# STEM video factory — Episode 01

The active renderer is `src/studio_canvas_engine.py`, a Pillow/FFmpeg illustrated
pipeline with Dr. Volt, native landscape and portrait compositions, a 30 fps
narration-RMS mouth, blinking and camera/energy motion. The narration source is
`src/episode_script.json`. The long version reads all eleven blocks in order;
the three Shorts use unchanged, complete blocks from that same script.

**Render Episode 01** runs four video jobs in parallel on GitHub Actions. Each
job synthesizes `en-US-ChristopherNeural`, uses faster-whisper `base.en` for
word timings, aligns the exact source words to those timings, burns white/gold
ASS captions, and writes SRT/ASS alongside the MP4. A final job checks streams
and exact SRT text and creates contact sheets and a motion/composition report.
Download the `ep01-phone-charger-videos` artifact from the run; check the job
and audit status before treating the output as finished. The artifact is kept
for 30 days. Edge TTS and Hugging Face must be reachable from the runner; Edge
TTS is unofficial and can change or fail.

The timing alignment uses Whisper matches; words Whisper misses are interpolated
between neighboring matches. Review captions and timing before publication.
The visual audit is a heuristic, not a guarantee of quality or narrative
accuracy. It tests 2-second windows (excluding the lower 20%) for **greater
than 3%** changed pixels and compares contact-sheet spatial luminance layouts.

The exact requested narration includes claims about explosion, charger
operation, and zero wasted energy that are not technically reliable. They are
preserved as requested; revise and fact-check before publication.

## Development

The workflow is the authoritative full-suite build. It requires FFmpeg with
libass and libx264, DejaVu fonts, Python 3.11 and the packages in
`requirements.txt`; it does not use Manim or LaTeX. Run the active tests with:

```sh
python -m unittest tests.test_canvas_engine tests.test_subtitle_engine tests.test_studio -v
python src/studio_canvas_engine.py --video full_youtube_video_16x9 --workers 2
```

Older Manim-era sources and their tests remain in the repository as historical
code but are not part of the active renderer or workflow. Outputs and temporary
assets are ignored by Git. Full-resolution video encoding and transcription
are computationally expensive; a five-minute end-to-end build is a target, not
a guarantee. See `STATE.md` for run status.
