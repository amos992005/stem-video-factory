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

class CompositionTests(unittest.TestCase):
    def test_contact_sheet_cells(self):
        from visual_audit import split_sheet
        grid=np.zeros((1080,1600),np.uint8)
        grid[180:360,320:640]=123
        frames=split_sheet(grid)
        self.assertEqual(len(frames),30)
        self.assertEqual(frames[6][20,20],123)
        self.assertEqual(frames[0][20,20],0)

    def test_layout_flags_fixed_template(self):
        from visual_audit import composition_pairs, MIN_DIVERSITY
        frame=np.zeros((180,320),np.uint8);frame[30:100,40:100]=200
        pairs=composition_pairs([frame.copy() for _ in range(30)])
        self.assertTrue(all(value < MIN_DIVERSITY for _,_,value in pairs))

    def test_composition_stride_and_background_baseline(self):
        from visual_audit import composition_pairs, layout_descriptor
        frame=np.full((180,320),40,np.uint8);frame[20:70,20:80]=200
        self.assertEqual(len(composition_pairs([frame]*30, stride=7)),23)
        np.testing.assert_allclose(layout_descriptor(frame),layout_descriptor(frame+10),atol=1e-9)

    def test_layout_ignores_subtitle_zone(self):
        from visual_audit import layout_descriptor
        a=np.zeros((180,320),np.uint8);a[20:80,40:100]=200
        b=a.copy();b[155:175,:]=255
        np.testing.assert_allclose(layout_descriptor(a),layout_descriptor(b))

    def test_layout_detects_major_recomposition(self):
        from visual_audit import layout_descriptor, MIN_DIVERSITY
        a=np.zeros((180,320),np.uint8);a[20:70,20:80]=200
        b=np.zeros_like(a);b[60:120,220:300]=200
        diff=np.abs(layout_descriptor(a)-layout_descriptor(b)).sum()/2
        self.assertGreater(diff,MIN_DIVERSITY)
