import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from comic_cutout_studio import NAMES,Studio,validate_assets,blend,make_sticker
from pilot_short import SCRIPT
from sfx_engine import mix

class ComicTest(unittest.TestCase):
    def test_required_artwork(self):
        self.assertEqual(len(NAMES),8);validate_assets()
    def test_missing_artwork_is_fatal(self):
        with self.assertRaises(ValueError):validate_assets(Path('/nonexistent'))
    def test_frames_change_and_size(self):
        stickers=[]
        for i in range(8):
            sticker=np.full((50,50,4),255,np.uint8);sticker[:,:,:3]=[i*25,50,100];stickers.append(sticker)
        studio=Studio(stickers)
        a=studio.frame(.3,0,.3,.5); b=studio.frame(1.8,0,1.8,.5)
        self.assertEqual(len(a),1080*1920*4);self.assertNotEqual(a,b)
    def test_script(self):
        self.assertEqual(len(SCRIPT),6);self.assertLessEqual(sum(len(s.split()) for s in SCRIPT),70)
    def test_mix_six_scenes(self):
        timeline=[dict(start=i*3,duration=3,cues={}) for i in range(6)]
        result=mix(np.ones(24_000*18,np.float32)*.05,timeline)
        self.assertEqual(len(result),24_000*18);self.assertLessEqual(np.max(np.abs(result)),1)

if __name__=='__main__':unittest.main()
