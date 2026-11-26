import sys, tempfile, unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.append(str(Path(__file__).resolve().parents[1]/'src'))
from subtitle_engine import Word, collect_words, group_words, write_ass, write_srt


class SubtitleTests(unittest.TestCase):
    def test_group_size_and_punctuation(self):
        words=[Word(x,i*.3,(i+1)*.3) for i,x in enumerate('one two three four five six seven eight nine ten eleven twelve'.split())]
        self.assertEqual([len(g) for g in group_words(words)], [8,4])
        self.assertEqual([len(g) for g in group_words(words,True)], [4,4,4])

    def test_whisper_timing_and_karaoke(self):
        samples=[SimpleNamespace(word=' Hello',start=0.1,end=.4),SimpleNamespace(word=' world.',start=.5,end=.8)]
        group=group_words(collect_words([SimpleNamespace(words=samples)]))
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'test.ass';q=Path(tmp)/'test.srt'
            write_ass(p,group);write_srt(q,group)
            text=p.read_text();events=[line for line in text.splitlines() if line.startswith('Dialogue:')]
            self.assertEqual(len(events),2)
            self.assertIn(r'{\1c&H20D7FF&}Hello',events[0])
            self.assertIn(r'{\1c&H20D7FF&}world.',events[1])
            self.assertIn('0:00:00.10,0:00:00.50',events[0])
            self.assertIn('PlayResX: 1920',text)
            self.assertIn('Hello world.',q.read_text())

    def test_overlapping_whisper_words_do_not_overlap_lines(self):
        samples=[SimpleNamespace(word=' one',start=0.1,end=.8),SimpleNamespace(word=' two',start=.5,end=.9)]
        words=collect_words([SimpleNamespace(words=samples)])
        self.assertLessEqual(words[0].end,words[1].start)

    def test_late_word_duration_cannot_overlap_following_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'x.ass'
            write_ass(p,[[Word('first',0,50)],[Word('second',.5,50)]],True)
            events=[x for x in p.read_text().splitlines() if x.startswith('Dialogue:')]
            self.assertIn('0:00:00.00,0:00:00.50',events[0])
            self.assertIn('0:00:00.50,0:00:01.30',events[1])

    def test_empty_and_markup(self):
        with self.assertRaises(RuntimeError): collect_words([])
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'a.ass';write_ass(p,[[Word('{x}\\y',0,.5)]],portrait=True)
            self.assertIn('(x)y',p.read_text())
            self.assertIn('PlayResY: 1920',p.read_text())

if __name__=='__main__': unittest.main()
