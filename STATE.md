# Fast 3D pilot state

The manual workflow requests the seven listed Pollinations illustrations and
four character cutouts, and falls back to an animated Three.js/WebGL 3D studio
when Pollinations is unavailable. It synthesizes the exact seven-line script,
uses an adaptive 26–36-second timeline, and burns word-highlighted ASS captions.
The workflow captures `output/pilot/build.log`, uploads the output directory even
on failure, and attempts to commit diagnostics on the current branch without
overwriting concurrent changes.

## Most recent run

[Run 45799603860](https://github.com/amos992005/stem-video-factory/actions/runs/45799603860)
failed validation after 3m48s, reporting "Wrong video dimensions or frame
rate". Pollinations returned HTTP 402, so Three.js/SwiftShader was used. The
`ep01-fast-pilot` artifact contains a **draft MP4**, ASS captions and build log,
but no contact sheet: the old pipeline validated before generating the sheet.
The draft's stream properties were not logged, so its precise failure is not
confirmed. The ASS file contains all 108 word events with no overlapping
narration events, fixing the overlapping-caption bug seen in the prior run.
Neither that validation nor artistic quality is verified from the draft video.

The code has since been changed to use integer frame timestamps and an explicit
CFR 30 fps final encode, print observed stream metadata, and generate the
contact sheet before validation. A local synthetic 1080×1920 audio/video smoke
test passed at exactly 30 fps with the expected frame count and a 4×4 sheet.
The fix has **not** been verified in GitHub Actions. All three authorized
workflow dispatches this turn were used (one stale dispatch was canceled), so
no further run was started.

WebGL frames are rendered at 360×640 and upscaled; they are not Flux-generated
or verified Pixar-quality artwork. The supplied statement that a battery will
explode in seconds is not guaranteed and should be fact-checked before
publication. Caption timing and intelligibility require listening review.
