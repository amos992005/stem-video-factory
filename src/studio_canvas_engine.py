"""Procedural illustrated episode renderer; no Manim or TeX.

Each shot is a native-aspect Pillow illustration, animated by FFmpeg. Dr. Volt
is a separate 30fps RGBA stream driven by the clean narration's RMS envelope.
"""
from __future__ import annotations
import argparse, asyncio, concurrent.futures, json, math, os, subprocess, tempfile, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=json.loads((ROOT/'src/episode_script.json').read_text(encoding='utf8'))
FULL='full_youtube_video_16x9'
SHORTS={'short_01_ac_vs_dc_war_9x16':[0,1,2], 'short_02_wireless_transformer_9x16':[3,4], 'short_03_diamond_diode_trick_9x16':[7,8,9,10]}
POSES=('curious_question','shocked_exploded','holding_firehose','tour_guide_pointing','pushing_turnstile','routing_traffic','filling_water_tower','proud_100_percent')
# Every block may contain multiple distinct shots. Sub-shot choice is made from
# elapsed audio, never by changing narration or adding words.
BLOCK_SCENES=[('charger','explosion'),('hose','glass','dispenser'),('factory','factory'),('cliff','coil'),('coil','rings','rings'),('pipe','turnstile'),('turnstile','turnstile','pipe'),('diamond','diamond'),('diamond','traffic','traffic'),('tower','tower'),('tower','battery','celebrate')]
POSE_FOR={'charger':0,'explosion':1,'hose':2,'glass':1,'dispenser':3,'factory':3,'cliff':0,'coil':3,'rings':3,'pipe':0,'turnstile':4,'diamond':5,'traffic':5,'tower':6,'battery':7,'celebrate':7}
PALETTES=[((22,28,83),(62,35,115)),((13,58,91),(19,111,125)),((53,31,97),(133,48,83)),((17,44,90),(50,91,131)),((43,34,97),(92,43,126)),((8,59,91),(24,126,128)),((65,31,79),(152,59,82)),((26,48,112),(68,98,145))]

def run(*cmd):
    subprocess.run([str(x) for x in cmd],check=True,stdout=subprocess.DEVNULL)

def font(size):
    for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf','/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf'):
        if Path(p).exists(): return ImageFont.truetype(p,size)
    return ImageFont.load_default()

def glow(draw,x,y,r,color):
    for i in range(5,0,-1):
        rr=r*i/5; draw.ellipse((x-rr,y-rr,x+rr,y+rr),fill=(*color,int(13+18*(1-i/5))))

def background(w,h,seed):
    """Smooth color field plus spotlights, perspective grid, and soft bokeh."""
    top,bottom=PALETTES[seed%len(PALETTES)]
    y=np.linspace(0,1,h)[:,None,None]; x=np.linspace(0,1,w)[None,:,None]
    col=np.array(top)[None,None,:]*(1-y)+np.array(bottom)[None,None,:]*y
    light=np.exp(-(((x-(.25+.12*(seed%4)))**2)/.1+((y-.34)**2)/.12))*38
    arr=np.clip(col+light,0,255).astype('uint8');arr=np.broadcast_to(arr,(h,w,3)).copy()
    im=Image.fromarray(arr,'RGB').convert('RGBA'); layer=Image.new('RGBA',(w,h));d=ImageDraw.Draw(layer)
    rng=np.random.default_rng(seed+71)
    for _ in range(35):
        xx,yy=rng.uniform(0,w),rng.uniform(0,h*.83);r=rng.uniform(4,22)*w/1920
        d.ellipse((xx-r,yy-r,xx+r,yy+r),fill=(151,231,255,int(rng.integers(12,42))))
    van=(w*.5,h*.69)
    for xx in np.linspace(-w,w*2,15):d.line((van,(xx,h)),fill=(125,221,245,38),width=max(1,w//960))
    for f in (.73,.77,.82,.88,.95):d.line((0,h*f,w,h*f),fill=(125,221,245,35),width=2)
    return Image.alpha_composite(im,layer)

class Art:
    """A compact vector-like drawing API over normalized 1000 x 700 coordinates."""
    def __init__(self, im, box): self.im=im; self.d=ImageDraw.Draw(im,'RGBA'); self.x,self.y,self.w,self.h=box
    def pt(self,p):return (self.x+p[0]*self.w/1000,self.y+p[1]*self.h/700)
    def rect(self,box,fill,outline=None,r=0,width=5):
        a=self.pt(box[:2]);b=self.pt(box[2:]); self.d.rounded_rectangle((*a,*b),radius=r*self.w/1000,fill=fill,outline=outline,width=max(1,int(width*self.w/1000)))
    def ellipse(self,box,fill,outline=None,width=5):
        a=self.pt(box[:2]);b=self.pt(box[2:]);self.d.ellipse((*a,*b),fill=fill,outline=outline,width=max(1,int(width*self.w/1000)))
    def poly(self,pts,fill,outline=None,width=5):
        points=[self.pt(p) for p in pts];self.d.polygon(points,fill=fill)
        if outline:self.d.line(points+[points[0]],fill=outline,width=max(1,int(width*self.w/1000)),joint='curve')
    def line(self,pts,fill,width=8):self.d.line([self.pt(p) for p in pts],fill=fill,width=max(1,int(width*self.w/1000)),joint='curve')
    def text(self,xy,s,size,fill,anchor='mm'):
        self.d.text(self.pt(xy),s,font=font(max(10,int(size*self.w/1000))),fill=fill,anchor=anchor,stroke_width=0)

INK=(17,28,58,255); WHITE=(240,252,255,255); CYAN=(38,225,238,255); GOLD=(255,212,78,255); CORAL=(255,102,88,255); BLUE=(66,163,255,255)
def phone(a,x,y,s=1,charge=True):
    a.rect((x,y,x+140*s,y+240*s),INK,WHITE,r=18,width=5);a.rect((x+12*s,y+22*s,x+128*s,y+217*s),(35,63,91,255),r=8)
    a.rect((x+34*s,y+80*s,x+106*s,y+151*s),(90,255,190,255) if charge else CORAL,WHITE,r=5)
    a.rect((x+60*s,y+70*s,x+80*s,y+80*s),WHITE,r=2)
    if charge:a.poly([(x+76*s,y+88*s),(x+57*s,y+119*s),(x+70*s,y+119*s),(x+62*s,y+143*s),(x+89*s,y+109*s),(x+76*s,y+109*s)],WHITE)

def charger(a,x,y,s=1):
    a.poly([(x,y),(x+145*s,y-30*s),(x+220*s,y+10*s),(x+75*s,y+42*s)],(250,255,255,255),INK)
    a.poly([(x,y),(x+75*s,y+42*s),(x+75*s,y+180*s),(x,y+140*s)],(183,216,232,255),INK)
    a.poly([(x+75*s,y+42*s),(x+220*s,y+10*s),(x+220*s,y+145*s),(x+75*s,y+180*s)],(229,244,247,255),INK)
    for off in (35,90):a.line([(x+off*s,y-8*s),(x+(off-10)*s,y-64*s)],(220,231,239,255),15)
    a.ellipse((x+120*s,y+81*s,x+148*s,y+109*s),CYAN)

def coil(a,x,y,s=1,color=GOLD):
    a.line([(x-50*s,y+65*s),(x+20*s,y+65*s)],(255,174,88,255),15)
    for i in range(5):a.ellipse((x+(i*25)*s,y-45*s,x+(i*25+53)*s,y+75*s),None,color,12)
    a.line([(x+150*s,y+10*s),(x+210*s,y+10*s)],(255,174,88,255),15)


def layout_box(portrait, variant):
    """Reframe each shot as a deliberate wide, detail, or offset composition."""
    if portrait:
        return [(20,130,1040,790),(-215,120,1430,1085),(-215,280,1210,920),(65,120,1240,940)][variant%4]
    return [(160,60,1600,930),(-150,-90,2100,1220),(-140,80,1580,920),(450,10,1530,890)][variant%4]

def scene_art(scene,variant,portrait):
    w,h=(1080,1920) if portrait else (1920,1080); im=background(w,h,variant+list(POSE_FOR).index(scene))
    # Portrait deliberately reflows the scene above the host and caption zone.
    box=layout_box(portrait,variant)
    a=Art(im,box)
    if scene in ('charger','explosion'):
        charger(a,160,230,1.3);phone(a,660,210,1.35,False)
        a.line([(430,340),(550,340),(570,370),(650,370)],CORAL,16)
        if scene=='explosion':
            a.poly([(735,135),(762,197),(825,155),(809,224),(891,228),(827,270),(867,340),(795,309),(764,381),(738,312),(670,353),(694,282),(630,249),(701,224)],(255,147,55,255),GOLD,7)
            phone(a,705,225,.55,False)
        for x,y in [(550,190),(635,420),(400,480)]:a.ellipse((x,y,x+28,y+28),GOLD)
    elif scene in ('hose','glass','dispenser'):
        a.line([(40,250),(200,250),(230,300)],(203,65,78,255),70);a.rect((190,240,280,330),(216,228,238,255),INK,r=16)
        for i in range(5):a.line([(280,265+i*11),(500+i*12,210+i*35),(650,320+i*16)],(56,184+i*12,255,230),14)
        a.poly([(665,255),(820,255),(805,440),(690,440)],(147,234,255,95),WHITE,8)
        if scene!='dispenser':
            for pts in [[(690,285),(730,340),(707,372)],[(805,300),(755,345),(790,410)],[(735,340),(760,400)]]:a.line(pts,WHITE,5)
            a.poly([(760,230),(782,175),(794,225),(835,195),(812,245)],GOLD)
        else:
            a.rect((480,230,600,390),(197,236,247,255),INK,r=22);a.line([(570,300),(705,300),(705,350)],CYAN,14)
    elif scene=='factory':
        a.poly([(110,245),(730,245),(875,340),(260,340)],(124,190,218,255),INK)
        a.poly([(110,245),(260,340),(260,510),(110,410)],(61,116,154,255),INK)
        a.poly([(260,340),(875,340),(875,510),(260,510)],(190,229,235,255),INK)
        for i,c in enumerate((GOLD,CYAN,CORAL,BLUE)):
            x=290+i*140;a.rect((x,360,x+110,470),(29,67,103,255),WHITE,r=12);a.ellipse((x+35,390,x+75,430),c)
        a.text((500,170),'FOUR ROOMS',45,WHITE)
    elif scene in ('cliff','coil','rings'):
        a.poly([(40,470),(40,270),(375,270),(405,470)],(117,99,121,255),INK)
        a.poly([(600,470),(635,270),(960,270),(960,470)],(79,105,142,255),INK)
        coil(a,170,280,.85);coil(a,650,280,.62,(255,181,110,255))
        for i in range(3):a.ellipse((390-i*18,180-i*25,590+i*18,400+i*25),None,(104,240,255,190-i*35),8)
        a.text((495,495),'THE GAP',30,WHITE)
    elif scene in ('pipe','turnstile'):
        a.line([(70,360),(910,360)],(50,122,149,255),120);a.line([(70,360),(910,360)],(137,223,232,255),78)
        for i,x in enumerate((160,330,600,750)):
            a.ellipse((x,326,x+70,396),GOLD if i%2==0 else CORAL,INK,4);a.ellipse((x+20,345,x+28,353),INK);a.ellipse((x+44,345,x+52,353),INK)
        if scene=='turnstile':
            a.rect((450,235,505,480),(223,239,245,255),INK,r=12)
            a.ellipse((565,190,630,255),(76,238,155,255));a.text((596,222),'✓',35,INK)
            a.ellipse((352,190,417,255),CORAL);a.text((384,222),'×',45,WHITE)
    elif scene in ('diamond','traffic'):
        # A thick, isometric diamond roadway with a shared output.
        a.line([(95,350),(270,350),(500,180),(735,350),(905,350)],(249,105,93,255),64)
        a.line([(95,350),(270,350),(500,520),(735,350),(905,350)],(70,167,255,255),64)
        for pts in [[(95,350),(270,350),(500,180),(735,350),(905,350)],[(95,350),(270,350),(500,520),(735,350),(905,350)]]:a.line(pts,WHITE,5)
        for x,y in [(300,300),(485,173),(680,295),(315,405),(495,513),(682,405)]:a.ellipse((x-18,y-18,x+18,y+18),GOLD,INK,3)
        phone(a,830,255,.65)
    else:
        # Water tower, waves, valve, river and charging phone.
        a.line([(315,390),(260,540)],(221,238,246,255),18);a.line([(480,390),(525,540)],(221,238,246,255),18)
        a.rect((270,170,520,405),(52,123,175,255),WHITE,r=28,width=8)
        a.rect((285,270,505,388),(72,221,237,255),r=15)
        a.poly([(255,170),(395,100),(535,170)],(225,241,246,255),INK)
        a.line([(400,406),(400,465),(695,465)],CYAN,35);a.ellipse((375,425,425,475),GOLD,INK,5)
        phone(a,700,240,1.1)
        if scene in ('battery','celebrate'):
            a.text((770,205),'100%',50,GOLD)
            for i in range(26):
                x=120+(i*137)%780;y=90+(i*91)%460
                a.poly([(x,y),(x+12,y+4),(x+8,y+20),(x-4,y+16)],(GOLD,CORAL,CYAN)[i%3])
    return im.convert('RGB')

def host_sprite(pose,mouth=0,blink=False):
    """Draw Dr. Volt as a small antialiased, transparent animated cel."""
    im=Image.new('RGBA',(440,560));d=ImageDraw.Draw(im,'RGBA')
    # Coat silhouette and lapels
    d.ellipse((73,184,371,553),fill=(9,31,57,80))
    d.polygon([(135,299),(90,332),(54,531),(382,531),(349,332),(303,299)],fill=(238,250,251),outline=INK,width=7)
    d.polygon([(139,300),(220,385),(302,300),(278,442),(220,473),(161,442)],fill=(54,205,221),outline=INK,width=5)
    d.polygon([(136,301),(216,369),(175,410),(119,342)],fill=WHITE,outline=INK,width=4)
    d.polygon([(305,301),(224,369),(263,410),(323,342)],fill=WHITE,outline=INK,width=4)
    d.ellipse((264,407,313,456),fill=(24,80,112),outline=CYAN,width=3)
    d.polygon([(291,413),(278,434),(289,434),(283,451),(303,428),(293,428)],fill=GOLD)
    # Face, ears, facial highlights and electric-cyan hair.
    d.ellipse((88,138,145,204),fill=(225,157,113),outline=INK,width=5);d.ellipse((294,138,351,204),fill=(225,157,113),outline=INK,width=5)
    d.rounded_rectangle((112,57,326,308),radius=92,fill=(237,175,129),outline=INK,width=7)
    d.ellipse((132,72,235,131),fill=(255,220,184,78))
    d.arc((124,68,315,301),95,170,fill=(184,111,86,105),width=10)
    d.ellipse((128,169,160,201),fill=(255,192,151,100));d.ellipse((278,169,308,201),fill=(255,192,151,100))
    d.polygon([(108,138),(78,95),(127,102),(109,40),(159,63),(174,9),(207,55),(244,4),(260,59),(310,25),(303,85),(352,71),(324,133),(291,100),(151,104)],fill=(32,217,236),outline=INK,width=6)
    d.line([(131,75),(166,82),(181,38)],fill=(160,253,255),width=6)
    # Visor, expressive eyes and brows.
    d.rounded_rectangle((117,127,322,202),radius=29,fill=(19,69,97),outline=(126,238,250),width=6)
    d.line([(143,123),(177,115)],fill=INK,width=8);d.line([(260,115),(295,123)],fill=INK,width=8)
    if blink:
        d.line([(145,165),(184,165)],fill=WHITE,width=7);d.line([(253,165),(292,165)],fill=WHITE,width=7)
    else:
        for x in (147,255):
            d.ellipse((x,143,x+39,187),fill=WHITE);d.ellipse((x+16,152,x+31,176),fill=(14,43,65));d.ellipse((x+20,155,x+25,160),fill=WHITE)
    if mouth:
        d.ellipse((190,228,248,228+8+mouth*7),fill=(63,24,38),outline=INK,width=3)
        if mouth>=2:d.ellipse((206,239+mouth*3,233,246+mouth*4),fill=(244,119,121))
    else:d.arc((190,220,250,253),10,170,fill=INK,width=5)
    # Articulated arms change pose, with generous rounded hands.
    gestures=[((106,364),(55,304)),((108,355),(48,226)),((104,364),(54,410)),((333,362),(395,275)),((330,361),(397,355)),((333,361),(399,317)),((330,360),(393,413)),((332,358),(390,250))]
    elbow,hand=gestures[pose]; shoulder=(125,335) if elbow[0]<220 else (314,335)
    d.line([shoulder,elbow,hand],fill=INK,width=39,joint='curve');d.line([shoulder,elbow,hand],fill=(238,250,251),width=29,joint='curve')
    x,y=hand;d.ellipse((x-22,y-21,x+22,y+21),fill=(237,175,129),outline=INK,width=4)
    if pose in (3,7):d.line([(x,y-10),(x+5,y-48)],fill=INK,width=13);d.line([(x,y-10),(x+5,y-48)],fill=(237,175,129),width=8)
    return im


def probe_duration(path):
    return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(path)]))

async def narrate(indices,out):
    import edge_tts
    sem=asyncio.Semaphore(3)
    async def one(i):
        async with sem:
            path=out/f'voice_{i:02d}.mp3'
            await edge_tts.Communicate(SCRIPT[i],'en-US-ChristopherNeural').save(str(path))
            return path
    return await asyncio.gather(*(one(i) for i in indices))

def extract_rms(wav):
    with wave.open(str(wav),'rb') as f:
        assert f.getframerate()==16000 and f.getnchannels()==1 and f.getsampwidth()==2
        samples=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').astype(np.float32)/32768
    return np.array([np.sqrt(np.mean(samples[(n*16000)//30:((n+1)*16000)//30]**2)) for n in range(math.ceil(len(samples)*30/16000))])

def align_exact(script,whisper_words):
    """Use Whisper timings but restore every exact source token, including punctuation.

    Matched tokens keep their real word timing. Missing/hallucinated words are
    interpolated between neighboring matches; captions are never silently omitted.
    """
    import difflib,re
    from subtitle_engine import Word
    tokens=script.split(); normalize=lambda s:re.sub(r'[^a-z0-9]', '',s.lower())
    a=[normalize(t) for t in tokens];b=[normalize(w.text) for w in whisper_words]
    matcher=difflib.SequenceMatcher(a=a,b=b,autojunk=False)
    result=[None]*len(tokens)
    for op,i,j,k,l in matcher.get_opcodes():
        if op=='equal':
            for ai,bi in zip(range(i,j),range(k,l)): result[ai]=Word(tokens[ai],whisper_words[bi].start,whisper_words[bi].end)
        elif i<j:
            start=whisper_words[k-1].end if k else 0.0
            end=whisper_words[l].start if l<len(b) else whisper_words[-1].end
            end=max(end,start+.01*(j-i)); step=(end-start)/(j-i)
            for n in range(i,j):result[n]=Word(tokens[n],start+(n-i)*step,start+(n-i+1)*step)
    return result


def render_shot(task):
    """FFmpeg composites camera movement with 30fps audio-reactive character."""
    index,scene,variant,portrait,start,length,rms,tmp,ass=task
    w,h=(1080,1920) if portrait else (1920,1080)
    base=tmp/f'bg_{index:03}.png';dest=tmp/f'shot_{index:03}.mp4'
    scene_art(scene,variant,portrait).save(base,optimize=False)
    pose=POSE_FOR[scene]; sprites={(m,b):host_sprite(pose,m,b).tobytes() for m in range(5) for b in (False,True)}
    # Host is independently arranged in each aspect ratio; captions remain clear.
    hw,hh=(432,550) if portrait else (385,490)
    hx,hy=((('45','1120') if variant%2==0 else ('W-w-45','1120')) if portrait else (('80','H-h-105') if variant%2==0 else ('W-w-70','H-h-105')))
    # The mouth coordinates in the image stream change every frame. Camera
    # motion and host bob are continuous and do not depend on subtitles.
    z="1.025+0.014*sin(on/100)"
    # Glowing energy packets travel across the illustration independently of
    # the camera and mouth. On the diamond, one takes each colored bridge.
    orb=Image.new('RGBA',(88,88));od=ImageDraw.Draw(orb)
    for rr,alpha in [(42,12),(34,22),(27,48),(20,110),(12,255)]:
        od.ellipse((44-rr,44-rr,44+rr,44+rr),fill=(255,226,100,alpha))
    orb_path=tmp/f'orb_{index:03}.png';orb.save(orb_path)
    bx,by,bw,bh=layout_box(portrait,variant)
    # Coordinates follow the native portrait layout, not a cropped landscape.
    x0=bx+bw*.10;x1=bx+bw*.88;cy=by+bh*.50
    amp=bh*.24 if scene in ('diamond','traffic') else bh*.035
    speed=0.28 if scene in ('diamond','traffic') else .38
    flow=f'mod(t*{speed},1)'
    xexpr=f'{x0:.1f}+{x1-x0:.1f}*{flow}'
    yexpr=f'{cy:.1f}-{amp:.1f}*sin(PI*{flow})'
    xexpr2=f'{x0:.1f}+{x1-x0:.1f}*mod(t*{speed}+0.5,1)'
    yexpr2=f'{cy:.1f}+{amp:.1f}*sin(PI*mod(t*{speed}+0.5,1))'
    # A separate mechanical layer gives the diode a swinging gate and the
    # reservoir a moving waterline rather than implying action by camera alone.
    action=Image.new('RGBA',(300,300));ad=ImageDraw.Draw(action,'RGBA')
    if scene=='turnstile':
        for endpoint in ((150,32),(48,208),(252,208)):
            ad.line((150,150,*endpoint),fill=(240,252,255,255),width=26)
            ad.ellipse((endpoint[0]-13,endpoint[1]-13,endpoint[0]+13,endpoint[1]+13),fill=(240,252,255,255))
        ad.ellipse((124,124,176,176),fill=(255,212,78,255),outline=(17,28,58,255),width=5)
        aw=int(bw*.20);ah=aw
        ax=bx+bw*.475;ay=by+bh*.50
        action_filter=f"[3:v]scale={aw}:{ah},rotate=angle='0.9*sin(t*2.2)':ow=rotw(iw):oh=roth(ih):c=none[act];[b2][act]overlay=x='{ax:.1f}-w/2':y='{ay:.1f}-h/2':shortest=1[animated];"
    elif scene in ('tower','battery','celebrate'):
        ad.rounded_rectangle((15,118,285,165),radius=20,fill=(116,244,253,220))
        ad.line([(25,128),(70,121),(110,133),(150,121),(190,133),(230,121),(275,129)],fill=(242,255,255,230),width=8)
        aw=int(bw*.21);ah=int(bh*.20)
        ax=bx+bw*.29;ay=by+bh*.37
        action_filter=f"[3:v]scale={aw}:{ah}[act];[b2][act]overlay=x='{ax:.1f}':y='{ay:.1f}+{bh*.045:.1f}*sin(t*1.4)':shortest=1[animated];"
    else:
        action_filter='[b2]null[animated];'
    action_path=tmp/f'action_{index:03}.png';action.save(action_path)
    filt=(f'[0:v]scale={w}:{h},zoompan=z=\'{z}\':x=\'iw/2-iw/zoom/2+12*sin(on/75)\':'
          f'y=\'ih/2-ih/zoom/2+8*cos(on/80)\':d=1:s={w}x{h}:fps=30[bg];'
          f'[2:v]split=2[o1][o2];[bg][o1]overlay=x=\'{xexpr}\':y=\'{yexpr}\':shortest=1[b1];'
          f'[b1][o2]overlay=x=\'{xexpr2}\':y=\'{yexpr2}\':shortest=1[b2];'
          +action_filter+f'[1:v]scale={hw}:{hh}[host];[animated][host]overlay=x=\'{hx}\':y=\'{hy}+7*sin(t*2.1)\':shortest=1,ass={ass}[v]')
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-filter_complex_threads','1','-loop','1','-framerate','30','-i',str(base),
         '-f','rawvideo','-pixel_format','rgba','-video_size','440x560','-framerate','30','-i','pipe:0',
         '-loop','1','-framerate','30','-i',str(orb_path),
         '-loop','1','-framerate','30','-i',str(action_path),
         '-filter_complex',filt,'-map','[v]','-t',f'{length:.6f}','-r','30','-an','-c:v','libx264','-threads','2','-preset','veryfast','-crf','18','-pix_fmt','yuv420p',str(dest)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for f in range(math.ceil(length*30)):
            i=min(len(rms)-1,max(0,int((start+f/30)*30)))
            level=float(rms[i]); m=min(4,int(level*35)) if level>.012 else 0
            blink=((start+f/30+variant*.3)%3.6)<.13
            proc.stdin.write(sprites[m,blink])
        proc.stdin.close()
        if proc.wait()!=0:raise RuntimeError(f'ffmpeg shot {index} failed')
    except BaseException:
        proc.kill();proc.wait();raise
    return dest


def write_shifted_ass(path,groups,start,end,portrait):
    from subtitle_engine import Word,write_ass
    shifted=[]
    for group in groups:
        # Keep a full line even where shot boundaries cut through a phrase.
        if group[-1].end<start or group[0].start>=end:continue
        shifted.append([Word(w.text,max(0,w.start-start),max(.01,w.end-start)) for w in group])
    write_ass(path,shifted,portrait)


def build(name,outdir,model_name='base.en',workers=2):
    import subtitle_engine as subtitles
    from faster_whisper import WhisperModel
    from audio_design import generate
    portrait=name!=FULL;indices=SHORTS[name] if portrait else list(range(len(SCRIPT)))
    outdir=Path(outdir).resolve();outdir.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='volt-') as td:
        tmp=Path(td);voice=asyncio.run(narrate(indices,tmp))
        # Decode each block to canonical PCM; concatenate exactly in script order.
        wavs=[];offsets=[];offset=0.
        for index,mp3 in zip(indices,voice):
            wav=tmp/f'voice_{index:02d}.wav';run('ffmpeg','-v','error','-y','-i',mp3,'-ac','1','-ar','16000','-c:a','pcm_s16le',wav)
            with wave.open(str(wav),'rb') as f: duration=f.getnframes()/f.getframerate()
            offsets.append((index,offset,duration));offset+=duration;wavs.append(wav)
        narration=tmp/'narration.wav'
        with wave.open(str(narration),'wb') as dst:
            dst.setparams((1,2,16000,0,'NONE','not compressed'))
            for wav in wavs:
                with wave.open(str(wav),'rb') as src:dst.writeframes(src.readframes(src.getnframes()))
        rms=extract_rms(narration)
        model=WhisperModel(model_name,device='cpu',compute_type='int8',cpu_threads=max(1,workers))
        segments,_=model.transcribe(str(narration),language='en',word_timestamps=True,vad_filter=False,beam_size=5)
        detected=subtitles.collect_words(segments)
        exact=align_exact(' '.join(SCRIPT[i] for i in indices),detected)
        groups=subtitles.group_words(exact,portrait)
        subtitles.write_srt(outdir/(name+'.srt'),groups);subtitles.write_ass(outdir/(name+'.ass'),groups,portrait)
        tasks=[];shot=0
        for block,start,dur in offsets:
            count=max(1,math.ceil(dur/7.5));shot_duration=dur/count
            for n in range(count):
                scene=BLOCK_SCENES[block][min(len(BLOCK_SCENES[block])-1,int(n*len(BLOCK_SCENES[block])/count))]
                t=round((start+n*shot_duration)*30)/30
                end=round((start+(n+1)*shot_duration)*30)/30
                ass=tmp/f'caption_{shot:03}.ass'
                write_shifted_ass(ass,groups,t,end,portrait)
                tasks.append((shot,scene,shot,portrait,t,end-t,rms,tmp,ass));shot+=1
        print(f'{name}: {offset:.1f}s, {len(tasks)} shots, {len(exact)} exact words',flush=True)
        with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as pool:
            paths=list(pool.map(render_shot,tasks))
        listing=tmp/'concat.txt';listing.write_text(''.join(f"file '{p}'\n" for p in paths))
        generate(tmp/'sounds');dest=outdir/(name+'.mp4')
        # Audio remains continuous across shots. Music bed is deliberately quiet.
        run('ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',listing,'-i',narration,'-stream_loop','-1','-i',tmp/'sounds/ambient.wav',
            '-filter_complex','[2:a]volume=0.08[bed];[1:a][bed]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]',
            '-map','0:v:0','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart','-shortest',dest)
        print('Created',dest,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--video',choices=[FULL,*SHORTS],required=True);p.add_argument('--output',default='output/ep01_phone_charger');p.add_argument('--model',default='base.en');p.add_argument('--workers',type=int,default=2)
    a=p.parse_args();build(a.video,a.output,a.model,a.workers)
