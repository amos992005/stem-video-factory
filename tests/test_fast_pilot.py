import hashlib, io, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from ai_asset_generator import BACKDROPS,POSES,SPECS,chroma_cutout,fetch_one,image_url
from pilot_audio import SCRIPT, RATE, BEAT, silence_bounds, tempo_filters, align_source, synth_sfx
from pilot_compositor import effects, frame_overlay, spring
from subtitle_engine import Word, write_ass

class PilotTests(unittest.TestCase):
    def test_script(self):
        self.assertEqual(len(SCRIPT),7)
        self.assertEqual(hashlib.sha256('\n'.join(SCRIPT).encode()).hexdigest(),'e9ef7a5c1e877ed69ba1bcc82d81e5161d54397f8b7226d6f5cfcf64a9b62ff6')
        self.assertEqual(len(BACKDROPS),7) # The request enumerates seven backdrops.
        self.assertEqual(len(POSES),4)
        self.assertEqual(len(SPECS),11)
    def test_url_and_chroma(self):
        self.assertIn('model=flux',image_url('blue red',1080,1920,42))
        pix=np.zeros((100,100,3),dtype=np.uint8);pix[:]=(0,255,0);pix[20:80,20:80]=(200,60,30)
        img=chroma_cutout(Image.fromarray(pix))
        self.assertEqual(img.mode,'RGBA');self.assertGreater(img.getchannel('A').getextrema()[1],250)
        self.assertLess(img.width,100)
    def test_cache_and_validation(self):
        class Response:
            headers={'Content-Type':'image/png'}
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,n):
                b=io.BytesIO();Image.new('RGB',(10,20),(50,40,30)).save(b,format='PNG');return b.getvalue()
        spec=('x.jpg','hello',20,40,42,False)
        with tempfile.TemporaryDirectory() as d,patch('ai_asset_generator.urlopen',return_value=Response()) as op:
            p=fetch_one(spec,d)
            with Image.open(p) as image: self.assertEqual(image.size,(20,40))
            fetch_one(spec,d);self.assertEqual(op.call_count,1)
    def test_exact_alignment_and_y_position(self):
        source='One two—three four!';w=[Word('One',.1,.3),Word('two',.3,.4),Word('three',.4,.5),Word('four',.5,.8)]
        aligned=align_source(source,w,0,1,0)
        self.assertEqual(' '.join(x.text for x in aligned),source)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.ass';write_ass(p,[aligned],True,margin_v=480)
            self.assertIn(',80,80,480,1',p.read_text());self.assertIn(r'{\1c&H20D7FF&}',p.read_text())
    def test_nonzero_beat_offset_is_applied_only_once(self):
        events=[Word('one',.1,.3),Word('two',.4,.6),Word('three',.7,.9)]
        words=align_source('one two three',events,0,1,20,duration=2)
        self.assertEqual([round(w.start,2) for w in words],[20.1,20.4,20.7])

    def test_extreme_timestamps_stay_inside_beat(self):
        words=align_source('one two three four', [Word('one',99,150)],0,1,7,duration=2)
        self.assertTrue(all(7 <= w.start < w.end <= 9 for w in words))
        self.assertTrue(all(a.start < b.start for a,b in zip(words,words[1:])))

    def test_audio_trim_tempo_and_sfx(self):
        sample=np.r_[np.zeros(RATE//2),np.ones(RATE)*.1,np.zeros(RATE//2)]
        a,b=silence_bounds(sample);self.assertGreater(a,0);self.assertLess(b,len(sample));self.assertEqual(tempo_filters(4),'atempo=2.000000000,atempo=2.000000000')
        sfx=synth_sfx();self.assertEqual(len(sfx),28*RATE);self.assertGreater(np.max(np.abs(sfx[4*RATE:5*RATE])),.1)
    def test_effects_and_spring(self):
        self.assertLess(spring(0),.001);self.assertGreater(spring(.5),.9)
        self.assertNotEqual(effects(0,0).tobytes(),effects(0,20).tobytes())
        image=Image.new('RGBA',(100,200),(230,230,230,255));rms=np.ones(840)*.5
        self.assertEqual(len(frame_overlay(0,20,image,rms)),540*960*4)
if __name__=='__main__':unittest.main()
