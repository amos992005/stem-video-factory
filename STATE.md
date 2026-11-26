# Episode 01 state

The active build is the illustrated Pillow/FFmpeg canvas pivot, not the older
Manim pipeline. Source narration is `src/episode_script.json`; the full video
uses all eleven blocks verbatim, and each Short uses unchanged complete blocks.

## Verified cloud run

- [Run 45770128693](https://github.com/amos992005/stem-video-factory/actions/runs/45770128693)
  succeeded on commit `13d112c`. The `ep01-phone-charger-videos` artifact
  expires 2026-12-26. All four videos have 30 fps video and audio, and all
  four SRTs were checked against their exact selected narration.
- End-to-end elapsed time was **5 minutes 39 seconds**, including setup,
  rendering, captioning, verification and upload. This misses the under-five-
  minute target; it is not a guarantee for future runs.
- Full landscape: 1920×1080, 185.42 s. Portrait Shorts: 1080×1920,
  50.53 s, 33.62 s and 65.43 s respectively.
- Minimum measured motion above the subtitle zone: 8.46%, 10.62%, 13.50%,
  and 11.89%; no two-second windows were at or below the strict 3% threshold.
- Contact-sheet composition minima: 0.324, 0.320, 0.336, and 0.347. All
  exceed 0.22 under the current foreground-layout heuristic. The earlier
  run 45767965753 failed the original raw-luminance composition test; after
  reframing shots, the current test subtracts the median background and
  compares samples at least nine seconds apart. The two metrics are not
  directly comparable. Neither is proof of visual or narrative quality.

## Remaining limitations

The illustrations are relatively simple, flat procedural cartoons, not the
lush, fully realized 2.5D character animation originally requested. The host
has RMS-driven mouth shapes, pose changes, blinking and bobbing; the turnstile,
waterline and energy packets move, but several analogies and the confetti are
still predominantly static. The audio bed is a synthesized ambient pad rather
than a fully designed scene-by-scene effects mix. The build therefore should
be reviewed and refined rather than treated as a fully polished final episode.
Whisper-missed words receive interpolated timings, so captions need a listening
review. The user-supplied narration also includes claims about explosion,
charger operation, and zero wasted energy that need fact-checking.
