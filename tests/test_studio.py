import sys
import tempfile
import unittest
import wave
from pathlib import Path
import numpy as np
sys.path.append(str(Path(__file__).resolve().parents[1] / 'src'))
from audio_design import generate, synth_pad, make_effect
from visual_audit import motion_windows


class StudioTests(unittest.TestCase):
    def test_audio_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            generate(tmp)
            for name in ('ambient','zap','whoosh','chime'):
                with wave.open(str(Path(tmp)/(name+'.wav'))) as f:
                    self.assertEqual(f.getframerate(),44100)
                    self.assertEqual(f.getnchannels(),1)
                    self.assertGreater(f.getnframes(),1000)
        self.assertTrue(np.isfinite(synth_pad(1)).all())
        self.assertGreater(np.max(np.abs(make_effect('zap'))),.05)

    def test_static_vs_motion(self):
        static=np.zeros((21,40,40),dtype=np.uint8)
        self.assertTrue(all(v==0 for _,v in motion_windows(static)))
        moving=static.copy()
        for i,frame in enumerate(moving): frame[:,i%40:i%40+3]=200
        self.assertTrue(all(v>.01 for _,v in motion_windows(moving)))
        self.assertEqual(len(motion_windows(moving)),11)


if __name__=='__main__': unittest.main()
