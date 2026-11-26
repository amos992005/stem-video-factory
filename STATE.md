# AI-illustrated studio pilot

[Run 45811851716](https://github.com/amos992005/stem-video-factory/actions/runs/45811851716) succeeded. The job took 1m59s; the editor reported 82.7 seconds using the committed cache. Its `ep01-fast-pilot` artifact (expires 2026-12-26) contains `output/pilot/short_01_pilot_9x16.mp4`, the 4×4 contact sheet, captions, metadata, log and cached images. The artifact is available through the run page; this sandbox could not download the video because the GitHub artifact redirect host is network-restricted.

The editor verified 1080×1920, 30 fps, 1,060 frames, 35.33 seconds and an audio stream. The ASS has 108 narration events with no temporal overlap and six separate impact events. The contact sheet was visually inspected: all ten AI artwork shots are present, with repeated panels for the longer shots; the character design varies somewhat between shots. Full video playback, audio quality and transitions were not directly reviewed in the sandbox. The requested 2.8–3.2-second cutting rhythm is not achieved for all shots because the exact narration and beat mapping were retained.

The ten source images were generated with Arena's image-generation tool at 941×1672, then Lanczos-upscaled to 1080×1920 and committed as `assets/pilot_shots/shot_01.jpg` through `shot_10.jpg`. The successful workflow used only this cache; no geometric or Three.js scene fallback was used. The 82.7-second cached edit did not meet the earlier under-45-second aspiration.

For future missing images the generator tries native `hf-inference`, dynamically inspected Spaces, and paced AI Horde. Its overall generation budget is 300 seconds, with 240 seconds reserved for Horde; each Space can use up to 60 seconds within the shared first-minute budget. These live fallbacks were not exercised in the successful cached run.

The exact requested script states that a battery will violently explode in seconds; this is not guaranteed and should be fact-checked before publication.
