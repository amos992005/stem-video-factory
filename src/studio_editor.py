"""Ten AI shots, continuous 30fps camera/VFX, overlapping transitions and audio.

No geometric or WebGL artwork fallback: if image generation fails, stop before
TTS or rendering. Pillows are only for validating/resampling generated images;
numpy supplies the explicitly requested small additive particle overlay.
"""
from __future__ import annotations
import argparse, asyncio, json, math, os, shutil, subprocess, tempfile, time
from pathlib import Path
import numpy as np
from PIL import Image
from ai_asset_generator import generate_all, cache_complete, shot_path
from pilot_audio import build_voice, mix_and_envelope
from subtitle_engine import timestamp

FPS=30
OVERLAP=10
# 01→02, 02→03, 03→04, 04→05, 05→06, 06→07, 07→08, 08→09, 09→10.
TRANSITIONS=('zoom','flash','flash','whip','zoom','whip','whip','zoom','zoom')

def shot_timeline(beats):
    if len(beats)!=7:raise ValueError('Expected seven narrative beats')
    layout=((0,.55),(1,.50),(2,None),(3,None),(4,None),(5,.45),(6,None))
    result=[];start=0
    for beat,split in layout:
        n=beats[beat]['frames']
        counts=[round(n*split),n-round(n*split)] if split is not None else [n]
        for count in counts:
            if count<=OVERLAP:raise ValueError('Shot too short for ten-frame transition')
            result.append({'index':len(result)+1,'beat':beat,'start_frame':start,'frames':count})
            start+=count
    if len(result)!=10 or start!=sum(b['frames'] for b in beats):raise ValueError('Invalid shot timing')
    return result

def effect_frame(frame, width=270, height=480):
    """Live foreground bokeh/sparks, never a replacement for AI artwork."""
    arr=np.zeros((height,width,3),np.uint8);t=frame/FPS
    rng=np.random.default_rng(28419)
    for i in range(26):
        x=int((rng.uniform(0,width)+t*rng.uniform(-6,6))%width)
        y=int((rng.uniform(0,height*.74)-t*rng.uniform(4,18))%(height*.74))
        r=3+i%4;x0=max(0,x-r);x1=min(width,x+r+1);y0=max(0,y-r);y1=min(height,y+r+1)
        yy,xx=np.ogrid[y0-y:y1-y,x0-x:x1-x];glow=np.clip(1-(xx*xx+yy*yy)/(r*r),0,1)**2
        color=np.array((255,166,68) if i%4==0 else (55,195,230),dtype=np.float32)
        patch=(glow[...,None]*color*.58).astype('uint8')
        arr[y0:y1,x0:x1]=np.maximum(arr[y0:y1,x0:x1],patch)
    return arr.tobytes()

def enabled(shots,types):
    tests=[]
    for i,kind in enumerate(TRANSITIONS):
        if kind in types:
            start=shots[i+1]['start_frame']/FPS;tests.append(f'between(t,{start:.6f},{start+OVERLAP/FPS:.6f})')
    return '+'.join(tests) or '0'

def build_filter(shots,ass,width=1080,height=1920):
    blocks=[]
    for i,shot in enumerate(shots):
        n=shot['frames'];total=n+(OVERLAP if i<9 else 0)
        p=f'min(on/{max(1,n-1)},1)';ease=f'({p})*({p})*(3-2*({p}))'
        z=f'1+0.12*({ease})'
        if i<9 and TRANSITIONS[i]=='zoom':z=f'if(gte(on,{n}),1.12+0.98*min((on-{n})/{OVERLAP},1),{z})'
        # The burst is limited to explosion/shatter, not every shot.
        shake='12*exp(-on/20)*sin(on*1.8)' if i in (2,5) else '0'
        # An incoming shot for a zoom-through starts at 65% and expands to
        # full frame during the overlap. Pad back to a constant canvas before
        # xfade, so both images really coexist during those ten frames.
        incoming=''
        if i>0 and TRANSITIONS[i-1]=='zoom':
            scale=f'if(lt(n,{OVERLAP}),0.65+0.35*n/{OVERLAP},1)'
            incoming=(f"scale=w='trunc({width}*({scale}))':h='trunc({height}*({scale}))':eval=frame,"
                      f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black:eval=frame,")
        blocks.append(f"[{i}:v]trim=end_frame={total},settb=1/30,setpts=PTS-STARTPTS,"
          f"zoompan=z='{z}':x='iw/2-iw/zoom/2+8*sin(on*1.7/30)+{shake}':"
          f"y='ih/2-ih/zoom/2+6*cos(on*1.3/30)+{shake}':d=1:s={width}x{height}:fps=30,"
          f"rotate='0.01047*sin(t)':ow=iw:oh=ih:c=black,{incoming}setsar=1,settb=1/30,format=yuv444p[v{i}]")
    prior='v0'
    for i,kind in enumerate(TRANSITIONS):
        transition={'zoom':'zoomin','flash':'fade','whip':'slideleft'}[kind]
        offset=shots[i+1]['start_frame']/FPS
        blocks.append(f'[{prior}][v{i+1}]xfade=transition={transition}:duration={OVERLAP/FPS:.6f}:offset={offset:.6f}[x{i}]');prior=f'x{i}'
    flash=[]
    for i,kind in enumerate(TRANSITIONS):
        if kind=='flash':
            center=shots[i+1]['start_frame']/FPS+OVERLAP/FPS/2
            flash.append(f'max(0,1-abs(t-{center:.6f})/0.133333)')
    brightness='0.55*('+('+'.join(flash) if flash else '0')+')'
    zoom_enable=enabled(shots,{'zoom'});whip_enable=enabled(shots,{'whip'})
    # Temporal frame mixing provides a zoom-through smear; avgblur is applied
    # horizontally only during whip transitions. Both inputs truly overlap.
    tint=[]
    for i,kind in enumerate(TRANSITIONS):
        if kind=='flash':
            start=shots[i+1]['start_frame']/FPS
            for color,a,b in [('orange',start+.067,start+.167),('cyan',start+.167,start+.267)]:
                tint.append(f"drawbox=x=0:y=0:w=iw:h=ih:color={color}@0.30:t=fill:enable='between(t,{a:.6f},{b:.6f})'")
    tint_filters=','.join(tint)
    blocks.append(f"[{prior}]tmix=frames=3:weights='1 2 1':enable='{zoom_enable}',"
                  f"avgblur=sizeX=25:sizeY=1:enable='{whip_enable}',eq=brightness='{brightness}':eval=frame,{tint_filters},format=gbrp[story]")
    blocks.append(f"[10:v]scale={width}:{height}:flags=bilinear,format=gbrp[particles]")
    blocks.append(f"[story][particles]blend=all_mode=screen:shortest=1,format=yuv420p,ass='{ass}'[v]")
    return ';'.join(blocks)

def render(shots,cache,ass,voice_mix,dest,width=1080,height=1920):
    total=sum(s['frames'] for s in shots);cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-filter_complex_threads','1']
    for s in shots:cmd+=['-loop','1','-framerate','30','-i',str(shot_path(cache,s['index']))]
    cmd+=['-f','rawvideo','-pixel_format','rgb24','-video_size','270x480','-framerate','30','-i','pipe:0','-i',str(voice_mix)]
    cmd+=['-filter_complex',build_filter(shots,ass,width,height),'-map','[v]','-map','11:a:0',
          '-r','30','-frames:v',str(total),'-c:v','libx264','-threads','2','-preset','veryfast','-crf','18','-pix_fmt','yuv420p',
          '-c:a','aac','-b:a','192k','-movflags','+faststart',str(dest)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for frame in range(total):proc.stdin.write(effect_frame(frame))
        proc.stdin.close()
        if proc.wait()!=0:raise RuntimeError('FFmpeg cinematic edit failed')
    except BaseException:
        proc.kill();proc.wait();raise
    return dest

def verify(video,shots):
    import av
    frames=sum(x['frames'] for x in shots)
    with av.open(str(video)) as c:
        v=next(x for x in c.streams if x.type=='video');observed=(v.width,v.height,str(v.average_rate),v.frames)
        print('Observed width, height, average rate, frames:',observed,flush=True)
        if observed!=(1080,1920,'30',frames):raise ValueError(f'Invalid pilot stream: {observed}; expected 1080x1920/30/{frames}')
        if not any(x.type=='audio' for x in c.streams):raise ValueError('Missing audio')
        if abs(c.duration/1_000_000-frames/FPS)>.15:raise ValueError('Audio/video duration mismatch')

def add_impacts(ass,shots):
    impacts={3:'EXPLODE!',5:'60 TIMES!',6:'SHATTER!',7:'ONE-WAY',9:'FOUR ROOMS',10:'THIN AIR!'}
    with open(ass,'a',encoding='utf8') as f:
        for shot in shots:
            if shot['index'] not in impacts:continue
            start=shot['start_frame']/FPS+.28;end=start+.92
            f.write('Dialogue: 1,'+timestamp(start,True)+','+timestamp(end,True)+',Default,,0,0,0,,{\\an5\\pos(540,420)\\fs92\\bord7\\1c&H20D7FF&\\fscx72\\fscy72\\t(0,180,\\fscx115\\fscy115)\\fad(50,220)}'+impacts[shot['index']]+'\n')

def build(outdir='output/pilot',cache='assets/pilot_shots'):
    start=time.monotonic();outdir=Path(outdir).resolve();outdir.mkdir(parents=True,exist_ok=True);cache=Path(cache).resolve()
    # Fail before starting voice, render, or transitions if any AI image is not
    # available within the bounded provider deadline. No 3D/geometric fallback.
    asyncio.run(generate_all(cache))
    if not cache_complete(cache):raise RuntimeError('Incomplete AI shot cache')
    print('All ten AI illustrations available.',flush=True)
    with tempfile.TemporaryDirectory(prefix='studio-editor-') as d:
        tmp=Path(d);voice,ass,beats=build_voice(tmp);shots=shot_timeline(beats)
        starts=[s['start_frame']/FPS for s in shots]
        mix_and_envelope(voice,tmp,beats,starts);add_impacts(ass,shots);shutil.copyfile(ass,outdir/'pilot_captions.ass')
        video=outdir/'short_01_pilot_9x16.mp4';render(shots,cache,ass,tmp/'mix.wav',video)
        duration=sum(s['frames'] for s in shots)/FPS
        sheet=outdir/'pilot_contact_sheet.png'
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(video),'-vf',f'fps=16/{duration:.6f},scale=270:480:flags=lanczos,tile=4x4:nb_frames=16','-frames:v','1','-update','1',str(sheet)],check=True)
        metadata={'source':'real AI images','duration':duration,'fps':FPS,'shots':shots,'transitions':list(TRANSITIONS),'transition_frames':OVERLAP,'verification':'pending'}
        (outdir/'render_metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
        verify(video,shots);metadata['verification']='passed';metadata['render_seconds']=time.monotonic()-start
        (outdir/'render_metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
        print(f'Studio pilot created in {metadata["render_seconds"]:.1f}s; duration {duration:.2f}s.',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',default='output/pilot');p.add_argument('--cache',default='assets/pilot_shots');args=p.parse_args()
    try:build(args.output,args.cache)
    except Exception as exc:
        import sys
        from ai_asset_generator import safe_error
        message=safe_error(f'{type(exc).__name__}: {exc}',os.environ.get('GEMINI_API_KEY',''),os.environ.get('HF_TOKEN','')).replace('%','%25').replace('\n','%0A').replace('\r','%0D')
        print('::error title=Studio pilot failed::'+message,file=sys.stderr,flush=True)
        raise SystemExit(1)
