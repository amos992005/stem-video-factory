import sys, unittest, xml.etree.ElementTree as ET
import asyncio
from unittest.mock import patch
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from pilot_short import SCRIPT,synthesize
from vector_studio import svg_frame,spring_angles,frame_plan,scene_art,FPS
from sfx_engine import make_sfx,mix,RATE

class VectorStudioTests(unittest.TestCase):
    def test_nine_scenes_are_valid_dynamic_svg(self):
        self.assertEqual(len(SCRIPT),9)
        for i in range(9):
            a=svg_frame(i,.65,4.0,.4,34,-60)
            b=svg_frame(i,1.15,4.0,.8,60,-90)
            root=ET.fromstring(a)
            self.assertEqual(root.attrib['width'],'1080');self.assertEqual(root.attrib['height'],'1920')
            self.assertIn('linearGradient',a);self.assertIn('radialGradient',a)
            self.assertNotEqual(a,b);self.assertNotIn('<image',a)
    def test_scene_specific_animated_props(self):
        for i in range(9):
            self.assertNotEqual(scene_art(i,.6,5),scene_art(i,2.3,5))
    def test_damped_springs_and_rig(self):
        x=spring_angles([0]*10+[90]*70,80)
        self.assertLess(abs(x[10]),10);self.assertGreater(x[-1],80)
        self.assertLess(max(x),110)
    def test_frame_plan_scene_and_audio_envelope(self):
        timeline=[{'index':i,'start':i,'duration':1,'frames':30} for i in range(9)]
        plans=list(frame_plan(timeline,np.linspace(0,1,270)))
        self.assertEqual(len(plans),270);self.assertEqual(plans[30][0],1)
        self.assertIsNotNone(plans[30][-1]);self.assertGreater(plans[-1][3],plans[0][3])
    def test_edge_retry_keeps_each_scene(self):
        attempts={}
        async def fake(index,text,tmp):
            attempts[index]=attempts.get(index,0)+1
            if index==2 and attempts[index]<3:raise RuntimeError('temporary')
            return index,text
        async def no_delay(n):pass
        with patch('pilot_short.synthesize_one',fake),patch('pilot_short.asyncio.sleep',no_delay):
            clips=asyncio.run(synthesize(Path('/tmp')))
        self.assertEqual([v[0] for v in clips],list(range(9)))
        self.assertEqual(attempts[2],3)
    def test_sfx_length_and_ducked_master(self):
        timeline=[{'index':i,'start':i*2,'duration':2,'frames':60} for i in range(9)]
        voice=np.full(RATE*18,.04,dtype=np.float32)
        effects=make_sfx(timeline,len(voice));out=mix(voice,timeline)
        self.assertEqual(len(out),len(voice));self.assertGreater(np.max(np.abs(effects)),.05)
        self.assertLessEqual(np.max(np.abs(out)),.941)
if __name__=='__main__':unittest.main()
