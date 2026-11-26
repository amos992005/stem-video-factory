import hashlib, json, sys, tempfile, unittest, wave
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from studio_canvas_engine import SCRIPT, SHORTS, BLOCK_SCENES, POSES, host_sprite, scene_art, extract_rms, align_exact
from subtitle_engine import Word, group_words, write_srt

class CanvasTests(unittest.TestCase):
    def test_exact_script_and_excerpt_choices(self):
        self.assertEqual(len(SCRIPT),11)
        self.assertEqual(hashlib.sha256('\n'.join(SCRIPT).encode()).hexdigest(), 'f7cd15aef833ff7eee9c5ead13f804a7c3be6e898f4b5a808282bbdfdf5a2c51')
        self.assertTrue(all(i in range(11) for v in SHORTS.values() for i in v))
        self.assertTrue(all(len(SCRIPT[i]) for v in SHORTS.values() for i in v))
        self.assertEqual(len(POSES),8)
    def test_cel_variations_and_native_canvas(self):
        self.assertNotEqual(host_sprite(0,0).tobytes(),host_sprite(1,4,True).tobytes())
        for portrait,size in ((False,(1920,1080)),(True,(1080,1920))):
            for scene in set(s for block in BLOCK_SCENES for s in block):
                self.assertEqual(scene_art(scene,1,portrait).size,size)
    def test_alignment_keeps_every_exact_token(self):
        words=[Word('one',.1,.3),Word('three',.8,1.1)]
        aligned=align_exact('one TWO three!',words)
        self.assertEqual([w.text for w in aligned],['one','TWO','three!'])
        self.assertGreaterEqual(aligned[1].start,aligned[0].end)
        self.assertLessEqual(aligned[1].end,aligned[2].start)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.srt';write_srt(p,group_words(aligned))
            self.assertIn('one TWO three!',p.read_text())
    def test_rms_frame_rate(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'a.wav'
            with wave.open(str(path),'wb') as f:
                f.setparams((1,2,16000,0,'NONE','not compressed'))
                f.writeframes(np.concatenate([np.zeros(16000),np.ones(16000)*5000]).astype('<i2').tobytes())
            rms=extract_rms(path)
            self.assertEqual(len(rms),60)
            self.assertEqual(rms[10],0)
            self.assertGreater(rms[40],.1)
if __name__=='__main__': unittest.main()
