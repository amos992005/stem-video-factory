"""Native stickman animation and cached Twemoji/Iconify SVG scene graph.

Icons are parsed once as Skia SVG DOMs and drawn as vector paths every frame.
All round/oval primitive drawing below belongs to the stickman, particle VFX,
or the background, never to a phone, plug, glass, valve, magnet or other prop.
AC oscillation is represented symbolically: 60 Hz cannot be sampled at 30 fps.
"""
from __future__ import annotations
import math
from pathlib import Path
import skia

FPS=30;W=540;H=960
ROOT=Path(__file__).resolve().parents[1]/'assets'/'vector_props'
ICONS=('phone','battery','plug','explosion','faucet','glass','truck','droplet','sunglasses','magnet','cyclone',
       'mdi-heating-coil','mdi-valve-open','mdi-valve-closed','mdi-power-plug','mdi-sine-wave','mdi-current-ac',
       'mdi-current-dc','mdi-arrow-right','mdi-pipe-valve','mdi-power-plug-battery')
PALETTES=(('#101937','#293263'),('#111935','#133d55'),('#261832','#493555'),('#0a2734','#165354'),
          ('#151a3e','#204157'),('#241633','#403253'),('#102940','#195351'))
TITLES=('A DANGEROUS SHORTCUT','THE AIR GAP','WALL POWER','A GENTLE CURRENT','01  TRANSFORMER','02  DIODE','03  CAPACITOR')


def color(value,alpha=255):
    value=value.lstrip('#');value=''.join(c*2 for c in value) if len(value)==3 else value
    return skia.ColorSetARGB(max(0,min(255,int(alpha))),int(value[0:2],16),int(value[2:4],16),int(value[4:6],16))

def fill(value,alpha=255):return skia.Paint(Color=color(value,alpha),AntiAlias=True)
def stroke(value,width=3,alpha=255):
    return skia.Paint(Color=color(value,alpha),AntiAlias=True,Style=skia.Paint.kStroke_Style,
                      StrokeWidth=width,StrokeCap=skia.Paint.kRound_Cap,StrokeJoin=skia.Paint.kRound_Join)

def path(points,close=False):
    p=skia.Path();p.moveTo(*points[0])
    for pt in points[1:]:p.lineTo(*pt)
    if close:p.close()
    return p

def curve(a,b,c,d):
    p=skia.Path();p.moveTo(*a);p.cubicTo(*b,*c,*d);return p

def spring_series(targets,k=48,c=12):
    """Integrate damped spring x''=-k(x-target)-c*x' at 30 fps."""
    x=float(targets[0]);v=0.;out=[]
    for target in targets:
        for _ in range(4):
            dt=1/(FPS*4);v+=(-k*(x-target)-c*v)*dt;x+=v*dt
        out.append(x)
    return out

def beat_boundaries(frames,max_frames=45):
    n=max(1,math.ceil(frames/max_frames))
    # Integer frame partitions keep each visual beat to at most 1.5 seconds.
    return [round(i*frames/n) for i in range(n+1)]

def frame_plan(timeline,rms):
    """One rig and camera plan, with spring state continuous across scene cuts."""
    # [left shoulder, right shoulder, left elbow, right elbow, left knee, right knee]
    aposes=[(-52,70,-36,24),(-92,56,42,-65),(-25,95,-48,35),(-78,40,36,-45),
            (-28,90,-44,30),(-90,50,52,-28),(-68,75,-30,35)]
    targets=[[] for _ in range(10)];records=[]
    for beat in timeline:
        i=beat['index'];bounds=beat_boundaries(beat['frames']);n=len(bounds)-1
        for local in range(beat['frames']):
            t=local/FPS;cut=min(n-1,next((j for j in range(n) if local<bounds[j+1]),n-1))
            cut_frame=local-bounds[cut];step=cut%2;scene_phase=local/max(1,beat['frames']-1)
            l,r,le,re=aposes[i];walk=math.sin(t*4.4)
            # Gesture goals change at every 1.5–2 second visual beat.
            variants=(l+step*34+8*math.sin(t*2),r-step*42+10*math.cos(t*2.3),
                      le+step*22,re-step*25,18*walk,-18*walk,
                      (-18 if step==0 else 24),(-9 if step==0 else 9),
                      (1.0 if step==0 else 1.17),
                      (142 if (i+step)%2==0 else 398))
            for dest,val in zip(targets,variants):dest.append(val)
            prev=(i-1,timeline[i-1]['duration']) if i>0 and local<10 else None
            records.append((i,t,beat['duration'],scene_phase,cut,cut_frame,prev))
    arrays=[spring_series(x,55 if j<6 else 38,13 if j<6 else 12) for j,x in enumerate(targets)]
    for i,rec in enumerate(records):
        yield (*rec,float(rms[min(i,len(rms)-1)]),*(arr[i] for arr in arrays))

class Studio:
    """Per-process canvas and decoded native-vector icon cache."""
    def __init__(self,width=1080,height=1920):
        self.width=width;self.height=height;self.surface=skia.Surface(width,height)
        self.icons={}
        for name in ICONS:
            p=ROOT/(name+'.svg')
            if not p.is_file():raise FileNotFoundError(f'Missing cached vector icon: {p}')
            # Skia's SVG parser rejects xml:space on Twemoji's battery; it
            # has no visual effect for path-only artwork. Keep source untouched.
            data=p.read_bytes().replace(b' xml:space="preserve"',b'')
            dom=skia.SVGDOM.MakeFromStream(skia.MemoryStream(data))
            if dom is None:raise ValueError(f'Invalid SVG icon {p}')
            dom.setContainerSize(skia.Size(100,100));self.icons[name]=dom
        font='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
        self.typeface=skia.Typeface.MakeFromFile(font) if Path(font).exists() else skia.Typeface.MakeDefault()

    def text(self,c,s,x,y,size=22,col='#efffff',align='left',alpha=255):
        font=skia.Font(self.typeface,size);font.setEdging(skia.Font.kAntiAlias)
        if align=='center':x-=font.measureText(s)/2
        elif align=='right':x-=font.measureText(s)
        c.drawString(s,x,y,font,fill(col,alpha))

    def icon(self,c,name,x,y,size,angle=0,opacity=255):
        c.save();c.translate(x,y);c.rotate(angle);c.scale(size/100,size/100);c.translate(-50,-50)
        if opacity<255:c.saveLayerAlpha(None,int(opacity))
        self.icons[name].render(c)
        if opacity<255:c.restore()
        c.restore()

    def beam(self,c,p,col='#79fff0',width=4):
        c.drawPath(p,stroke(col,width*4,35));c.drawPath(p,stroke(col,width*2,65));c.drawPath(p,stroke(col,width,240))

    def background(self,c,scene,t):
        a,b=PALETTES[scene]
        paint=skia.Paint(AntiAlias=True)
        paint.setShader(skia.GradientShader.MakeLinear([(0,0),(W,H)],[color(a),color(b)],None,skia.TileMode.kClamp))
        c.drawRect(skia.Rect.MakeWH(W,H),paint)
        # Parallax marks are environmental VFX, not prop geometry.
        for i in range(14):
            x=(i*83+16+3*t*(i%3+1))%W;y=(i*157+50-t*(i%4+3))%H
            c.drawCircle(x,y,1+(i%3)*.35,fill('#87d9ff',45))

    def mascot(self,c,x,y,t,kind='hot',scale=1):
        c.save();c.translate(x,y);c.scale(scale,scale)
        cyan=kind=='steady';col='#47ffdc' if cyan else '#ff515c';glow='#b5fff1' if cyan else '#ffd081'
        # An expressive skeletal character, not an icon or drawn prop.
        bob=3*math.sin(t*5 if not cyan else t*2)
        c.translate(0,bob)
        if not cyan:
            c.drawPath(path([(0,-49),(10,-28),(27,-36),(22,-14),(34,-5),(20,7),(25,25),(9,20),(-2,41),(-8,21),(-27,26),(-21,6),(-32,-5),(-19,-14),(-24,-34),(-9,-25)],True),fill(col))
            c.drawCircle(-9,-8,4,fill('#fff6ca'));c.drawCircle(10,-8,4,fill('#fff6ca'))
            c.drawCircle(-8,-8,2,fill('#582c40'));c.drawCircle(11,-8,2,fill('#582c40'))
        else:
            c.drawCircle(0,-20,20,fill(col));self.icon(c,'sunglasses',0,-21,36)
        for arm in (-1,1):
            p=curve((arm*13,0),(arm*23,5),(arm*27,16),(arm*33,13+5*math.sin(t*4+arm)))
            c.drawPath(p,stroke(glow,5));
            c.drawPath(curve((arm*7,20),(arm*10,30),(arm*13,40),(arm*20,43)),stroke(col,5))
        c.restore()

    def host(self,c,x,y,t,amp,angles,focus,scene,cut):
        l,r,le,re,lk,rk=angles
        # Jump and recoil respond to scene energy; limbs are true chained joints.
        jump=(max(0,math.sin(t*3.3))**4)*16 if scene in (0,2) else 3*math.sin(t*2.6)
        headnod=amp*5*math.sin(t*11)+3*math.sin(t*2.5)
        c.save();c.translate(x,y-jump)
        white='#efffff';cyan='#75f8ff';glow='#5beeff'
        body=curve((0,-106),(-8,-79),(7,-52),(0,-20))
        c.drawPath(body,stroke(glow,17,32));c.drawPath(body,stroke(white,8))
        def endpoint(p,length,ang):
            a=math.radians(ang);return (p[0]+length*math.sin(a),p[1]+length*math.cos(a))
        def bone(start,a1,a2,length1,length2):
            joint=endpoint(start,length1,a1);end=endpoint(joint,length2,a1+a2)
            bend=((start[0]+joint[0])/2+4,(start[1]+joint[1])/2)
            c.drawPath(curve(start,bend,bend,joint),stroke(white,8))
            mid=((joint[0]+end[0])/2,(joint[1]+end[1])/2-3)
            c.drawPath(curve(joint,mid,mid,end),stroke(white,7))
            c.drawCircle(*joint,4,fill(cyan));c.drawCircle(*end,4.2,fill(white))
        bone((-5,-92),l,le,53,49);bone((5,-92),r,re,53,49)
        bone((-5,-20),-15+lk,lk*.6,55,54);bone((5,-20),15+rk,rk*.6,55,54)
        # White/cyan glowing head with subtle brows; no mouth, nose or clothes.
        c.drawCircle(0,-143+headnod,42,fill(glow,35));c.drawCircle(0,-143+headnod,34,fill('#eeffff'))
        c.save();c.translate(0,headnod)
        c.drawPath(path([(-32,-156),(-30,-187),(-18,-180),(-13,-199),(-2,-183),(12,-201),(15,-182),(29,-187),(33,-156),(22,-165),(-23,-165)],True),fill('#00e8f7'))
        blink=abs(math.sin(math.pi*(t+scene*.43)/2.8))<.06
        px=max(-4,min(4,(focus[0]-x)/40));py=max(-3,min(3,(focus[1]-(y-143))/55))
        for sx in (-13,13):
            if blink:c.drawLine(sx-7,-143,sx+7,-143,stroke('#223b59',3))
            else:
                c.drawOval(skia.Rect.MakeXYWH(sx-7,-153,14,19),fill('#183c5a'))
                c.drawCircle(sx+px*.4,-144+py*.4,3,fill('#fff'))
            brow=-164-(5 if (scene==0 and cut>0) else 0)
            c.drawPath(curve((sx-7,brow+1),(sx-3,brow-2),(sx+3,brow-2),(sx+7,brow+1)),stroke('#2b5970',2.5))
        c.restore();c.restore()

    def art(self,c,scene,t,duration,phase,cut):
        u=max(0,min(1,phase));wave=math.sin(t*3);sec=cut%2
        if scene==0:
            self.icon(c,'phone',358 if not sec else 356,342 if not sec else 315,245 if not sec else 290,-6+wave*2)
            self.icon(c,'plug',195+min(t*25,60),330,140,38+wave*3)
            self.beam(c,curve((105,475),(150,435),(165,360),(230,360)),'#ff7055',5)
            self.mascot(c,260+26*math.sin(t*5),340,t,'hot',.65)
            if sec or u>.6:self.icon(c,'explosion',351,350,185+24*math.sin(t*8))
            self.text(c,'DO NOT CONNECT',270,173,21,'#ffd0ae','center')
        elif scene==1:
            if not sec:self.icon(c,'mdi-power-plug-battery',290,335,255,-5+wave*2)
            else:self.icon(c,'magnet',280,325,195,90+5*wave)
            for x in (174,393):self.icon(c,'mdi-heating-coil',x,380,120 if x==174 else 90,90)
            for i in range(3):
                x=230+(t*60+i*32)%100;c.drawOval(skia.Rect.MakeXYWH(x-10,322,20,111),stroke('#84fbff',2,175))
            self.text(c,'AIR GAP',270,225,22,'#9bfaff','center')
        elif scene==2:
            self.icon(c,'truck',180 if not sec else 145,336,190,-4+3*wave)
            self.mascot(c,180,270,t,'hot',.65)
            self.icon(c,'glass',390,450,175,4*math.sin(t*3) if sec else 0)
            for j in range(5):
                x=260+(j*42+t*48)%190;y=355+24*math.sin(t*5-j*.8)
                self.icon(c,'droplet',x,y,32+j*2,90)
            self.text(c,'60 CYCLES / SECOND',270,190,19,'#ffe2a1','center')
        elif scene==3:
            self.icon(c,'faucet',220 if not sec else 185,305,200,-3*wave)
            self.icon(c,'glass',332,460,190)
            for i in range(4):self.icon(c,'droplet',300,355+(t*90+i*30)%100,25)
            self.mascot(c,305,405,t,'steady',.55)
            if sec:self.icon(c,'battery',433,325,122,4*wave)
            self.text(c,'ONE WAY  •  LOW VOLTAGE',270,185,18,'#9fffe6','center')
        elif scene==4:
            self.icon(c,'mdi-heating-coil',160 if not sec else 137,360,190,90)
            self.icon(c,'mdi-heating-coil',407 if not sec else 417,360,135,90)
            for i in range(5):
                x=230+(t*85+i*26)%95;c.drawOval(skia.Rect.MakeXYWH(x-12,300,24,125),stroke('#63f5ff',3,180))
            self.icon(c,'magnet',270,475,100,20*math.sin(t*2))
            self.text(c,'ENERGY CROSSES THE GAP',270,190,18,'#b5faff','center')
        elif scene==5:
            opened=math.sin(t*2.3)>0;self.icon(c,'mdi-valve-open' if opened else 'mdi-valve-closed',300,357,260,0)
            self.mascot(c,150+35*math.sin(t*2.3),354,t,'hot',.85)
            self.icon(c,'mdi-arrow-right',440,350,80)
            self.text(c,'OPEN' if opened else 'BLOCKED!',320,200,25,'#a7ffdd' if opened else '#ff9a9d','center')
        else:
            self.icon(c,'battery',220 if not sec else 165,335,220,-6+wave*3)
            self.icon(c,'phone',385,365,210,5-wave*2)
            self.beam(c,curve((280,390),(320,380),(350,395),(410,385)),'#78ffe0',5)
            self.mascot(c,302+30*math.sin(t),405,t,'steady',.6)
            self.text(c,'5V DC  •  SMOOTH & STEADY',270,190,19,'#b9fff0','center')

    def frame(self,plan):
        scene,t,dur,phase,cut,cut_frame,prev,amp,l,r,le,re,lk,rk,camx,camy,zoom,hostx=plan
        c=self.surface.getCanvas();c.clear(skia.ColorBLACK);c.save();c.scale(self.width/W,self.height/H)
        self.background(c,scene,t)
        # Artwork shifts between zones on scene change; camera offset/zoom are
        # spring-integrated and also change on every <=1.5s visual beat.
        c.save();c.translate(270+camx,380+camy);c.scale(zoom,zoom);c.translate(-270,-380)
        if prev and t<.3:
            q=1-math.exp(-10*t)*(1+10*t);q=max(0,min(1,q));old,old_dur=prev
            c.save();c.translate(-540*q,0);self.art(c,old,old_dur,old_dur,1,1);c.restore()
            c.save();c.translate(540*(1-q),0);self.art(c,scene,t,dur,phase,cut);c.restore()
        else:self.art(c,scene,t,dur,phase,cut)
        c.restore()
        # Text is scene-specific, not part of any prop drawing.
        self.text(c,TITLES[scene],270,98,25,'#e8fbff','center')
        self.host(c,hostx,715,t,amp,(l,r,le,re,lk,rk),(300,350),scene,cut)
        if scene==6:
            self.text(c,'Twemoji © Twitter & contributors · CC BY 4.0',270,927,9,'#b7d9e7','center',200)
            self.text(c,'Material Design Icons / Pictogrammers · Apache 2.0',270,943,9,'#b7d9e7','center',200)
        c.restore();return self.surface.makeImageSnapshot().tobytes()
