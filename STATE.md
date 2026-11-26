# Fast 3D pilot state

The revised manually triggered workflow tries Pollinations briefly, falling
back to the Three.js/WebGL 3D studio if the service fails or times out. The
exact seven-block narration now uses an adaptive 26–36 second timeline rather
than a fixed 28-second assertion. The workflow captures `output/pilot/build.log`,
uploads diagnostics even on failure, and attempts to commit the log and
contact sheet on the current branch without overwriting concurrent changes.

The revised pipeline has not yet completed a cloud run. The earlier pilot run
[45795458025](https://github.com/amos992005/stem-video-factory/actions/runs/45795458025)
failed before upload; its detailed logs were inaccessible from the sandbox.
This version's local unit tests passed; Chromium was unavailable locally, so
the WebGL fallback requires runner validation. Quality, duration, runtime and
artifact status must not be inferred from the earlier run.
