"""Validate all required streams, exact caption text, and native aspect ratios."""
import json, subprocess, sys
from pathlib import Path
from studio_canvas_engine import SCRIPT, FULL, SHORTS

def verify(directory):
    directory=Path(directory)
    for name in [FULL,*SHORTS]:
        mp4=directory/(name+'.mp4');srt=directory/(name+'.srt');ass=directory/(name+'.ass')
        info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(mp4)]))
        video=next(s for s in info['streams'] if s['codec_type']=='video')
        assert (video['width'],video['height']) == ((1920,1080) if name==FULL else (1080,1920))
        assert video['r_frame_rate']=='30/1',video['r_frame_rate']
        assert any(s['codec_type']=='audio' for s in info['streams'])
        assert float(info['format']['duration'])>1
        raw=srt.read_text(encoding='utf8').strip().split('\n\n')
        text=' '.join(' '.join(entry.splitlines()[2:]) for entry in raw)
        expected=' '.join(SCRIPT[i] for i in (range(len(SCRIPT)) if name==FULL else SHORTS[name]))
        assert text==expected, f'{name}: SRT does not match exact source narration'
        assert 'Dialogue:' in ass.read_text(encoding='utf8')
        print(f"{name}: {video['width']}x{video['height']} at 30 fps, {info['format']['duration']}s, narration captions exact",flush=True)

if __name__=='__main__': verify(sys.argv[1])
