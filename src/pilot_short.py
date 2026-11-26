"""Render an AI-illustrated, naturally narrated comic cutout pilot."""
from __future__ import annotations
import argparse,asyncio,io,json,math,multiprocessing as mp,os,shutil,subprocess,tempfile,time
from pathlib import Path
import numpy as np
import av
from pilot_audio import RATE,VOICE,synthesize_one,read_wav,write_wav,silence_bounds,align_source
from subtitle_engine import Word,collect_words,group_words,write_ass
from comic_cutout_studio import FPS, Studio, prepare
from sfx_engine import mix

SCRIPT=(
"Connect your phone battery to the wall, and it could catch fire!",
"Chargers transfer energy across an insulating gap, without wires touching.",
"US wall power alternates sixty times a second, like a firehose.",
"Batteries need a calm, low-voltage, one-way flow.",
"A transformer transfers energy magnetically and changes the voltage.",
"Diodes guide current; a capacitor smooths the output.",
"Now your phone gets usable power. Follow Dr. Volt!",
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
    if natural>28.5:
        raise ValueError(f'Natural narration {natural:.2f}s exceeds the target. Shorten the script; do not speed up speech.')
    voice_parts=[];timeline=[];position=0
    for i,sample in enumerate(trimmed):
        frames=math.ceil((len(sample)/RATE+.07)*FPS);target=frames*(RATE//FPS)
        sample=np.pad(sample,(int(.035*RATE),target-len(sample)-int(.035*RATE)))
        voice_parts.append(sample);timeline.append({'index':i,'start':position/FPS,'frames':frames,'duration':frames/FPS});position+=frames
    # Pad only the end if naturally shorter than 25 seconds.
    extra=max(0,25*FPS-position)
    if extra:
        voice_parts[-1]=np.pad(voice_parts[-1],(0,extra*(RATE//FPS)))
        timeline[-1]['frames']+=extra;timeline[-1]['duration']=timeline[-1]['frames']/FPS;position+=extra
    if position/FPS>29.0:raise ValueError(f'Natural narration exceeds 29 seconds: {position/FPS:.2f}s')
    for i,(sample,beat) in enumerate(zip(voice_parts,timeline)):
        clip=tmp/f'scene-{i}.wav';write_wav(clip,sample);beat['audio']=str(clip)
        print(f'Scene {i+1}: {beat["duration"]:.2f}s',flush=True)
    voice=np.concatenate(voice_parts);write_wav(tmp/'voice.wav',voice)
    n=RATE//FPS;rms=np.sqrt(np.mean(voice[:len(voice)//n*n].reshape(-1,n)**2,axis=1));rms=np.clip(rms/.13,0,1)
    print(f'Edge {VOICE} +12%: natural {natural:.2f}s, final {len(voice)/RATE:.2f}s.',flush=True)
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
    ass=tmp/'pilot.ass';write_ass(ass,groups,portrait=True,margin_v=140)
    ass.write_text(ass.read_text().replace(r'{\1c&H20D7FF&}',r'{\1c&H00E6FF&}'))
    # Hold each caption event until the next one, including sentence pauses,
    # and hold the final line through the short padded tail. No overlaps.
    lines=ass.read_text().splitlines(); indices=[i for i,l in enumerate(lines) if l.startswith('Dialogue:')]
    for j,idx in enumerate(indices):
        fields=lines[idx].split(',',3)
        if j==0: fields[1]='0:00:00.00'
        if j+1<len(indices):fields[2]=lines[indices[j+1]].split(',',3)[1]
        else:
            from subtitle_engine import timestamp
            fields[2]=timestamp(sum(b['duration'] for b in timeline),True)
        lines[idx]=','.join(fields)
    ass.write_text('\n'.join(lines)+'\n')
    entries=[]
    for line in ass.read_text().splitlines():
        if line.startswith('Dialogue:'):
            fields=line.split(',',3)
            def sec(v):h,m,s=v.split(':');return int(h)*3600+int(m)*60+float(s)
            entries.append((sec(fields[1]),sec(fields[2])))
    if any(a[1]>b[0]+1e-8 for a,b in zip(entries,entries[1:])):raise ValueError('Caption events overlap')
    print(f'Whisper-timed ASS: {len(entries)} events, zero temporal overlaps, MarginV=140.',flush=True)
    return ass


def render(timeline,rms,ass,mixfile,dest,stickers,workers=1):
    total=sum(b['frames'] for b in timeline);studio=Studio(stickers)
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pixel_format','bgra','-video_size','1080x1920','-framerate','30','-i','pipe:0',
         '-i',str(mixfile),'-vf',f'ass={ass}', '-map','0:v:0','-map','1:a:0','-frames:v',str(total),
         '-r','30','-c:v','libx264','-threads','2','-preset','veryfast','-crf','18','-pix_fmt','yuv420p',
         '-c:a','aac','-b:a','192k','-movflags','+faststart',str(dest)]
    print(f'Rendering {total} native comic cutout frames at 1080×1920.',flush=True)
    start=time.monotonic();proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for i in range(total):
            t=i/FPS
            scene=next(j for j,b in reversed(list(enumerate(timeline))) if t >= b['start'])
            proc.stdin.write(studio.frame(t,scene,t-timeline[scene]['start'],rms[i]))
            if (i+1)%150==0:print(f'Rendered {i+1}/{total} frames.',flush=True)
        proc.stdin.close()
        if proc.wait()!=0:raise RuntimeError('FFmpeg encode failed')
    except BaseException:
        proc.kill();proc.wait();raise
    print(f'Comic composite frames and encode: {time.monotonic()-start:.1f}s.',flush=True)

def verify(video,timeline):
    total=sum(x['frames'] for x in timeline)
    with av.open(str(video)) as c:
        v=c.streams.video[0];obs=(v.width,v.height,str(v.average_rate),v.frames)
        print('Video stream:',obs,'audio streams:',len(c.streams.audio),flush=True)
        if obs!=(1080,1920,'30',total) or not c.streams.audio:raise ValueError(f'Invalid video stream {obs}')
        if abs(c.duration/1_000_000-total/FPS)>.15:raise ValueError('Unexpected output duration')

def build(outdir='output/pilot',workers=2):
    start=time.monotonic();outdir=Path(outdir).resolve();outdir.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='comic-pilot-') as d:
        tmp=Path(d);stickers=prepare();voice,rms,timeline=audio(tmp);ass=captions(tmp,timeline)
        write_wav(tmp/'mix.wav',mix(voice,timeline));shutil.copyfile(ass,outdir/'pilot_captions.ass')
        video=outdir/'short_01_pilot_9x16.mp4';render(timeline,rms,ass,tmp/'mix.wav',video,stickers,workers)
        duration=sum(b['frames'] for b in timeline)/FPS
        sheet=outdir/'pilot_contact_sheet.png'
        run('ffmpeg','-v','error','-y','-i',video,'-vf',f'fps=16/{duration:.6f},scale=270:480:flags=lanczos,tile=4x4:nb_frames=16','-frames:v','1','-update','1',sheet)
        verify(video,timeline)
        metadata={'engine':'AI comic cutouts / rembg / OpenCV 2.5D','duration':duration,'fps':FPS,'frames':sum(b['frames'] for b in timeline),
                  'scenes':[{k:v for k,v in b.items() if k!='audio'} for b in timeline],
                  'narration':'Edge Andrew +12%', 'extra_tempo':1.0, 'captions':'faster-whisper tiny.en word timestamps, exact script alignment',
                  'render_seconds':time.monotonic()-start,'verification':'passed'}
        (outdir/'render_metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
        print(f'Comic pilot completed in {metadata["render_seconds"]:.1f}s. Duration: {duration:.2f}s.',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',default='output/pilot');parser.add_argument('--workers',type=int,default=1);args=parser.parse_args()
    try:build(args.output,args.workers)
    except Exception as exc:
        import sys
        print(f'::error title=Comic pilot failed::{type(exc).__name__}: {exc}',file=sys.stderr,flush=True);raise SystemExit(1)
