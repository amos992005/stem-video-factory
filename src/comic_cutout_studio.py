"""AI-illustrated sticker compositing. No procedural replacement artwork."""
from __future__ import annotations
import math
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageStat

FPS=30
ROOT=Path(__file__).resolve().parent.parent/'assets'/'comic_2d'
NAMES=('dr_volt_pointing','dr_volt_shocked','dr_volt_explaining','dr_volt_victory',
       'prop_plug_explosion','prop_firehose_glass','prop_transformer_coils','prop_diode_capacitor')
PROPS=(4,6,5,6,7,7)
POSES=(1,2,1,2,2,3)

def validate_assets(root=ROOT):
    for name in NAMES:
        path=root/(name+'.png')
        if not path.is_file(): raise ValueError(f'Missing required AI illustration: {path}; no fallback permitted')
        with Image.open(path) as im:
            im.load()
            if im.format!='PNG' or min(im.size)<512:raise ValueError(f'Invalid or undersized PNG: {path}')
            sample=im.convert('RGB').resize((128,128))
            stat=ImageStat.Stat(sample)
            if sum(stat.stddev)/3<18 or sample.entropy()<4.0:raise ValueError(f'Low visual entropy: {path}')
            a=np.array(sample); white=(a.min(axis=2)>240)
            if white.mean()<.08 or white.mean()>.95:raise ValueError(f'Invalid white background/content ratio: {path}')
    print(f'Validated {len(NAMES)} original AI-illustrated PNGs; no fallback.',flush=True)

def make_sticker(path,session):
    from rembg import remove
    image=np.asarray(Image.open(path).convert('RGBA'))
    # Remove only white connected to the edges, retaining interior white clothing.
    rgb=image[:,:,:3]; nearwhite=(rgb.min(axis=2)>=247).astype(np.uint8)
    flood=np.pad(nearwhite,1,constant_values=1); cv2.floodFill(flood,None,(0,0),2)
    key=(flood[1:-1,1:-1]!=2).astype(np.uint8)*255
    result=remove(Image.fromarray(image),session=session,post_process_mask=False)
    matte=np.asarray(result.convert('RGBA'))[:,:,3]
    # Keep the generated foreground (including white garments) if isolated from
    # the white border; rembg recovers soft colored details adjacent to white.
    alpha=np.maximum(key,matte);alpha[nearwhite.astype(bool)&(key==0)]=0
    if np.count_nonzero(alpha>64)<alpha.size*.01:raise ValueError(f'Empty cutout: {path}')
    pad=48
    rgba=np.zeros((image.shape[0]+pad*2,image.shape[1]+pad*2,4),np.uint8)
    rgba[pad:-pad,pad:-pad,:3]=rgb;rgba[pad:-pad,pad:-pad,3]=alpha
    border=cv2.dilate(rgba[:,:,3],cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(17,17)))
    # Trim empty areas but keep enough margin for outline and shadow.
    ys,xs=np.where(border>0)
    x0=max(0,int(xs.min())-26); x1=min(rgba.shape[1],int(xs.max())+31)
    y0=max(0,int(ys.min())-26); y1=min(rgba.shape[0],int(ys.max())+35)
    rgba=rgba[y0:y1,x0:x1];border=border[y0:y1,x0:x1]
    shift=np.float32([[1,0,10],[0,1,14]])
    shadow=cv2.warpAffine(border,shift,(border.shape[1],border.shape[0]))
    shadow=cv2.GaussianBlur(shadow,(21,21),0).astype(np.float32)/255*.55
    a=rgba[:,:,3].astype(np.float32)/255; b=border.astype(np.float32)/255
    # Premultiplied alpha composite foreground over solid white border and shadow.
    outa=a+b*(1-a)+shadow*(1-b)*(1-a)
    prem=rgba[:,:,:3].astype(np.float32)*a[:,:,None]+255*(b*(1-a))[:,:,None]
    rgbout=np.divide(prem,outa[:,:,None],out=np.zeros_like(prem),where=outa[:,:,None]>1e-6)
    return np.dstack((np.clip(rgbout,0,255).astype(np.uint8),(outa*255).astype(np.uint8)))

def prepare(root=ROOT,cache=None):
    validate_assets(root)
    from rembg import new_session
    session=new_session('u2netp')
    return [make_sticker(root/(n+'.png'),session) for n in NAMES]

def ease(t):
    return 1-math.exp(-7*max(0,t))*math.cos(11*max(0,t))

def blend(frame,img,cx,cy,width,rotation=0,sx=1,sy=1,opacity=1):
    h,w=img.shape[:2]; height=max(1,int(width*h/w*sy)); width=max(1,int(width*sx))
    if width>2600 or height>3200: return
    resized=cv2.resize(img,(width,height),interpolation=cv2.INTER_AREA if width<w else cv2.INTER_LINEAR)
    if abs(rotation)>.1:
        mat=cv2.getRotationMatrix2D((width/2,height/2),rotation,1)
        resized=cv2.warpAffine(resized,mat,(width,height),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
    x=int(cx-width/2);y=int(cy-height/2);x0=max(x,0);y0=max(y,0);x1=min(x+width,frame.shape[1]);y1=min(y+height,frame.shape[0])
    if x0>=x1 or y0>=y1:return
    layer=resized[y0-y:y1-y,x0-x:x1-x];target=frame[y0:y1,x0:x1]
    a=layer[:,:,3:4].astype(np.float32)*(opacity/255)
    target[:]=np.clip(layer[:,:,:3]*a+target*(1-a),0,255).astype(np.uint8)

class Studio:
    def __init__(self,stickers):
        self.stickers=stickers
        # Generate only backgrounds and effects procedurally, never characters or props.
        y,x=np.mgrid[:960,:540];self.xx=x;self.yy=y
        self.rng=np.random.default_rng(781);self.particles=self.rng.uniform([0,0],[540,960],(38,2))
    def frame(self,t,scene,local,rms):
        beat=int(t/1.45);phase=t-beat*1.45; mode=beat%4
        colors=[(54,15,26),(16,47,65),(56,18,31),(12,55,42),(16,52,61),(12,55,42)]
        c=np.array(colors[scene],dtype=np.float32)
        dx=self.xx-(290+55*math.sin(t*.45));dy=self.yy-340
        glow=np.exp(-(dx*dx/70000+dy*dy/130000))[:,:,None]
        base=np.array([8,15,31],np.float32)+glow*c
        grid=((np.mod(self.xx+t*9,90)<1)|(np.mod(self.yy+t*6,90)<1))[:,:,None]
        frame=np.clip(base+grid*np.array([8,15,19]),0,255).astype(np.uint8)
        for n,(x,y) in enumerate(self.particles):
            xx=int((x+math.sin(t*.6+n)*8)%540);yy=int((y-t*(3+n%5))%960)
            cv2.circle(frame,(xx,yy),1+(n%2),(35,89,105),-1,cv2.LINE_AA)
        frame=cv2.resize(frame,(1080,1920),interpolation=cv2.INTER_LINEAR)
        # Four intentionally distinct compositions per beat; hard camera cuts
        # combined with a short spring/pan ease deliver readable close-ups.
        prop=self.stickers[PROPS[scene]]; pose=POSES[scene]
        if scene==0 and local<.65:pose=0
        person=self.stickers[pose]
        pop=max(.72,min(1.14,.78+.22*ease(phase)))
        layouts=[(540,650,790,230,1410,380),(700,740,1080,205,1400,300),
                 (280,600,700,730,1180,690),(570,850,990,800,1500,315)]
        px,py,pw,cx,cy,cw=layouts[mode]
        px+=int(25*math.sin(t*1.1));cy+=int(7*math.sin(t*2.0));amp=float(rms)
        blend(frame,prop,px,py,int(pw*pop),rotation=2*math.sin(t*1.6))
        # FX are decorative overlays, not replacement character or object art.
        if scene in (1,3):
            for k in range(3):
                r=30+((t*120+k*54)%170); cv2.ellipse(frame,(int(px-70+k*50),int(py)),(int(r*.32),int(r)),0,0,360,(40,225,245),3,cv2.LINE_AA)
        if scene in (0,2):
            x=int(px+50*math.sin(t*16));y=int(py-70)
            points=np.array([[x-50,y-120],[x+8,y-65],[x-18,y-18],[x+45,y+40],[x+5,y+100]],np.int32)
            cv2.polylines(frame,[points],False,(255,61,73),7,cv2.LINE_AA)
        blend(frame,person,cx,cy,int(cw*pop),rotation=4*math.sin(t*3)*amp,sx=1-.04*amp,sy=1+.08*amp)
        return cv2.cvtColor(frame,cv2.COLOR_RGB2BGRA).tobytes()
