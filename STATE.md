# Fast 3D pilot state

[Run 45801513380](https://github.com/amos992005/stem-video-factory/actions/runs/45801513380)
succeeded in **3m49s** and uploaded the `ep01-fast-pilot` artifact (expires
2026-12-26). It contains the 35.33-second portrait MP4, 4×4 contact sheet,
active-word ASS, build log and render metadata. The MP4 was verified as
1080×1920, 30 fps, 1,060 frames, with audio. All 13 local/runner tests passed;
the ASS has 108 narration word events and no overlapping event timings.

Pollinations failed with HTTP 402/503 and the job used the Three.js/WebGL
fallback with SwiftShader. Its 3D frames were rendered at 360×640 and upscaled;
they are not Flux-generated or verified Pixar-quality artwork. The seven exact
narration blocks were synthesized by Andrew Multilingual and required an
additional 1.08× tempo adjustment to fit the revised 26–36-second target.
The contact sheet shows some captions overlapping the foreground character;
timing and intelligibility need a full listening/visual review.

The workflow captures `output/pilot/build.log` and attempts to commit the log,
ASS, metadata and contact sheet to the current branch even on failure. The
user-supplied statement that a battery will explode in seconds is not guaranteed
and should be fact-checked before publication.
