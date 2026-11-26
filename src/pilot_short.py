"""Render the seven-scene stickman pilot from narration and cached SVG assets."""
from __future__ import annotations
import argparse,asyncio,io,json,math,multiprocessing as mp,os,shutil,subprocess,tempfile,time
from pathlib import Path
import numpy as np
import av
from pilot_audio import RATE,VOICE,synthesize_one,read_wav,write_wav,silence_bounds,align_source
from subtitle_engine import Word,collect_words,group_words,write_ass
from vector_studio import FPS,frame_plan,Studio,beat_boundaries,ROOT,ICONS
from sfx_engine import mix

SCRIPT=(
"Connect a battery to the wall, and it could catch fire!",
"Your charger moves energy across an air gap, without wires touching.",
"Wall power alternates sixty cycles a second—like a wild firehose.",
"Your battery needs low-voltage, steady current, flowing one way.",
"A transformer transfers energy across that gap and changes voltage.",
"Diodes steer current in one direction, like turnstiles.",
"A capacitor smooths the flow. Follow for more!",
)

def run(*args):subprocess.run([str(x) for x in args],check=True,stdout=subprocess.DEVNULL)

async def synthesize(tmp):
    # Avoid sending all nine requests simultaneously; transient service errors
    # must not cancel unrelated scenes or silently substitute another voice.
    semaphore=asyncio.Semaphore(2)
    async def one(i,text):
        async with semaphore:
            for attempt in range(4):
                try:
                    result=await synthesize_one(i,text,tmp)
                    print(f'Edge voice scene {i+1} received.',flush=True)
                    return result
                except Exception as exc:
                    print(f'Edge voice scene {i+1} attempt {attempt+1}/4: {type(exc).__name__}: {exc}',flush=True)
                    if attempt==3:raise RuntimeError(f'Edge voice scene {i+1} failed after 4 attempts: {type(exc).__name__}: {exc}') from exc
                    await asyncio.sleep(1.0*(2**attempt))
    return await asyncio.gather(*(one(i,text) for i,text in enumerate(SCRIPT)))

def audio(tmp):
    clips=asyncio.run(synthesize(tmp));trimmed=[]
    for i,(mp3,_) in enumerate(clips):
        raw=tmp/f'raw-{i}.wav';run('ffmpeg','-v','error','-y','-i',mp3,'-ac','1','-ar',RATE,'-c:a','pcm_s16le',raw)
        sample=read_wav(raw);start,end=silence_bounds(sample);trimmed.append(sample[start:end])
    natural=sum(len(x)/RATE for x in trimmed)+.07*len(trimmed)
    # A small additional atempo adjustment, if required, avoids clipping words.
    # Never use extreme speed to falsely satisfy the target.
    ratio=max(1.,natural/27.5)
    if ratio>1.12:raise ValueError(f'Natural narration {natural:.2f}s needs {ratio:.2f}x extra speed; script must be shortened')
    voice_parts=[];timeline=[];position=0
    for i,sample in enumerate(trimmed):
        source=tmp/f'trim-{i}.wav';write_wav(source,sample)
        if ratio>1.001:
            adjusted=tmp/f'tempo-{i}.wav';run('ffmpeg','-v','error','-y','-i',source,'-af',f'atempo={ratio:.8f}','-ar',RATE,'-ac','1','-c:a','pcm_s16le',adjusted);sample=read_wav(adjusted)
        frames=math.ceil((len(sample)/RATE+.07)*FPS);target=frames*(RATE//FPS)
        sample=np.pad(sample,(int(.035*RATE),target-len(sample)-int(.035*RATE)))
        voice_parts.append(sample);timeline.append({'index':i,'start':position/FPS,'frames':frames,'duration':frames/FPS});position+=frames
    # Pad only the end if naturally shorter than 25 seconds.
    extra=max(0,25*FPS-position)
    if extra:
        voice_parts[-1]=np.pad(voice_parts[-1],(0,extra*(RATE//FPS)))
        timeline[-1]['frames']+=extra;timeline[-1]['duration']=timeline[-1]['frames']/FPS;position+=extra
    if position/FPS>28.0:raise ValueError(f'Narration remained too long after bounded tempo adjustment: {position/FPS:.2f}s')
    for i,(sample,beat) in enumerate(zip(voice_parts,timeline)):
        clip=tmp/f'scene-{i}.wav';write_wav(clip,sample);beat['audio']=str(clip)
        print(f'Scene {i+1}: {beat["duration"]:.2f}s; visual beats {len(beat_boundaries(beat["frames"]))-1}',flush=True)
    voice=np.concatenate(voice_parts);write_wav(tmp/'voice.wav',voice)
    n=RATE//FPS;rms=np.sqrt(np.mean(voice[:len(voice)//n*n].reshape(-1,n)**2,axis=1));rms=np.clip(rms/.13,0,1)
    print(f'Edge {VOICE} +12%: natural {natural:.2f}s, extra tempo {ratio:.3f}x, final {len(voice)/RATE:.2f}s.',flush=True)
    return voice,rms,timeline,ratio

def captions(tmp,timeline):
    from faster_whisper import WhisperModel
    print('Loading faster-whisper tiny.en (CPU/int8) for word timing.',flush=True)
    model=WhisperModel('tiny.en',device='cpu',compute_type='int8',cpu_threads=2)
    groups=[]
    for beat in timeline:
        segments,_=model.transcribe(beat['audio'],language='en',word_timestamps=True,beam_size=1,vad_filter=False)
        words=collect_words(segments)
        # Preserve the exact script; use Whisper's per-word times for alignment.
        aligned=align_source(SCRIPT[beat['index']],words,0,1,beat['start'],duration=beat['duration'])
        beat['cues']={w.text.strip('.,!?;:').lower():w.start for w in aligned}
        groups.extend(group_words(aligned,portrait=True))
    ass=tmp/'pilot.ass';write_ass(ass,groups,portrait=True,margin_v=220)
    ass.write_text(ass.read_text().replace(r'{\1c&H20D7FF&}',r'{\1c&H00E6FF&}'))
    entries=[]
    for line in ass.read_text().splitlines():
        if line.startswith('Dialogue:'):
            fields=line.split(',',3)
            def sec(v):h,m,s=v.split(':');return int(h)*3600+int(m)*60+float(s)
            entries.append((sec(fields[1]),sec(fields[2])))
    if any(a[1]>b[0]+1e-8 for a,b in zip(entries,entries[1:])):raise ValueError('Caption events overlap')
    print(f'Whisper-timed ASS: {len(entries)} events, zero temporal overlaps, MarginV=220.',flush=True)
    return ass

def validate_props():
    # Validate locally cached SVGs with CairoSVG once, then retain native
    # vector paths in Skia SVGDOM during rendering (no per-frame PNG calls).
    import cairosvg
    for name in ICONS:
        data=(ROOT/(name+'.svg')).read_bytes()
        cairosvg.svg2png(bytestring=data,output_width=24,output_height=24)
    print(f'Validated {len(ICONS)} locally cached Twemoji/Iconify SVGs with CairoSVG.',flush=True)


def render(timeline,rms,ass,mixfile,dest,workers=1):
    total=sum(b['frames'] for b in timeline);studio=Studio()
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pixel_format','bgra','-video_size','1080x1920','-framerate','30','-i','pipe:0',
         '-i',str(mixfile),'-vf',f'ass={ass}', '-map','0:v:0','-map','1:a:0','-frames:v',str(total),
         '-r','30','-c:v','libx264','-threads','2','-preset','veryfast','-crf','18','-pix_fmt','yuv420p',
         '-c:a','aac','-b:a','192k','-movflags','+faststart',str(dest)]
    print(f'Rendering {total} native SVGDOM vector frames at 1080×1920.',flush=True)
    start=time.monotonic();proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for i,plan in enumerate(frame_plan(timeline,rms)):
            proc.stdin.write(studio.frame(plan))
            if (i+1)%150==0:print(f'Rendered {i+1}/{total} frames.',flush=True)
        proc.stdin.close()
        if proc.wait()!=0:raise RuntimeError('FFmpeg encode failed')
    except BaseException:
        proc.kill();proc.wait();raise
    print(f'Native SVGDOM frames and encode: {time.monotonic()-start:.1f}s.',flush=True)

def verify(video,timeline):
    total=sum(x['frames'] for x in timeline)
    with av.open(str(video)) as c:
        v=c.streams.video[0];obs=(v.width,v.height,str(v.average_rate),v.frames)
        print('Video stream:',obs,'audio streams:',len(c.streams.audio),flush=True)
        if obs!=(1080,1920,'30',total) or not c.streams.audio:raise ValueError(f'Invalid video stream {obs}')
        if abs(c.duration/1_000_000-total/FPS)>.15:raise ValueError('Unexpected output duration')

def build(outdir='output/pilot',workers=2):
    start=time.monotonic();outdir=Path(outdir).resolve();outdir.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='vector-pilot-') as d:
        tmp=Path(d);validate_props();voice,rms,timeline,ratio=audio(tmp);ass=captions(tmp,timeline)
        write_wav(tmp/'mix.wav',mix(voice,timeline));shutil.copyfile(ass,outdir/'pilot_captions.ass')
        video=outdir/'short_01_pilot_9x16.mp4';render(timeline,rms,ass,tmp/'mix.wav',video,workers)
        duration=sum(b['frames'] for b in timeline)/FPS
        sheet=outdir/'pilot_contact_sheet.png'
        run('ffmpeg','-v','error','-y','-i',video,'-vf',f'fps=16/{duration:.6f},scale=270:480:flags=lanczos,tile=4x4:nb_frames=16','-frames:v','1','-update','1',sheet)
        verify(video,timeline)
        metadata={'engine':'Twemoji/Iconify SVGDOM / Skia native vector rendering','duration':duration,'fps':FPS,'frames':sum(b['frames'] for b in timeline),
                  'scenes':[{k:v for k,v in b.items() if k!='audio'} for b in timeline],
                  'narration':'Edge Andrew +12%', 'extra_tempo':ratio, 'max_visual_beat_seconds':1.5,'captions':'faster-whisper tiny.en word timestamps, exact script alignment',
                  'render_seconds':time.monotonic()-start,'verification':'passed'}
        (outdir/'render_metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
        print(f'Vector pilot completed in {metadata["render_seconds"]:.1f}s. Duration: {duration:.2f}s.',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',default='output/pilot');parser.add_argument('--workers',type=int,default=1);args=parser.parse_args()
    try:build(args.output,args.workers)
    except Exception as exc:
        import sys
        print(f'::error title=Vector pilot failed::{type(exc).__name__}: {exc}',file=sys.stderr,flush=True);raise SystemExit(1)
