# Fast 3D pilot state

The manual workflow requests seven Flux scene illustrations and four cutouts,
then falls back to the Three.js/WebGL studio when Pollinations is unavailable.
The seven exact narration blocks use an adaptive 26–36-second timeline and
active-word ASS subtitles. Build output and diagnostics are uploaded on failure
or success; the workflow attempts to commit the build log, ASS, metadata and
contact sheet to the current branch without overwriting concurrent changes.

## Latest completed render

[Run 45798419265](https://github.com/amos992005/stem-video-factory/actions/runs/45798419265)
succeeded in 3m46s and uploaded `ep01-fast-pilot`. It rendered the WebGL
fallback after Pollinations returned HTTP 402. The video is 35.33s, 1080×1920,
30fps; 3D frames were rendered at 360×640 then upscaled. However, inspection of
the contact sheet showed overlapping and lingering captions: a beat offset was
added repeatedly to successive word timestamps. That render is not approved.
The offset bug and caption event bounds have been corrected locally with
regression tests. A final render is needed to verify the correction.

The visuals are procedural 3D, not Flux-generated artwork or verified Pixar
quality. Voice and captions still need a listening review. The supplied claim
that the battery will explode in seconds is not guaranteed and should be
fact-checked before publication.
