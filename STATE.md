# Fast pilot state

The active workflow is a single manually triggered pilot job. It requests the
seven enumerated Flux backdrops and four character poses, synthesizes the exact
seven-line script, makes one 28-second portrait MP4 and its 4×4 contact sheet,
and is intended to upload `ep01-fast-pilot`. It does not trigger on push.

## One requested Actions run

[Run 45795458025](https://github.com/amos992005/stem-video-factory/actions/runs/45795458025)
failed in the art/voice/render step after 54 seconds on commit `79e2db3`; the
upload step was skipped and no pilot artifact exists. Local unit tests (10) and
one synthetic-fixture beat/FFmpeg smoke test passed before that run. They do
not verify the remote AI art or voice services. The sandbox could not download
GitHub's external-hosted run logs; the checks API reports only exit code 1, so
the failure's cause has not been confirmed. Inspect the job's logs in GitHub
before deciding on a fix. No second run was triggered.

The legacy Pollinations endpoint is deprecated and may be unavailable, rate
limited, watermarked, or fail to identify its actual model. Additional speedup
may be necessary to preserve all words in 28 seconds; assess intelligibility.
The user-supplied statement that a battery will explode in seconds is not
guaranteed and should be fact-checked before publication. The workflow now
emits a check annotation with a caught failure message on future runs, but that
change has not been run on GitHub.
