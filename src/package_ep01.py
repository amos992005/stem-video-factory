"""Concatenate chapters, transcribe, burn short captions, and validate deliverables."""
import argparse
import json
import subprocess
import tempfile
from pathlib import Path
import subtitle_engine as subtitles

SCENES = ['Ch1_TheHookAndACvsDC', 'Ch2_TheWirelessJumpTransformer', 'Ch3_OneWayValveDiode', 'Ch4_TheMagicDiamondBridge', 'Ch5_TheCapacitorIron']
SHORTS = {
    'Short01_ACvsDC': 'short_01_ac_vs_dc_war_9x16',
    'Short02_WirelessTransformer': 'short_02_wireless_transformer_9x16',
    'Short03_DiamondBridge': 'short_03_diamond_diode_trick_9x16',
}
FULL = 'full_youtube_video_16x9'


def run(*args):
    subprocess.run([str(x) for x in args], check=True)


def timestamp(seconds, ass=False):
    # Quantize first, avoiding 60-second fields at rounding boundaries.
    unit = 100 if ass else 1000
    n = max(0, round(seconds * unit))
    h, n = divmod(n, 3600*unit)
    m, n = divmod(n, 60*unit)
    sec, fraction = divmod(n, unit)
    return f'{h}:{m:02d}:{sec:02d}.{fraction:02d}' if ass else f'{h:02d}:{m:02d}:{sec:02d},{fraction:03d}'


def captions(segments, max_chars=34, max_seconds=3.4):
    """Group Whisper word timestamps into short, readable, non-overlapping cues."""
    result, current = [], []
    def flush():
        if current:
            start, end = current[0][0], current[-1][1]
            result.append((start, max(start + .05, end), ' '.join(x[2] for x in current)))
            current.clear()
    for segment in segments:
        for word in segment.words or []:
            text = word.word.strip()
            if not text:
                continue
            start, end = max(0., float(word.start)), max(float(word.start), float(word.end))
            prospective = ' '.join(x[2] for x in current + [(start,end,text)])
            if current and (len(prospective) > max_chars or end-current[0][0] > max_seconds):
                flush()
            current.append((start,end,text))
            if text.endswith(('.', '?', '!')):
                flush()
    flush()
    return result


def write_srt(path, cues):
    Path(path).write_text('\n\n'.join(f'{i}\n{timestamp(a)} --> {timestamp(b)}\n{text}' for i,(a,b,text) in enumerate(cues,1))+'\n', encoding='utf-8')


def write_ass(path, cues):
    header = '''[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,58,&H0000FFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,1,2,80,80,175,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    lines=[]
    for a,b,text in cues:
        safe=text.replace('\\','').replace('{','').replace('}','')
        lines.append(f'Dialogue: 0,{timestamp(a,True)},{timestamp(b,True)},Default,,0,0,0,,{safe}')
    Path(path).write_text(header+'\n'.join(lines)+'\n', encoding='utf-8')


def transcribe(model, source):
    segments, _ = model.transcribe(str(source), language='en', word_timestamps=True, vad_filter=False, beam_size=5)
    cues=captions(segments)
    if not cues:
        raise RuntimeError(f'No subtitle words detected in {source}')
    return cues


def probe(path, width, height):
    info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)]))
    video=next((s for s in info['streams'] if s['codec_type']=='video'),None)
    audio=next((s for s in info['streams'] if s['codec_type']=='audio'),None)
    if not video or not audio or (video['width'],video['height']) != (width,height) or float(info['format']['duration']) <= 0:
        raise RuntimeError(f'Invalid output streams/dimensions: {path}: {info}')
    print(f"Verified {path}: {width}x{height}, {float(info['format']['duration']):.1f}s, audio present",flush=True)


def package(input_dir, output_dir, model_name):
    from faster_whisper import WhisperModel
    input_dir, output_dir = Path(input_dir).resolve(), Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    for name in SCENES + list(SHORTS):
        if not (input_dir / f'{name}.mp4').is_file():
            raise FileNotFoundError(input_dir / f'{name}.mp4')
    # concat demuxer escaping for the unlikely case of apostrophes in the path.
    with tempfile.TemporaryDirectory() as temp:
        temp=Path(temp)
        listing=temp/'concat.txt'
        listing.write_text(''.join("file '"+str(input_dir / f'{name}.mp4').replace("'", "'\\''")+"'\n" for name in SCENES))
        full=output_dir/f'{FULL}.mp4'
        raw_full=temp/'full-unmixed.mp4'
        run('ffmpeg','-y','-f','concat','-safe','0','-i',listing,'-c','copy',raw_full)
        model=WhisperModel(model_name, device='cpu', compute_type='int8')
        # Transcribe clean narration before adding the music bed.
        full_groups=subtitles.transcribe(model,raw_full,portrait=False)
        subtitles.write_srt(output_dir/f'{FULL}.srt',full_groups)
        full_ass=output_dir/f'{FULL}.ass'
        subtitles.write_ass(full_ass,full_groups,portrait=False)
        pad=Path(__file__).resolve().parents[1]/'assets/audio/ep01/ambient.wav'
        if not pad.is_file():
            from audio_design import generate
            generate(pad.parent)
        mix='[1:a]volume=-20dB[bed];[0:a][bed]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,alimiter=limit=0.95[a]'
        full_filter=f'drawbox=x=0:y=ih*0.84:w=iw:h=ih*0.16:color=0x050814:t=fill,ass={full_ass}'
        run('ffmpeg','-y','-i',raw_full,'-stream_loop','-1','-i',pad,'-filter_complex',mix,'-map','0:v:0','-map','[a]','-vf',full_filter,'-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',full)
        probe(full,1920,1080)
        for scene,name in SHORTS.items():
            source=input_dir/f'{scene}.mp4'
            groups=subtitles.transcribe(model,source,portrait=True)
            subtitles.write_srt(output_dir/f'{name}.srt',groups)
            ass=output_dir/f'{name}.ass'
            subtitles.write_ass(ass,groups,portrait=True)
            dest=output_dir/f'{name}.mp4'
            run('ffmpeg','-y','-i',source,'-stream_loop','-1','-i',pad,'-filter_complex',mix,'-map','0:v:0','-map','[a]','-vf',f'drawbox=x=0:y=ih*0.8125:w=iw:h=ih*0.1875:color=0x050814:t=fill,ass={ass}', '-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',dest)
            probe(dest,1080,1920)
    print('Episode package complete:',output_dir,flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--input-dir',default='staging')
    parser.add_argument('--output-dir',default='output/ep01_phone_charger')
    parser.add_argument('--model',default='base.en')
    args=parser.parse_args()
    package(args.input_dir,args.output_dir,args.model)
