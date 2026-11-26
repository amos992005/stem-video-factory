import asyncio,sys,unittest,xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from pilot_short import SCRIPT,synthesize
from vector_studio import Studio,spring_series,frame_plan,beat_boundaries,ROOT,ICONS
from sfx_engine import make_sfx,mix,RATE

class VectorStudioTests(unittest.TestCase):
    def test_script_is_seven_short_scenes(self):
        self.assertEqual(len(SCRIPT),7)
        self.assertLessEqual(sum(len(s.split()) for s in SCRIPT),70)
    def test_icon_sources_are_cached_valid_svg(self):
        self.assertGreaterEqual(len(ICONS),20)
        for name in ICONS:
            root=ET.parse(ROOT/(name+'.svg')).getroot()
            self.assertTrue(root.tag.endswith('svg'));self.assertTrue(root.attrib.get('viewBox'))
        self.assertTrue((ROOT/'TWEMOJI-LICENSE.txt').is_file())
        self.assertTrue((ROOT/'APACHE-2.0.txt').is_file())
    def test_damped_springs(self):
        x=spring_series([0]*10+[90]*70)
        self.assertLess(abs(x[10]),10);self.assertGreater(x[-1],80);self.assertLess(max(x),110)
    def test_visual_cuts_have_max_one_and_half_second_intervals(self):
        for n in range(1,250):
            b=beat_boundaries(n)
            self.assertEqual((b[0],b[-1]),(0,n));self.assertTrue(all(0<y-x<=45 for x,y in zip(b,b[1:])))
    def test_native_svgdom_frames_move(self):
        timeline=[{'index':i,'start':i*4,'duration':4,'frames':120} for i in range(7)]
        frames=list(frame_plan(timeline,np.linspace(0,1,840)))
        self.assertEqual(len(frames),840);self.assertEqual(frames[120][0],1);self.assertIsNotNone(frames[120][6])
        studio=Studio(270,480)
        for i in range(7):
            a=studio.frame(frames[i*120+25]);b=studio.frame(frames[i*120+92])
            self.assertEqual(len(a),270*480*4);self.assertNotEqual(a,b)
    def test_edge_retry_keeps_each_scene(self):
        attempts={}
        async def fake(index,text,tmp):
            attempts[index]=attempts.get(index,0)+1
            if index==2 and attempts[index]<3:raise RuntimeError('temporary')
            return index,text
        async def no_delay(n):pass
        with patch('pilot_short.synthesize_one',fake),patch('pilot_short.asyncio.sleep',no_delay):
            clips=asyncio.run(synthesize(Path('/tmp')))
        self.assertEqual([v[0] for v in clips],list(range(7)));self.assertEqual(attempts[2],3)
    def test_sfx_and_ducking(self):
        timeline=[{'index':i,'start':i*4,'duration':4,'frames':120} for i in range(7)]
        voice=np.full(RATE*28,.04,dtype=np.float32);fx=make_sfx(timeline,len(voice));out=mix(voice,timeline)
        self.assertEqual(len(out),len(voice));self.assertGreater(np.max(np.abs(fx)),.05);self.assertLessEqual(np.max(np.abs(out)),.941)
if __name__=='__main__':unittest.main()
