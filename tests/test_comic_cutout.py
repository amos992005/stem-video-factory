import sys,unittest
from pathlib import Path
import numpy as np
import cv2
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from comic_cutout_studio import (NAMES, Studio, validate_assets, fit_prop,
    remove_small_islands, prop_for, PRESENTER_TOP, PROP_MAX, STAGE)
from pilot_short import SCRIPT
from sfx_engine import mix

class ComicTest(unittest.TestCase):
    def test_required_artwork(self):
        self.assertEqual(len(NAMES),11);validate_assets()
    def test_missing_artwork_is_fatal(self):
        with self.assertRaises(ValueError):validate_assets(Path('/nonexistent'))
    def test_small_islands_removed_and_two_main_components_retained(self):
        alpha=np.zeros((200,200),np.uint8)
        cv2.rectangle(alpha,(10,10),(99,99),255,-1)
        cv2.rectangle(alpha,(140,40),(169,69),255,-1)
        cv2.rectangle(alpha,(190,190),(192,192),255,-1)
        cleaned=remove_small_islands(alpha)
        self.assertEqual(cleaned[191,191],0)
        self.assertEqual(cleaned[20,20],255);self.assertEqual(cleaned[150%200,50],alpha[150%200,50])
        self.assertEqual(cleaned[50,150],255)
    def test_prop_safe_bounds_extreme_aspects(self):
        for h,w in [(20,2000),(2000,20),(1200,1200),(900,1300)]:
            img=np.zeros((h,w,4),np.uint8)
            for zoom in (.6,.86,1,1.2):
                x,y,pw,ph=fit_prop(img,zoom)
                self.assertLessEqual(pw,PROP_MAX[0]);self.assertLessEqual(ph,PROP_MAX[1])
                self.assertGreaterEqual(x,STAGE[0]);self.assertGreaterEqual(y,STAGE[1])
                self.assertLessEqual(x+pw,STAGE[2]);self.assertLessEqual(y+ph,STAGE[3]);self.assertLessEqual(y+ph,PRESENTER_TOP)
    def test_seven_prop_assets_are_used(self):
        used={prop_for(i,0) for i in range(7)}|{prop_for(6,2)}
        self.assertEqual(used,set(range(4,11)))
    def test_frames_change_and_size(self):
        stickers=[]
        for i in range(len(NAMES)):
            sticker=np.full((100,50,4),255,np.uint8);sticker[:,:,:3]=[i*20,50,100];stickers.append(sticker)
        studio=Studio(stickers)
        a=studio.frame(.3,0,.3,.5);b=studio.frame(1.8,0,1.8,.5)
        self.assertEqual(len(a),1080*1920*4);self.assertNotEqual(a,b)
    def test_script(self):
        self.assertEqual(len(SCRIPT),7);self.assertLessEqual(sum(len(s.split()) for s in SCRIPT),75)
    def test_mix_seven_scenes(self):
        timeline=[dict(start=i*3,duration=3,cues={}) for i in range(7)]
        result=mix(np.ones(24_000*21,np.float32)*.05,timeline)
        self.assertEqual(len(result),24_000*21);self.assertLessEqual(np.max(np.abs(result)),1)
if __name__=='__main__':unittest.main()
