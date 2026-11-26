# AI-illustrated studio pilot

The single authorized AI pilot run [45807374677](https://github.com/amos992005/stem-video-factory/actions/runs/45807374677) **failed**. The Actions job took 21 seconds, including setup and diagnostics. No AI shots, MP4, or contact sheet were produced. The committed `output/pilot/build.log` contains the HTTP responses, and the `ep01-fast-pilot` artifact contains diagnostics (expires 2026-12-26).

- Gemini 3.1 Flash Image and Gemini 2.5 Flash Image: HTTP 429, Google reports a free-tier quota limit of zero.
- Requested legacy Gemini 2.0 image endpoints and Imagen 3: HTTP 404, model not found or not supported.
- Hugging Face `black-forest-labs/FLUX.1-schnell` via `hf-inference`: HTTP 410, model deprecated and no longer supported by that provider.
- 13 workflow tests passed before generation. The production rendering, character consistency, video quality and cached re-edit speed remain unverified. Local tests also included a synthetic-image 1080×1920, 30 fps, 180-frame test; synthetic images were temporary and never used as production artwork.

No Three.js/geometric image fallback is active. The generator has a 15-second overall generation deadline. A working image-generation service with available quota is needed before another run; do not dispatch another run without authorization.

Historical run [45801513380](https://github.com/amos992005/stem-video-factory/actions/runs/45801513380) was a 35.33-second Three.js draft, not the requested AI pilot. Its old diagnostics were removed from this branch to prevent confusion.

The exact requested script includes a statement that a battery will violently explode in seconds; this is not guaranteed and should be fact-checked before publication.
