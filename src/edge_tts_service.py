"""Microsoft Edge speech service for Manim Voiceover."""
from pathlib import Path
import os
import tempfile

import edge_tts
from manim_voiceover.helper import remove_bookmarks
from manim_voiceover.services.base import SpeechService


class EdgeTTSService(SpeechService):
    """Generate and cache MP3 voiceovers using the free Edge TTS service.

    Timing in the sample scene uses the full audio duration, not bookmarks.
    This service does not currently supply word boundaries for bookmark timing.
    """

    def __init__(self, voice="en-US-ChristopherNeural", **kwargs):
        super().__init__(**kwargs)
        self.voice = voice

    def generate_from_text(self, text, cache_dir=None, path=None, **kwargs):
        if kwargs:
            raise TypeError(f"Unsupported Edge TTS options: {', '.join(kwargs)}")
        cache_dir = Path(self.cache_dir if cache_dir is None else cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        spoken_text = remove_bookmarks(text)
        input_data = {"input_text": spoken_text, "service": "edge-tts", "voice": self.voice}
        if path is None:
            cached = self.get_cached_result(input_data, cache_dir)
            if cached and (cache_dir / cached["original_audio"]).is_file():
                # Bookmarks are removed for speech but must remain in the returned text.
                return {**cached, "input_text": text}
            audio_path = self.get_audio_basename(input_data) + ".mp3"
        else:
            audio_path = os.fspath(path)
        destination = cache_dir / audio_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        # Do not leave a partial audio file behind when the network request fails.
        fd, temp_name = tempfile.mkstemp(suffix=".mp3", dir=destination.parent)
        os.close(fd)
        try:
            edge_tts.Communicate(spoken_text, self.voice).save_sync(temp_name)
            os.replace(temp_name, destination)
        finally:
            Path(temp_name).unlink(missing_ok=True)
        return {"input_text": text, "input_data": input_data, "original_audio": audio_path}
