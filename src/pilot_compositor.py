"""One 28-second portrait pilot: AI art + independent 30 fps compositing.

No scenery or character is drawn with Pillow. Backgrounds/cutouts come only from
Pollinations; numpy generates the requested foreground particle VFX. Pillow is
used to resample and composite the AI character cutouts.
"""
from __future__ import annotations
import argparse, concurrent.futures, math, subprocess, tempfile, time
from pathlib import Path
import numpy as np
from PIL import Image
from ai_asset_generator import BACKDROPS, generate_all
from pilot_audio import BEAT, DURATION, RATE, SCRIPT, build_voice, mix_and_envelope

W,H=540,960
FPS=30
POSES=('dr_volt_curious.png','dr_volt_shocked.png','dr_volt_pointing.png','dr_volt_shocked.png','dr_volt_pointing.png','dr_volt_pointing.png','dr_volt_mindblown.png')
IMPACTS=('','EXPLODE!','60 TIMES!','SHATTER!','ONE-WAY','FOUR ROOMS','THIN AIR!')

def run(*args):subprocess.run([str(x) for x in args],check=True,stdout=subprocess.DEVNULL)

def spring(t):
    if t<0:return 0.
    return 1-math.exp(-6*t)*(math.cos(10*t)+.12*math.sin(10*t))

def dot(arr,x,y,r,color,alpha):
    """Soft glowing bokeh/energy, not a replacement for any AI artwork."""
    x=int(x);y=int(y);r=int(r);x0=max(0,x-r);x1=min(W,x+r+1);y0=max(0,y-r);y1=min(H,y+r+1)
    if x1<=x0 or y1<=y0:return
    yy,xx=np.ogrid[y0-y:y1-y,x0-x:x1-x];fall=np.clip(1-(xx*xx+yy*yy)/(r*r),0,1)**2
    region=arr[y0:y1,x0:x1];a=(fall*alpha).astype(np.uint8);mask=a>region[:,:,3]
    region[:,:,:3][mask]=color;region[:,:,3][mask]=a[mask]

def line(arr,x1,y1,x2,y2,color,alpha=220,thickness=1):
    steps=max(2,int(max(abs(x2-x1),abs(y2-y1))))
    xs=np.linspace(x1,x2,steps).astype(int);ys=np.linspace(y1,y2,steps).astype(int)
    for dx in range(-thickness,thickness+1):
        for dy in range(-thickness,thickness+1):
            xx=xs+dx;yy=ys+dy;valid=(xx>=0)&(xx<W)&(yy>=0)&(yy<H)
            arr[yy[valid],xx[valid],:3]=color;arr[yy[valid],xx[valid],3]=alpha

def effects(beat,frame):
    """Thirty independently animated frames per second with deterministic seeds."""
    arr=np.zeros((H,W,4),dtype=np.uint8);t=frame/FPS;rng=np.random.default_rng(7400+beat)
    # Floating bokeh plus 60 fast embers or directional spray/shards.
    count=60 if beat<2 else 32
    for i in range(count):
        x=rng.uniform(0,W);y=rng.uniform(40,H*.77);velocity=rng.uniform(35,160)
        if beat<2:
            xx=(x+velocity*t*(1 if i%2 else -1))%W;yy=(y-velocity*t*.6)%int(H*.78)
            dot(arr,xx,yy,4+i%5,(255,177,77) if i%3 else (100,239,255),100+i%80)
        elif beat<4:
            xx=(x+velocity*t*2)%W;yy=(y+velocity*t*.5)%int(H*.78)
            color=(111,223,255) if beat==2 else (216,251,255)
            line(arr,xx,yy,xx-18-i%20,yy-6,color,130,0)
        else:
            xx=(x+20*math.sin(t*2+i))%W;yy=(y-velocity*t*.35)%int(H*.78)
            dot(arr,xx,yy,4+i%6,(50,238,244),100+i%100)
    if beat<2:
        # Fast changing branching electric arcs, brighter around the impact.
        rng=np.random.default_rng(1800+beat*100+frame//3)
        for bolt in range(3):
            x=rng.uniform(35,W-35);y=65.;points=[(x,y)]
            for j in range(6):x+=rng.uniform(-45,45);y+=75;points.append((x,y))
            for a,b in zip(points,points[1:]):line(arr,*a,*b,(73,220,255),145,2);line(arr,*a,*b,(234,255,255),230,0)
            mid=points[3];line(arr,*mid,mid[0]+rng.uniform(-75,75),mid[1]+100,(95,226,255),170,1)
    if beat>=4:
        # Pulsing open shockwave rings, below titles and above caption region.
        radius=12+(frame%45)*1.7;cx=W*.5;cy=H*.39
        theta=np.linspace(0,2*np.pi,130);x=(cx+radius*np.cos(theta)).astype(int);y=(cy+radius*np.sin(theta)).astype(int)
        ok=(x>=0)&(x<W)&(y>=0)&(y<H);arr[y[ok],x[ok],:3]=(105,255,255);arr[y[ok],x[ok],3]=np.uint8(max(20,190-3*(frame%45)))
    return Image.fromarray(arr,'RGBA')

def frame_overlay(beat,frame,cutout,rms):
    """Independent spring slide + RMS squash/stretch and slight tilt."""
    base=effects(beat,frame);t=frame/FPS;amp=float(rms[min(len(rms)-1,beat*120+frame)])
    width=235;target_height=round(width*cutout.height/cutout.width)
    if target_height>420:target_height=420;width=round(target_height*cutout.width/cutout.height)
    sx=1-.04*amp;sy=1+.06*amp
    char=cutout.resize((max(1,round(width*sx)),max(1,round(target_height*sy))),Image.Resampling.BILINEAR)
    char=char.rotate(3*math.sin(t*2.2),resample=Image.Resampling.BILINEAR,expand=True)
    # Slide from outside the canvas with overshoot spring; alternate screen side.
    progress=spring(t);right=beat%2==1
    target_x=W-char.width-14 if right else 14
    offscreen=W+20 if right else -char.width-20
    x=round(offscreen+(target_x-offscreen)*progress)
    # Keep the cutout below the 75% subtitle baseline. Its lower body can
    # extend offscreen, as in a foreground presenter entering the shot.
    y=round(755-9*amp+6*math.sin(t*2.3))
    base.alpha_composite(char,(x,y))
    return base.tobytes()

def add_impact_words(ass):
    with open(ass,'a',encoding='utf8') as f:
        for i,word in enumerate(IMPACTS):
            if not word:continue
            start=i*BEAT+.28;end=i*BEAT+1.2
            def ts(t):return f'0:00:{int(t):02d}.{round((t%1)*100):02d}'
            f.write('Dialogue: 1,'+ts(start)+','+ts(end)+',Default,,0,0,0,,{\\an5\\pos(540,420)\\fs92\\bord7\\1c&H20D7FF&\\fscx72\\fscy72\\t(0,180,\\fscx115\\fscy115)\\fad(50,220)}'+word+'\n')

def render_beat(task):
    i,cache,tmp,rms,ass=task;backdrop=Path(cache)/list(BACKDROPS)[i];cutout=Image.open(Path(cache)/POSES[i]).convert('RGBA')
    dest=Path(tmp)/f'beat_{i}.mp4'
    # Ease-out camera push from 1.0 to 1.18; pan and damped shake live on the
    # background, while the character and VFX remain independent foregrounds.
    z="1+0.18*(1-pow(1-min(on/119,1),3))"
    shake="20*exp(-on/18)*sin(on*1.8)" if i<2 else "0"
    graph=(f"[0:v]zoompan=z='{z}':x='iw/2-iw/zoom/2+12*sin(on/36)+{shake}':"
           f"y='ih/2-ih/zoom/2+16*cos(on/47)+{shake}':d=1:s=1080x1920:fps=30,vignette=PI/5[bg];"
           f"[1:v]scale=1080:1920:flags=bilinear[fx];[bg][fx]overlay=0:0:shortest=1,"
           f"fade=t=in:st=0:d=0.2:color=white,setpts=PTS+{i*BEAT}/TB,ass='{ass}',setpts=PTS-{i*BEAT}/TB[v]")
    cmd=['ffmpeg','-v','error','-y','-filter_complex_threads','1','-loop','1','-framerate','30','-i',str(backdrop),
         '-f','rawvideo','-pixel_format','rgba','-video_size',f'{W}x{H}','-framerate','30','-i','pipe:0',
         '-filter_complex',graph,'-map','[v]','-frames:v','120','-r','30','-an','-c:v','libx264','-threads','2','-preset','veryfast','-crf','18','-pix_fmt','yuv420p',str(dest)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for frame in range(120):proc.stdin.write(frame_overlay(i,frame,cutout,rms))
        proc.stdin.close()
        if proc.wait()!=0:raise RuntimeError(f'FFmpeg failed on beat {i+1}')
    except BaseException:
        proc.kill();proc.wait();raise
    print(f'Rendered beat {i+1}',flush=True);return dest

def verify(video):
    import av
    with av.open(str(video)) as container:
        v=next(s for s in container.streams if s.type=='video')
        assert (v.width,v.height,str(v.average_rate))==(1080,1920,'30')
        assert v.frames==840,v.frames
        assert any(s.type=='audio' for s in container.streams)
        assert abs(container.duration/1_000_000-28)<.1
    print('Verified 1080x1920, 30 fps, 840 frames, 28 seconds, audio',flush=True)

def build(outdir='output/pilot',cache='assets/ai_cache',workers=2):
    started=time.monotonic();outdir=Path(outdir).resolve();outdir.mkdir(parents=True,exist_ok=True);cache=Path(cache).resolve()
    with tempfile.TemporaryDirectory(prefix='fast-pilot-') as d:
        tmp=Path(d)
        # Network work happens in parallel. The render stops if either provider
        # fails: no geometric placeholders or silent substitution.
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            art=pool.submit(generate_all,cache);voice_job=pool.submit(build_voice,tmp)
            art.result();voice,ass,ratios=voice_job.result()
        print('Source art and narration complete',flush=True)
        rms=mix_and_envelope(voice,tmp);add_impact_words(ass)
        tasks=[(i,cache,tmp,rms,ass) for i in range(7)]
        with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as pool:paths=list(pool.map(render_beat,tasks))
        listing=tmp/'concat.txt';listing.write_text(''.join(f"file '{p}'\n" for p in paths))
        video=outdir/'short_01_pilot_9x16.mp4'
        run('ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',listing,'-i',tmp/'mix.wav',
            '-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-t','28','-movflags','+faststart',video)
        verify(video)
        sheet=outdir/'pilot_contact_sheet.png'
        run('ffmpeg','-v','error','-y','-i',video,'-vf','fps=16/28,scale=270:480:flags=lanczos,tile=4x4:nb_frames=16','-frames:v','1','-update','1',sheet)
        print(f'Pilot created in {time.monotonic()-started:.1f}s; per-beat extra tempo ratios: {ratios}',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',default='output/pilot');p.add_argument('--cache',default='assets/ai_cache');p.add_argument('--workers',type=int,default=2)
    a=p.parse_args()
    try:
        build(a.output,a.cache,a.workers)
    except Exception as exc:
        # Surface the root failure through the Actions checks API, even when
        # full log downloads are unavailable to the calling environment.
        import sys
        message=str(exc).replace('%','%25').replace('\r','%0D').replace('\n','%0A')
        print('::error title=Pilot generation failed::'+message, file=sys.stderr, flush=True)
        raise
