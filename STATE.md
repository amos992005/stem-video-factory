# Fast pilot state

The active workflow is a single manually triggered pilot job. It requests the
seven enumerated Flux backdrops and four character poses, synthesizes the exact
seven-line script, makes one 28-second portrait MP4 and its 4×4 contact sheet,
and uploads `ep01-fast-pilot`. It does not trigger on push.

The pipeline and local tests are implemented; the first and only requested
Actions run has not yet been verified. Pollinations' legacy endpoint and Edge
TTS are externally hosted; availability, model identity, artwork quality and
end-to-end time cannot be guaranteed. Source speech may require additional
speed-up to preserve every requested word within 28 seconds. No earlier render
is evidence that the new pilot succeeded. Review the resulting video, captions,
visuals and technical claims before publication.
