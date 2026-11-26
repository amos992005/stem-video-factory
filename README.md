# Fast 3D pilot

The manual-only GitHub Actions workflow renders one vertical 1080×1920,
30 fps pilot and a 4×4 contact sheet. The target duration is 26–36 seconds:
seven exact narration blocks are synthesized with Andrew Multilingual at +12%
and +2 Hz, silence is trimmed, and an additional global speedup is applied only
when needed to fit. Edge word boundaries are aligned to the exact source words
for burned-in white/gold ASS captions. Procedural audio supplies the beat SFX.

The renderer first requests seven listed scene illustrations and four Dr. Volt
cutouts from Pollinations' legacy Flux endpoint. If the service fails or times
out, it falls back to an original Three.js/WebGL animated 3D studio, using
Chromium's software renderer, physical materials, lighting, moving particles,
a scientist hover-bot and bloom. WebGL frames are rendered at 360×640 and
upsampled for the 1080×1920 deliverable; this is not native 1080p 3D rendering.
Neither the generated character's identity nor the aesthetic quality is
independently guaranteed. Real video, captions and illustrations need review.

`ep01-fast-pilot` includes the video, contact sheet, metadata and `build.log`
when available. The job attempts to commit the log and contact sheet back to
the same branch even on failure, but leaves the video in the artifact rather
than Git. It refuses to overwrite a branch that advanced during the job.
`STATE.md` records the most recently verified run. AI image cache, local node
modules and generated video are ignored by Git.

The two-to-four-minute workflow time is a target, not guaranteed; the job gives
the software renderer up to six minutes before collecting diagnostics. The
exact user-provided statement that a battery will explode in seconds is not
guaranteed and should be fact-checked before publication.
