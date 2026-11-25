import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from generate_ep01_svgs import generate
from ep01_math import verify, LATEX
from package_ep01 import captions, timestamp, write_srt, write_ass


class EpisodeTests(unittest.TestCase):
    def test_symbolic_math(self):
        self.assertTrue(verify())
        self.assertEqual(set(LATEX), {'ac','transformer','half','rect','cap'})

    def test_svgs(self):
        with tempfile.TemporaryDirectory() as tmp:
            generate(tmp)
            paths=list(Path(tmp).glob('*.svg'))
            self.assertEqual(len(paths),4)
            for path in paths:
                raw=path.read_text()
                root=ET.fromstring(raw)
                self.assertIn('white',raw.lower())
                self.assertIn('background-color:none',raw)
                self.assertFalse(any(e.tag.endswith('text') for e in root.iter()))

    def test_captions_and_formatting(self):
        words=[SimpleNamespace(word=' hello',start=0.0,end=.4),SimpleNamespace(word=' world.',start=.5,end=.9),SimpleNamespace(word=' next',start=1,end=1.3)]
        cues=captions([SimpleNamespace(words=words)])
        self.assertEqual([x[2] for x in cues],['hello world.','next'])
        self.assertEqual(timestamp(59.9996),'00:01:00,000')
        with tempfile.TemporaryDirectory() as tmp:
            srt=Path(tmp)/'test.srt'; ass=Path(tmp)/'test.ass'
            write_srt(srt,cues); write_ass(ass,cues)
            self.assertIn('00:00:00,000 --> 00:00:00,900',srt.read_text())
            self.assertIn('PlayResY: 1920',ass.read_text())
            self.assertIn('hello world.',ass.read_text())


if __name__ == '__main__':
    unittest.main()
