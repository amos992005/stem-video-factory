"""Render the exact nine-scene vector pilot from narration and live SVG frames."""
from __future__ import annotations
import argparse,asyncio,io,json,math,multiprocessing as mp,os,shutil,subprocess,tempfile,time
from pathlib import Path
import numpy as np
import av
import resvg_py
from pilot_audio import RATE,VOICE,synthesize_one,read_wav,write_wav,silence_bounds,align_source
from subtitle_engine import Word,collect_words,group_words,write_ass
from vector_studio import FPS,frame_plan,svg_frame
from sfx_engine import mix

SCRIPT=(
"Connect your wall outlet straight to your phone battery—and boom, it explodes!",
"Yet inside this tiny plastic block, electricity literally jumps across thin air without touching a single wire!",
"See, wall power is a violent firehose—one hundred twenty volts slamming forward and backward sixty times a second.",
"Your battery needs a calm, five-volt stream flowing smoothly in just one direction.",
"So inside the charger, Stage One is the Transformer. Because AC flips back and forth, it launches pulsing magnetic rings across an air gap into a smaller coil—crushing the voltage down!",
"Stage Two: the Diode. It acts like a one-way subway turnstile—blocking every backward surge!",
"Add four diodes in a diamond bridge, and every backward push gets rerouted forward—wasting zero energy!",
"Finally, a Capacitor acts like a water tower—filling in the gaps until the flow is razor-flat.",
"Four miniature machines inside one tiny plug. Follow Dr. Volt to see what happens inside your screen next!",
)

def run(*args):subprocess.run([str(x) for x in args],check=True,stdout=subprocess.DEVNULL)

async def synthesize(tmp):return await asyncio.gather(*(synthesize_one(i,text,tmp) for i,text in enumerate(SCRIPT)))

def audio(tmp):
    clips=asyncio.run(synthesize(tmp));voice_parts=[];timeline=[];position=0
    for i,(mp3,_) in enumerate(clips):
        raw=tmp/f'raw-{i}.wav';run('ffmpeg','-v','error','-y','-i',mp3,'-ac','1','-ar',RATE,'-c:a','pcm_s16le',raw)
        sample=read_wav(raw);start,end=silence_bounds(sample);sample=sample[start:end]
        # Add breathing room without clipping or changing the exact supplied text.
        frames=math.ceil((len(sample)/RATE+.12)*FPS);target=frames*(RATE//FPS)
        sample=np.pad(sample,(int(.06*RATE),target-len(sample)-int(.06*RATE)))
        clip=tmp/f'scene-{i}.wav';write_wav(clip,sample);voice_parts.append(sample)
        timeline.append({'index':i,'start':position/FPS,'frames':frames,'duration':frames/FPS,'audio':str(clip)})
        print(f'Scene {i+1}: {frames/FPS:.2f}s, {len(SCRIPT[i].split())} words',flush=True);position+=frames
    voice=np.concatenate(voice_parts);write_wav(tmp/'voice.wav',voice)
    n=RATE//FPS;rms=np.sqrt(np.mean(voice[:len(voice)//n*n].reshape(-1,n)**2,axis=1))
    rms=np.clip(rms/.13,0,1)
    print(f'Natural Edge {VOICE} +12%: {len(voice)/RATE:.2f}s; no words cut or extra speed-up.',flush=True)
    return voice,rms,timeline

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

def raster(plan):
    svg=svg_frame(*plan)
    font='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    opts={'svg_string':svg,'width':1080,'height':1920}
    if Path(font).exists():opts.update(skip_system_fonts=True,font_files=[font])
    return resvg_py.svg_to_bytes(**opts)

def render(timeline,rms,ass,mixfile,dest,workers=2):
    total=sum(b['frames'] for b in timeline)
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','image2pipe','-vcodec','png','-framerate','30','-i','pipe:0',
         '-i',str(mixfile),'-vf',f'ass={ass}', '-map','0:v:0','-map','1:a:0','-frames:v',str(total),
         '-r','30','-c:v','libx264','-threads','2','-preset','veryfast','-crf','18','-pix_fmt','yuv420p',
         '-c:a','aac','-b:a','192k','-movflags','+faststart',str(dest)]
    print(f'Rendering {total} native 1080×1920 SVG frames using resvg ({workers} workers).',flush=True)
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        with mp.Pool(workers) as pool:
            for i,png in enumerate(pool.imap(raster,frame_plan(timeline,rms),chunksize=2)):
                proc.stdin.write(png)
                if (i+1)%150==0:print(f'Rasterized {i+1}/{total} frames.',flush=True)
        proc.stdin.close()
        if proc.wait()!=0:raise RuntimeError('FFmpeg encode failed')
    except BaseException:
        proc.kill();proc.wait();raise

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
        tmp=Path(d);voice,rms,timeline=audio(tmp);ass=captions(tmp,timeline)
        write_wav(tmp/'mix.wav',mix(voice,timeline));shutil.copyfile(ass,outdir/'pilot_captions.ass')
        video=outdir/'short_01_pilot_9x16.mp4';render(timeline,rms,ass,tmp/'mix.wav',video,workers)
        duration=sum(b['frames'] for b in timeline)/FPS
        sheet=outdir/'pilot_contact_sheet.png'
        run('ffmpeg','-v','error','-y','-i',video,'-vf',f'fps=16/{duration:.6f},scale=270:480:flags=lanczos,tile=4x4:nb_frames=16','-frames:v','1','-update','1',sheet)
        verify(video,timeline)
        metadata={'engine':'SVG / resvg native vector rendering','duration':duration,'fps':FPS,'frames':sum(b['frames'] for b in timeline),
                  'scenes':[{k:v for k,v in b.items() if k!='audio'} for b in timeline],
                  'narration':'Edge Andrew +12%; no additional speed-up','captions':'faster-whisper tiny.en word timestamps, exact script alignment',
                  'render_seconds':time.monotonic()-start,'verification':'passed'}
        (outdir/'render_metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
        print(f'Vector pilot completed in {metadata["render_seconds"]:.1f}s. Duration: {duration:.2f}s.',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',default='output/pilot');parser.add_argument('--workers',type=int,default=2);args=parser.parse_args()
    try:build(args.output,args.workers)
    except Exception as exc:
        import sys
        print(f'::error title=Vector pilot failed::{type(exc).__name__}: {exc}',file=sys.stderr,flush=True);raise SystemExit(1)
