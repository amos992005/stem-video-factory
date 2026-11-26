"""Original SVG vector scenes: hierarchical host rig, animated props and camera.

All shapes are SVG paths, gradients and strokes; no raster artwork or external
image generation. 30fps cannot depict a literal 60Hz oscillation (Nyquist), so
Sparky's fast alternating motion is a deliberately visible *symbolic* cycle.
"""
from __future__ import annotations
import math, html
import numpy as np

W,H,FPS=540,960,30
DEFS='''<defs>
<linearGradient id="bg" x2="1" y2="1"><stop stop-color="#0B1026"/><stop offset=".52" stop-color="#151E3F"/><stop offset="1" stop-color="#090D1E"/></linearGradient>
<linearGradient id="hair" x2=".8" y2="1"><stop stop-color="#83ffff"/><stop offset=".35" stop-color="#00F2FE"/><stop offset="1" stop-color="#0072FF"/></linearGradient>
<linearGradient id="skin" x2="1" y2=".9"><stop stop-color="#ffe0ba"/><stop offset=".55" stop-color="#f5b98f"/><stop offset="1" stop-color="#df8a73"/></linearGradient>
<linearGradient id="coat" x2="1" y2="1"><stop stop-color="#ffffff"/><stop offset=".5" stop-color="#e4f4ff"/><stop offset="1" stop-color="#a6c6e3"/></linearGradient>
<linearGradient id="aqua" x2="1" y2="1"><stop stop-color="#00F5A0"/><stop offset=".5" stop-color="#25f3db"/><stop offset="1" stop-color="#00a8f5"/></linearGradient>
<linearGradient id="hot" x2="1" y2="1"><stop stop-color="#ff477e"/><stop offset=".55" stop-color="#ff5c42"/><stop offset="1" stop-color="#ffb629"/></linearGradient>
<linearGradient id="copper" x2="1" y2="0"><stop stop-color="#8a3b32"/><stop offset=".24" stop-color="#ffca72"/><stop offset=".5" stop-color="#d97244"/><stop offset=".78" stop-color="#ffd08a"/><stop offset="1" stop-color="#884331"/></linearGradient>
<linearGradient id="glass" x2="1" y2="1"><stop stop-color="#eaffff" stop-opacity=".75"/><stop offset=".4" stop-color="#5ad8ef" stop-opacity=".12"/><stop offset="1" stop-color="#c4fcff" stop-opacity=".45"/></linearGradient>
<linearGradient id="panel" x2="0" y2="1"><stop stop-color="#344775"/><stop offset="1" stop-color="#192746"/></linearGradient>
<radialGradient id="halo"><stop stop-color="#25e7ff" stop-opacity=".27"/><stop offset="1" stop-color="#25e7ff" stop-opacity="0"/></radialGradient>
<radialGradient id="fire"><stop stop-color="#fff7a5"/><stop offset=".4" stop-color="#ffba44"/><stop offset=".76" stop-color="#ff4a52"/><stop offset="1" stop-color="#fa3464" stop-opacity="0"/></radialGradient>
</defs>'''

def path(d,fill='none',stroke='none',sw=1,extra=''):
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round" {extra}/>'
def text(x,y,s,size=18,color='#e8f9ff',anchor='start',weight=700,extra=''):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-family="DejaVu Sans, sans-serif" font-weight="{weight}" text-anchor="{anchor}" {extra}>{html.escape(str(s))}</text>'
def circ(x,y,r,fill,extra=''):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" {extra}/>'
def rect(x,y,w,h,r,fill,extra=''):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" {extra}/>'
def group(content,transform='',extra=''):
    return f'<g transform="{transform}" {extra}>{content}</g>'
def line(x1,y1,x2,y2,color,width=2,opacity=1):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}" opacity="{opacity}" stroke-linecap="round"/>'
def glowpath(d,color='#58f7ff',width=5):
    return path(d,'none',color,width*4,'opacity=".11"')+path(d,'none',color,width*2,'opacity=".2"')+path(d,'none',color,width)
def label(x,y,s,color='#71f5f5',size=15):
    w=max(55,13*len(s)*size/20+22)
    return rect(x,y,w,29,14,'#142b49','stroke="#3b7893" stroke-width="1"')+text(x+12,y+20,s,size,color)

def spring_angles(targets,frames,k=60,c=13):
    """Integrate theta''=-k(theta-target)-c*theta' at 30fps."""
    x=float(targets[0]);v=0.;out=[]
    for target in targets[:frames]:
        for _ in range(4):
            dt=1/(FPS*4);v+=(-k*(x-target)-c*v)*dt;x+=v*dt
        out.append(x)
    return out

def arm(side,shoulder,elbow):
    # Articulated upper arm and forearm are nested at their actual joints.
    skin=path('M -12 0 Q -21 31 -17 58 Q -12 68 -2 65 L 10 57 Q 8 27 11 0 Z','url(#coat)','#6e93b4',2)
    fore=path('M -10 0 Q -16 29 -10 49 L 8 52 Q 17 35 10 0 Z','url(#coat)','#7898b0',2)
    hand=path('M -9 47 Q -15 61 -8 68 Q 0 73 8 65 L 14 57 Q 17 48 8 46 Z','url(#skin)','#d79176',1)
    nested=skin+group(fore+hand,f'translate(0 59) rotate({elbow:.2f})')
    return group(nested,f'translate({side*49} -12) rotate({shoulder:.2f})')

def host(x,y,scale,t,amp,left,right,scene):
    bob=3*math.sin(t*2.7);tilt=4*math.sin(t*1.6)+( -8*math.exp(-max(t-.8,0)*3) if scene==0 and t>.8 else 0)
    blink=abs(math.sin((t+scene*.17)*math.pi/2.8))<.055
    iris=-3 if scene in (1,3,5,7,8) else 4
    # Visemes derived from frame RMS (the words themselves stay in subtitles).
    if amp<.08:mouth=path('M -8 25 Q 0 32 8 25','none','#8d4650',2.4)
    elif amp<.22:mouth='<ellipse cx="0" cy="28" rx="7" ry="4" fill="#78364d"/>'
    elif amp<.45:mouth='<ellipse cx="0" cy="28" rx="11" ry="7" fill="#78364d"/>'+path('M -6 27 Q 0 29 6 27','none','#fff',2)
    elif amp<.7:mouth='<ellipse cx="0" cy="28" rx="9" ry="10" fill="#78364d"/>'
    else:mouth='<ellipse cx="0" cy="28" rx="8" ry="12" fill="#54263d"/>'
    eyes=(path('M -24 4 q 7 5 14 0 M 10 4 q 7 5 14 0','none','#513b50',3) if blink else
          '<ellipse cx="-17" cy="4" rx="9" ry="11" fill="white"/><ellipse cx="17" cy="4" rx="9" ry="11" fill="white"/>'+circ(-17+iris,5,4,'#173456')+circ(17+iris,5,4,'#173456')+circ(-15+iris,2,1.4,'white')+circ(19+iris,2,1.4,'white'))
    face=('<ellipse cx="0" cy="6" rx="42" ry="49" fill="url(#skin)" stroke="#b9706e" stroke-width="2"/>'
        +path('M -39 -19 L -43 -48 L -28 -43 L -25 -69 L -9 -52 L 6 -77 L 13 -55 L 35 -67 L 31 -43 L 48 -40 L 37 -15 Q 0 -37 -39 -19 Z','url(#hair)','#00aee5',2)
        +path('M -37 -16 Q 0 -27 37 -16','none','#22617a',7)
        +'<ellipse cx="-20" cy="-17" rx="13" ry="10" fill="#19546f" stroke="#82fbff" stroke-width="3"/><ellipse cx="20" cy="-17" rx="13" ry="10" fill="#19546f" stroke="#82fbff" stroke-width="3"/>'
        +line(-7,-17,7,-17,'#9beeff',3)+path('M -26 -9 Q -18 -14 -10 -10 M 10 -10 Q 18 -14 26 -9','none','#774e55',2.5)+eyes+path('M -2 8 Q -5 16 1 17','none','#c37965',1.5)+mouth)
    legs=path('M -33 64 L -36 148 Q -35 158 -16 158 L -8 80 L 8 80 L 16 158 Q 35 158 36 148 L 33 64 Z','#24365f','#12213e',2)
    shoes=path('M -37 148 Q -53 154 -50 163 L -15 163 L -15 151 Z M 15 151 L 15 163 L 50 163 Q 53 154 37 148 Z','#111d39')
    torso=path('M -48 -18 Q -35 -35 -23 -35 L 23 -35 Q 37 -35 48 -18 L 43 78 Q 0 90 -43 78 Z','url(#coat)','#8baec8',2)
    torso+=path('M -20 -35 L 0 -17 L 20 -35 L 17 69 L -17 69 Z','url(#aqua)')+path('M -23 -34 L -42 -19 L -20 10 L -28 19 L -8 51 L -5 -20 Z M 23 -34 L 42 -19 L 20 10 L 28 19 L 8 51 L 5 -20 Z','#f3fbff','#a9c9df',1.5)
    torso+=path('M 20 38 h 13 v 12 h -13 Z','none','#90b8d0',1.5)+circ(-26,20,3,'#12d5e6')
    body=legs+shoes+arm(-1,left,-26+8*math.sin(t*3))+torso+arm(1,right,22+10*math.sin(t*2.4))+group(face,f'translate(0 -70) rotate({tilt:.2f})')
    return group(body,f'translate({x} {y+bob:.1f}) scale({scale})')

def sparky(x,y,t,scale=1):
    angle=4*math.sin(t*16);body=path('M 0 -47 L 13 -25 L 35 -35 L 29 -9 L 49 0 L 27 12 L 34 35 L 10 26 L 0 48 L -12 26 L -37 35 L -29 10 L -48 0 L -28 -10 L -36 -34 L -13 -25 Z','url(#hot)','#ffcf78',2)
    body+=circ(-14,-7,7,'#fff9ce')+circ(14,-7,7,'#fff9ce')+circ(-12,-7,3,'#7d283a')+circ(16,-7,3,'#7d283a')+path('M -12 13 Q 0 22 12 13','none','#7d283a',3)
    body+=glowpath('M -53 -28 l -10 12 l 8 4 l -10 13','#ffad54',2)+glowpath('M 52 10 l 10 -12 l -8 -4 l 10 -11','#ffad54',2)
    return group(body,f'translate({x+5*math.sin(t*11):.1f} {y+4*math.cos(t*9):.1f}) rotate({angle:.1f}) scale({scale})')

def steady(x,y,t,scale=1):
    body=path('M -37 -8 Q -34 -36 0 -40 Q 34 -36 38 -8 L 30 26 Q 0 41 -30 26 Z','url(#aqua)','#aaffea',2)
    body+=path('M -30 -10 Q 0 -14 30 -10 L 25 4 Q 0 10 -25 4 Z','#102e4a')+line(-20,-5,-10,-6,'#9bfff4',2)+line(10,-5,20,-6,'#9bfff4',2)+path('M -11 14 Q 0 20 11 14','none','#087c89',2)
    return group(body,f'translate({x:.1f} {y+3*math.sin(t*2):.1f}) scale({scale})')

def charger(x,y,scale=1):
    s=rect(-105,-130,210,260,34,'url(#coat)','stroke="#b7e1f0" stroke-width="3"')+rect(-82,-100,164,196,20,'#1b3151','stroke="#7ed9e9" stroke-width="2"')
    s+=rect(-60,131,18,37,5,'url(#copper)')+rect(40,131,18,37,5,'url(#copper)')
    for xx in [-54,-18,18,54]:s+=rect(xx-10,-67,21,105,9,'url(#copper)','opacity=".9"')
    s+=glowpath('M -65 63 H 65','#54f4fd',4)
    return group(s,f'translate({x} {y}) scale({scale})')

def coil(x,y,turns,scale=1):
    s=rect(-27,-75,54,150,19,'#344566','stroke="#7d9cb8" stroke-width="2"')
    for i in range(turns):
        yy=-67+i*(134/max(turns-1,1));s+=path(f'M -34 {yy:.1f} C -24 {yy-8:.1f} 24 {yy-8:.1f} 34 {yy:.1f} C 23 {yy+8:.1f} -23 {yy+8:.1f} -34 {yy:.1f}','none','url(#copper)',8)
    return group(s,f'translate({x} {y}) scale({scale})')

def battery(x,y,level=0.6,scale=1):
    s=rect(-68,-115,136,230,20,'#152b4a','stroke="#a9fbff" stroke-width="4"')+rect(-22,-130,44,15,5,'#a9fbff')
    s+=rect(-55,99-194*level,110,194*level,12,'url(#aqua)','opacity=".78"')+path('M -4 -32 L -25 5 L -4 5 L -14 36 L 23 -9 L 3 -9 L 12 -32 Z','#f9ffbe')
    return group(s,f'translate({x} {y}) scale({scale})')

def scene_art(scene,t,duration):
    u=max(0,min(1,t/max(.1,duration)));s='';phase=t*2.8
    if scene==0:
        s+=text(42,115,'THE DIRECT CONNECTION',23,'#a4efff')+label(42,132,'120V AC  →  PHONE','#ffb867',14)
        s+=battery(366,380,.16,1.13)+glowpath('M 125 357 C 185 300 230 430 292 386','#ff6f54',7)
        s+=group(rect(-43,-24,86,48,15,'url(#hot)')+rect(36,-13,26,9,4,'#d9efff')+rect(36,6,26,9,4,'#d9efff'),f'translate(142 355) rotate(-10)')
        s+=sparky(235+20*math.sin(phase*2),365,t,.62)
        if u>.62:
            r=40+110*((u-.62)*2%1);s+=f'<circle cx="365" cy="380" r="{r:.1f}" fill="none" stroke="#ffcc70" stroke-width="5" opacity="{max(0,.7-(r/200)):.2f}"/>'+circ(365,380,100,'url(#fire)')
    elif scene==1:
        s+=text(42,115,'THE AIR GAP',28,'#b0faff')+label(42,132,'0 WIRES CONNECTED?!','#ffd666',13)
        s+=charger(280,374,1.25)+coil(214,354,7,.43)+coil(345,354,4,.43)
        for k in range(3):
            x=245+((t*65+k*34)%88);s+=f'<ellipse cx="{x:.1f}" cy="354" rx="17" ry="47" fill="none" stroke="#6cfaff" stroke-width="3" opacity=".8"/>'
        s+=glowpath('M 248 425 Q 281 402 314 425','#79fbff',3)
    elif scene==2:
        s+=text(42,115,'WALL POWER',28,'#a5f2ff')+label(42,132,'PUSH ↔ PULL   60 Hz','#ffcf72',14)
        s+=group(rect(-84,-31,132,62,22,'url(#hot)')+path('M 48 -25 L 95 -42 L 95 42 L 48 25 Z','#ffb66d','#ffce9a',3),f'translate(140 339) rotate(-12)')
        for k in range(5):
            yy=327+(k-2)*12;s+=glowpath(f'M 224 {yy} C 292 {yy-55*math.sin(phase):.1f} 347 {yy+48*math.sin(phase):.1f} 434 {yy+8:.1f}','#40daff',2.8)
        s+=sparky(154,290,t,.62)
        s+=path('M 386 435 L 395 534 Q 426 545 456 534 L 465 435 Z','url(#glass)','#bafaff',3)+text(425,505,'5V',20,'#eaffff','middle')
        if u>.55:s+=path('M 420 435 l -10 42 l 14 4 l -10 33 M 433 451 l 15 18 l -12 8 l 10 26','none','#eaffff',3)
    elif scene==3:
        s+=text(42,115,'A CALM ONE-WAY FLOW',25,'#a9ffee')+label(42,132,'5V  /  DIRECT CURRENT','#75ffe1',14)
        s+=group(path('M -105 5 H -20 Q 10 5 10 30 V 46','none','#3ca393',30)+path('M -105 5 H -20 Q 10 5 10 30 V 46','none','#9af8dc',12)+circ(-18,-19,24,'url(#aqua)')+path('M -32 -19 H -4 M -18 -33 V -5','none','#125369',3),f'translate(215 303)')
        s+=glowpath('M 225 350 Q 225 395 226 455','#79ffe7',10)
        s+=path('M 159 440 L 174 567 Q 226 582 278 567 L 293 440 Z','url(#glass)','#b2fff4',3)
        s+=path(f'M 177 {535-75*u:.1f} Q 225 {525-75*u:.1f} 274 {535-75*u:.1f} L 267 559 Q 226 570 183 559 Z','url(#aqua)','none',1,'opacity=".65"')
        s+=steady(226,391+55*u,t,.5)+label(304,485,f'{int(25+75*u)}%', '#9dfff3',19)
    elif scene==4:
        s+=text(42,115,'01  TRANSFORMER',28,'#b9f6ff')+label(42,132,'MAGNETIC AIR GAP','#75f8ff',14)
        s+=coil(148,380,9,1)+coil(397,380,5,.76)
        for k in range(4):
            x=200+((t*72+k*45)%155);s+=f'<ellipse cx="{x:.1f}" cy="380" rx="20" ry="92" fill="none" stroke="#5afaff" stroke-width="3" opacity=".7"/>'
        s+=text(148,525,'120V AC',16,'#ffcb83','middle')+text(397,525,'5V AC',16,'#8effed','middle')
        s+=label(181,560,f'{int(120-115*u)} V', '#fff3a4',20)
    elif scene==5:
        s+=text(42,115,'02  ONE-WAY DIODE',27,'#b1f7ff')+label(42,132,'FORWARD  /  BLOCKED','#91ffdf',13)
        forward=math.sin(t*2.2)>0;ang=-34 if forward else 4
        s+=glowpath('M 55 400 H 480','#4de5ff',8)+rect(214,290,112,220,20,'url(#panel)','stroke="#66cfd6" stroke-width="3"')
        s+=group(rect(-8,-65,16,130,7,'url(#aqua)')+circ(0,0,12,'#dbfff3'),f'translate(270 400) rotate({ang})')
        s+=sparky(145+58*math.sin(t*2.2),398,t,.65)
        s+=label(320,315,'OPEN' if forward else 'BLOCKED!', '#99ffe1' if forward else '#ff9b87',15)
        for i in range(3):s+=circ(350+(i*45+t*48)%130,400,6,'#8cfaff')
    elif scene==6:
        s+=text(42,115,'03  DIODE BRIDGE',28,'#b1f8ff')+label(42,132,'TWO DIRECTIONS → ONE','#c5ffed',13)
        s+=glowpath('M 65 382 H 143 L 270 255 L 397 382 L 270 509 L 143 382 H 65 M 397 382 H 475','#65eafa',5)
        for x,y,a in [(206,319,-45),(334,319,45),(206,445,45),(334,445,-45)]:
            s+=group(path('M -20 -15 L 14 0 L -20 15 Z','url(#aqua)')+line(19,-18,19,18,'#b2fff5',4),f'translate({x} {y}) rotate({a})')
        for i in range(7):
            q=(t*.32+i/7)%1;x=150+q*244;y=382+(-1 if i%2 else 1)*120*math.sin(q*math.pi);s+=circ(x,y,5,'#fff5a7')
        s+=steady(455,382,t,.54)
    elif scene==7:
        s+=text(42,115,'04  CAPACITOR',28,'#a8f8ff')+label(42,132,'STORE  /  SMOOTH  /  RELEASE','#95ffde',12)
        s+=path('M 35 398 C 60 338 85 458 110 398 S 160 338 185 398','none','#ffd277',6)
        s+=rect(190,276,160,234,45,'url(#panel)','stroke="#7ffbff" stroke-width="4"')
        s+=rect(203,410-65*(.5+.5*math.sin(phase)),134,87+65*(.5+.5*math.sin(phase)),25,'url(#aqua)','opacity=".72"')
        s+=path('M 204 305 Q 270 323 336 305','none','#c6ffff',4)+glowpath('M 350 398 H 490','#73ffe1',6)+steady(438,398,t,.55)
        s+=label(205,531,'5.0V  PURE DC','#9dffe4',14)
    else:
        s+=text(42,115,'FOUR TINY MACHINES',28,'#b2f7ff')+label(42,132,'ONE REMARKABLE PLUG','#ffe29c',14)
        s+=charger(268,374,1.25)
        for i in range(4):
            xx=190+i*52;s+=circ(xx,380+8*math.sin(t*3+i),12,'url(#aqua)')+text(xx,386,str(i+1),13,'#102941','middle')
        s+=glowpath('M 190 428 H 350','#6cfff3',5)+battery(430,480,.95,.55)
    return s

def background(t,scene):
    s=rect(0,0,W,H,0,'url(#bg)')+circ(280+30*math.sin(t*.4),320,280,'url(#halo)')
    for x in range(-120,700,90):s+=path(f'M {x+(t*4)%90:.1f} 0 L {x+160+(t*4)%90:.1f} 960','none','#78b9e3',1,'opacity=".08"')
    for i in range(20):
        x=(i*113+39+t*(3+i%4))%540;y=(i*193+28-t*(5+i%5))%830
        s+=circ(round(x,1),round(y,1),1.2+i%3*.6,'#9beafa',f'opacity="{.15+(i%3)*.08}"')
    return s

def svg_frame(scene,t,duration,amp,left,right,previous=None):
    # Transition reveals the next zone over ten frames with a sliding camera.
    body=scene_art(scene,t,duration)
    bob_scale=1+.075*min(1,t/max(.1,duration))+.014*math.sin(t*.8+scene)
    body=group(body,f'translate({270*(1-bob_scale):.2f} {350*(1-bob_scale):.2f}) scale({bob_scale:.4f})')
    if previous is not None and t<.30:
        prev,pt,pdur=previous;q=min(1,t/.30);ease=1-(1-q)**3
        old=group(scene_art(prev,pt,pdur),f'translate({-540*ease:.1f} 0)',f'opacity="{1-ease:.3f}"')
        body=old+group(body,f'translate({540*(1-ease):.1f} 0)',f'opacity="{ease:.3f}"')
    # The host animates independently of the illustration. Pose follows the
    # scene's integrated spring angles rather than snapping on cuts.
    hx=(170,370,170,370,170,370,170,370,370)[scene]
    hscale=1.25 if scene in (0,1,8) else 1.12
    host_layer=host(hx,710,hscale,t,amp,left,right,scene)
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1920" viewBox="0 0 540 960">{DEFS}{background(t,scene)}{body}{host_layer}</svg>'

def frame_plan(timeline,rms):
    targets_l=[];targets_r=[]
    poses=[(48,-85),(-42,102),(70,-50),(-48,85),(36,-105),(72,-73),(-65,75),(20,-90),(-80,110)]
    frames=sum(x['frames'] for x in timeline)
    scenes=[]
    for beat in timeline:
        for j in range(beat['frames']):
            t=j/FPS;i=beat['index'];left,right=poses[i]
            targets_l.append(left+12*math.sin(t*1.9));targets_r.append(right+15*math.sin(t*1.55+.7))
            scenes.append((i,t,beat['duration'],beat['start'],j))
    left=spring_angles(targets_l,frames);right=spring_angles(targets_r,frames)
    for i,(scene,t,dur,start,j) in enumerate(scenes):
        prev=(scene-1,timeline[scene-1]['duration'],timeline[scene-1]['duration']) if scene>0 and j<9 else None
        yield scene,t,dur,float(rms[min(i,len(rms)-1)]),left[i],right[i],prev
