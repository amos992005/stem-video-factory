import asyncio, base64, hashlib, io, json, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import time
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from ai_asset_generator import SHOTS, MODELS, cache_complete, decode_google, generate_all, post, safe_error, save_image, shot_path, valid_shot, ImageGenerationError
from pilot_audio import SCRIPT, RATE, silence_bounds, tempo_filters, align_source, synth_sfx
from studio_editor import shot_timeline, build_filter, effect_frame, TRANSITIONS, OVERLAP
from subtitle_engine import Word, write_ass

class PilotTests(unittest.TestCase):
    def test_exact_script_and_shots(self):
        self.assertEqual(len(SCRIPT),7)
        self.assertEqual(hashlib.sha256('\n'.join(SCRIPT).encode()).hexdigest(),'e9ef7a5c1e877ed69ba1bcc82d81e5161d54397f8b7226d6f5cfcf64a9b62ff6')
        self.assertEqual(len(SHOTS),10);self.assertEqual(len(TRANSITIONS),9)
        self.assertIn('gemini-2.0-flash-exp-image-generation',MODELS)
        self.assertIn('gemini-3.1-flash-image-preview',MODELS)
    def test_decode_google_and_mask_secrets(self):
        raw=b'some bytes';v=base64.b64encode(raw).decode()
        self.assertEqual(decode_google({'candidates':[{'content':{'parts':[{'inlineData':{'data':v}}]}}]}),raw)
        self.assertEqual(decode_google({'predictions':[{'bytesBase64Encoded':v}]}),raw)
        self.assertNotIn('supersecret',safe_error('key supersecret','supersecret'))
        with self.assertRaises(ImageGenerationError):decode_google({'candidates':[]})
    def test_cache_reused_without_any_key(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);buf=io.BytesIO();Image.new('RGB',(384,640),(50,40,30)).save(buf,format='PNG')
            save_image(buf.getvalue(),shot_path(root,1));self.assertTrue(valid_shot(shot_path(root,1)))
            for i in range(2,11):shot_path(root,i).write_bytes(shot_path(root,1).read_bytes())
            self.assertTrue(cache_complete(root));self.assertEqual(asyncio.run(generate_all(root,key='',hf='')),root)
            shot_path(root,5).write_bytes(b'not an image');self.assertFalse(cache_complete(root))
            with self.assertRaises(ImageGenerationError):asyncio.run(generate_all(root,key='',hf=''))
    def test_http_429_retry_and_secret_redaction(self):
        class Reply:
            def __init__(self,status,body):self.status=status;self.body=body;self.headers={'Content-Type':'application/json'}
            async def __aenter__(self):return self
            async def __aexit__(self,*args):return False
            async def read(self):return self.body
        class Session:
            def __init__(self):self.calls=[]
            def post(self,url,**kw):
                self.calls.append((url,kw));data=base64.b64encode(b'image').decode()
                return Reply(429,b'{"error":"quota"}') if len(self.calls)==1 else Reply(200,json.dumps({'candidates':[{'content':{'parts':[{'inlineData':{'data':data}}]}}]}).encode())
        import time
        session=Session();result=asyncio.run(post(session,'https://example.com/model',{'x-goog-api-key':'secret'},{},time.monotonic()+3,('secret',),'gemini-2.0'))
        self.assertEqual(result,b'image');self.assertEqual(len(session.calls),2);self.assertNotIn('secret',session.calls[0][0])
    def test_global_timeout_cancels_inflight_shots(self):
        cancelled=[]
        async def slow(session,index,prompt,directory,key,hf,deadline):
            try: await asyncio.sleep(5)
            except asyncio.CancelledError:
                cancelled.append(index)
                raise
        with tempfile.TemporaryDirectory() as d,patch('ai_asset_generator.generate_one',slow):
            start=time.monotonic()
            with self.assertRaisesRegex(ImageGenerationError,'within 0.2 seconds'):
                asyncio.run(generate_all(d,key='test',hf='',budget=.2))
            self.assertLess(time.monotonic()-start,1)
            self.assertEqual(len(cancelled),10)
    def test_shot_mapping_and_true_overlap_filters(self):
        beats=[{'frames':n} for n in [120,90,180,120,120,150,180]];shots=shot_timeline(beats)
        self.assertEqual([x['frames'] for x in shots],[66,54,45,45,180,120,120,68,82,180])
        self.assertEqual(sum(s['frames'] for s in shots),sum(b['frames'] for b in beats))
        graph=build_filter(shots,Path('/tmp/caption.ass'),360,640)
        self.assertEqual(graph.count('xfade=transition='),9)
        self.assertEqual(graph.count('duration=0.333333'),9)
        self.assertIn('avgblur=sizeX=25:sizeY=1',graph);self.assertIn('blend=all_mode=screen',graph)
        self.assertIn('tmix=frames=3',graph);self.assertEqual(OVERLAP,10)
    def test_nonoverlap_audio_and_subtitles(self):
        events=[Word('one',.1,.3),Word('two',.4,.6),Word('three',.7,.9)]
        aligned=align_source('one two three',events,0,1,20,duration=2)
        self.assertEqual([round(w.start,2) for w in aligned],[20.1,20.4,20.7])
        sample=np.r_[np.zeros(RATE//2),np.ones(RATE)*.1,np.zeros(RATE//2)];a,b=silence_bounds(sample)
        self.assertGreater(a,0);self.assertLess(b,len(sample));self.assertEqual(tempo_filters(4),'atempo=2.000000000,atempo=2.000000000')
        self.assertEqual(len(synth_sfx()),28*RATE)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.ass';write_ass(p,[aligned],True,margin_v=480)
            self.assertIn(',80,80,480,1',p.read_text());self.assertIn(r'{\1c&H20D7FF&}',p.read_text())
    def test_vfx_is_animated_overlay_only(self):
        self.assertEqual(len(effect_frame(0)),270*480*3)
        self.assertNotEqual(effect_frame(0),effect_frame(30))
if __name__=='__main__':unittest.main()
