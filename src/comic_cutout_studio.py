"""AI illustration stickers on a zone-constrained comic stage (no fallback art)."""
from __future__ import annotations
import math
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageStat

FPS=30
ROOT=Path(__file__).resolve().parent.parent/'assets'/'comic_2d'
NAMES=('dr_volt_pointing','dr_volt_shocked','dr_volt_explaining','dr_volt_victory',
       'prop_plug_explosion','prop_firehose_glass','prop_transformer_coils','prop_diode_capacitor',
       'prop_gentle_faucet','prop_diode_turnstile','prop_charged_phone')
# The transformer is shown twice, as required by the story; the last scene
# transitions from the capacitor illustration to the charged-phone payoff.
PROPS=(4,6,5,8,6,9,7)
POSES=(1,2,1,2,2,2,3)
HEADERS=('120V AC DANGER!', 'THE AIR-GAP MYSTERY','60Hz BACK & FORTH',
         'CALM LOW-VOLTAGE DC','STAGE 1: TRANSFORMER','STAGE 2: DIODE VALVE',
         'STAGE 3: CAPACITOR SMOOTHING')
BADGES=('US MAINS EXAMPLE','MAGNETIC TRANSFER','SLOW-MOTION ANALOGY','ONE-WAY FLOW',
        'VOLTAGE CHANGE','ONE-WAY PATH','SMOOTHED DC')
STAGE=(70,230,1010,1080)
PROP_MAX=(880,780)
PRESENTER_TOP=1080

def validate_assets(root=ROOT):
    for name in NAMES:
        path=root/(name+'.png')
        if not path.is_file(): raise ValueError(f'Missing required AI illustration: {path}; no fallback permitted')
        with Image.open(path) as im:
            im.load()
            if im.format!='PNG' or min(im.size)<512:raise ValueError(f'Invalid or undersized PNG: {path}')
            sample=im.convert('RGB').resize((128,128));stat=ImageStat.Stat(sample)
            if sum(stat.stddev)/3<18 or sample.entropy()<4.0:raise ValueError(f'Low visual entropy: {path}')
            a=np.array(sample); white=(a.min(axis=2)>240)
            if white.mean()<.08 or white.mean()>.95:raise ValueError(f'Invalid white background/content ratio: {path}')
    print(f'Validated {len(NAMES)} original AI-illustrated PNGs; no fallback.',flush=True)

def remove_small_islands(alpha,ratio=.05):
    """Remove alpha components smaller than 5% of the largest foreground area."""
    binary=(alpha>32).astype(np.uint8)
    count,labels,stats,_=cv2.connectedComponentsWithStats(binary,8)
    if count<2: raise ValueError('Cutout has no visible foreground')
    areas=stats[1:,cv2.CC_STAT_AREA];largest=int(areas.max())
    keep=np.zeros(count,np.uint8);keep[1:]=(areas>=largest*ratio).astype(np.uint8)
    # Retain anti-aliased fringes adjacent to retained connected components.
    mask=cv2.dilate(keep[labels],np.ones((3,3),np.uint8),iterations=1)
    return np.where(mask,alpha,0).astype(np.uint8)

def make_sticker(path,session):
    from rembg import remove
    image=np.asarray(Image.open(path).convert('RGBA'));rgb=image[:,:,:3]
    nearwhite=(rgb.min(axis=2)>=235).astype(np.uint8)
    flood=np.pad(nearwhite,1,constant_values=1);cv2.floodFill(flood,None,(0,0),2)
    key=(flood[1:-1,1:-1]!=2).astype(np.uint8)*255
    matte=np.asarray(remove(Image.fromarray(image),session=session,post_process_mask=False).convert('RGBA'))[:,:,3]
    alpha=np.maximum(key,matte);alpha[nearwhite.astype(bool)&(key==0)]=0
    alpha=remove_small_islands(alpha)
    if np.count_nonzero(alpha>64)<alpha.size*.01:raise ValueError(f'Empty cutout: {path}')
    pad=48;rgba=np.zeros((image.shape[0]+pad*2,image.shape[1]+pad*2,4),np.uint8)
    rgba[pad:-pad,pad:-pad,:3]=rgb;rgba[pad:-pad,pad:-pad,3]=alpha
    border=cv2.dilate(rgba[:,:,3],cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(17,17)))
    ys,xs=np.where(border>0)
    x0=max(0,int(xs.min())-26);x1=min(rgba.shape[1],int(xs.max())+31)
    y0=max(0,int(ys.min())-26);y1=min(rgba.shape[0],int(ys.max())+35)
    rgba=rgba[y0:y1,x0:x1];border=border[y0:y1,x0:x1]
    shift=np.float32([[1,0,10],[0,1,14]])
    shadow=cv2.warpAffine(border,shift,(border.shape[1],border.shape[0]))
    shadow=cv2.GaussianBlur(shadow,(21,21),0).astype(np.float32)/255*.55
    a=rgba[:,:,3].astype(np.float32)/255;b=border.astype(np.float32)/255
    outa=a+b*(1-a)+shadow*(1-b)*(1-a)
    prem=rgba[:,:,:3].astype(np.float32)*a[:,:,None]+255*(b*(1-a))[:,:,None]
    rgbout=np.divide(prem,outa[:,:,None],out=np.zeros_like(prem),where=outa[:,:,None]>1e-6)
    return np.dstack((np.clip(rgbout,0,255).astype(np.uint8),(outa*255).astype(np.uint8)))

def prepare(root=ROOT,cache=None):
    validate_assets(root)
    from rembg import new_session
    session=new_session('u2netp')
    return [make_sticker(root/(n+'.png'),session) for n in NAMES]

def fit_prop(img,zoom=1):
    """Bounding box includes outline and shadow and can never leave the stage."""
    h,w=img.shape[:2];scale=min(PROP_MAX[0]/w,PROP_MAX[1]/h)*min(max(zoom,.6),1.0)
    width=max(1,round(w*scale));height=max(1,round(h*scale))
    return ((1080-width)//2,(1310-height)//2,width,height)

def blend_at(frame,img,x,y,width,height):
    if width<1 or height<1:return
    resized=cv2.resize(img,(width,height),interpolation=cv2.INTER_AREA if width<img.shape[1] else cv2.INTER_LINEAR)
    x0=max(x,0);y0=max(y,0);x1=min(x+width,frame.shape[1]);y1=min(y+height,frame.shape[0])
    if x0>=x1 or y0>=y1:return
    layer=resized[y0-y:y1-y,x0-x:x1-x];target=frame[y0:y1,x0:x1]
    a=layer[:,:,3:4].astype(np.float32)/255
    target[:]=np.clip(layer[:,:,:3]*a+target*(1-a),0,255).astype(np.uint8)

def blend(frame,img,cx,cy,width,rotation=0,sx=1,sy=1,opacity=1):
    h,w=img.shape[:2];height=max(1,int(width*h/w*sy));width=max(1,int(width*sx))
    blend_at(frame,img,int(cx-width/2),int(cy-height/2),width,height)

def rounded(frame,p1,p2,r,color,thickness=-1):
    x1,y1=p1;x2,y2=p2
    if thickness<0:
        cv2.rectangle(frame,(x1+r,y1),(x2-r,y2),color,-1);cv2.rectangle(frame,(x1,y1+r),(x2,y2-r),color,-1)
        for x,y in ((x1+r,y1+r),(x2-r,y1+r),(x1+r,y2-r),(x2-r,y2-r)):cv2.circle(frame,(x,y),r,color,-1,cv2.LINE_AA)
    else:
        cv2.line(frame,(x1+r,y1),(x2-r,y1),color,thickness,cv2.LINE_AA);cv2.line(frame,(x1+r,y2),(x2-r,y2),color,thickness,cv2.LINE_AA)
        cv2.line(frame,(x1,y1+r),(x1,y2-r),color,thickness,cv2.LINE_AA);cv2.line(frame,(x2,y1+r),(x2,y2-r),color,thickness,cv2.LINE_AA)
        for x,y,a,b in ((x1+r,y1+r,180,270),(x2-r,y1+r,270,360),(x1+r,y2-r,90,180),(x2-r,y2-r,0,90)):
            cv2.ellipse(frame,(x,y),(r,r),0,a,b,color,thickness,cv2.LINE_AA)

def text_fit(frame,text,x,y,max_width,color,scale=1.1,thick=2):
    font=cv2.FONT_HERSHEY_DUPLEX
    size=cv2.getTextSize(text,font,scale,thick)[0][0]
    if size>max_width:scale*=max_width/size
    cv2.putText(frame,text,(x,y),font,scale,color,thick,cv2.LINE_AA)

def presenter(frame,img,cx,level,t):
    """Split at the neck and rotate the head about that joint, clipped to presenter zone."""
    width=540;height=int(width*img.shape[0]/img.shape[1]);top=PRESENTER_TOP+18
    # The exact fractional neck depends on each AI pose; 30% avoids cutting
    # most faces, while remaining a simple image cut (not a skeletal redraw).
    neck=int(img.shape[0]*.31);head=img[:neck].copy();torso=img[neck:].copy()
    imgscaled=cv2.resize(img,(width,height));cut=int(height*.31)
    torso=imgscaled[cut:].copy();head=imgscaled[:cut].copy()
    # Signed angular motion is RMS-gated and independently pivoted at the neck.
    tilt=6*level*math.sin(t*12.0)
    mat=cv2.getRotationMatrix2D((width/2,cut-3),tilt,1)
    head=cv2.warpAffine(head,mat,(width,cut),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
    # Torso breathes independently by a few pixels; the frame edge crops legs.
    bounce=int(level*7);x=int(cx-width/2);region=frame[PRESENTER_TOP:]
    blend_at(region,torso,x,top-PRESENTER_TOP+cut-bounce,width,torso.shape[0])
    blend_at(region,head,x,top-PRESENTER_TOP-bounce,width,head.shape[0])

def draw_overlays(frame,scene,t,local):
    if scene==0:
        if int(t*3)%2==0:
            pts=np.array([[220,425],[275,485],[245,525],[315,585]],np.int32);cv2.polylines(frame,[pts],False,(255,65,74),7,cv2.LINE_AA)
        text_fit(frame,'DANGER: 120V AC!',135,320,460,(255,125,130),.9,2)
    if scene in (1,4):
        for k in range(3):
            r=26+int((t*95+k*55)%115)
            cv2.ellipse(frame,(480+k*55,650),(int(r*.32),r),0,0,360,(40,233,255),4,cv2.LINE_AA)
        if scene==4:
            # Conceptual indicator only: charger topology and voltages vary.
            text_fit(frame,'STEP-DOWN (ILLUSTRATIVE)',125,1005,750,(120,239,255),.75,2)
    if scene==2:
        y=1003;forward=int(t*2)%2==0
        cv2.arrowedLine(frame,(340 if forward else 740,y),(740 if forward else 340,y),(255,85,88),6,cv2.LINE_AA,tipLength=.09)
        text_fit(frame,'PUSH / PULL - SLOWED',190,330,700,(255,161,161),.85,2)
    if scene==5 and int(t*2.5)%2==0:text_fit(frame,'BLOCKED!',700,330,240,(255,100,115),.85,2)
    if scene==6 and local>1.35:
        text_fit(frame,'SMOOTH DC',150,1005,400,(135,255,194),.9,2)

def prop_for(scene,local):
    return 10 if scene==6 and local>=1.35 else PROPS[scene]

class Studio:
    def __init__(self,stickers):
        if len(stickers)!=len(NAMES):raise ValueError('All illustrated cutouts required')
        self.stickers=stickers
        y,x=np.mgrid[:960,:540];self.xx=x;self.yy=y
        self.particles=np.random.default_rng(781).uniform([0,0],[540,960],(38,2))
    def frame(self,t,scene,local,rms):
        colors=[(65,17,30),(16,48,65),(65,20,35),(12,55,42),(16,52,61),(65,20,35),(12,55,42)]
        c=np.array(colors[scene],dtype=np.float32)
        dx=self.xx-(290+55*math.sin(t*.45));dy=self.yy-340
        glow=np.exp(-(dx*dx/70000+dy*dy/130000))[:,:,None]
        grid=((np.mod(self.xx+t*9,90)<1)|(np.mod(self.yy+t*6,90)<1))[:,:,None]
        frame=np.clip(np.array([8,15,31],np.float32)+glow*c+grid*np.array([8,15,19]),0,255).astype(np.uint8)
        for n,(x,y) in enumerate(self.particles):
            cv2.circle(frame,(int((x+math.sin(t*.6+n)*8)%540),int((y-t*(3+n%5))%960)),1,(35,89,105),-1,cv2.LINE_AA)
        frame=cv2.resize(frame,(1080,1920))
        rounded(frame,(70,70),(1010,210),28,(25,33,58));rounded(frame,(70,70),(1010,210),28,(82,214,235),3)
        text_fit(frame,HEADERS[scene],100,130,870,(255,255,255),1.0,2)
        text_fit(frame,BADGES[scene],105,182,870,(95,234,250),.65,2)
        rounded(frame,(70,230),(1010,1080),34,(18,27,58));rounded(frame,(70,230),(1010,1080),34,(38,115,142),4)
        prop=self.stickers[prop_for(scene,local)]
        zoom=.86+.11*(.5+.5*math.sin(t*1.4))
        x,y,w,h=fit_prop(prop,zoom);blend_at(frame,prop,x,y,w,h)
        draw_overlays(frame,scene,t,local)
        side=260 if scene%2==0 else 820
        presenter(frame,self.stickers[POSES[scene]],side,float(rms),t)
        # A single always-present translucent pill under ASS subtitles.
        overlay=frame.copy();rounded(overlay,(50,1650),(1030,1830),44,(4,10,25))
        cv2.addWeighted(overlay,.84,frame,.16,0,frame)
        rounded(frame,(50,1650),(1030,1830),44,(52,86,105),2)
        return cv2.cvtColor(frame,cv2.COLOR_RGB2BGRA).tobytes()
