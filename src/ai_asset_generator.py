"""Download the seven specified Flux backdrops and four chroma-keyed portraits.

Pillow is used only to validate/resize service images and extract an alpha
channel; it does not draw or replace any artwork. No placeholder images are
silently substituted for service failures.
"""
from __future__ import annotations
import hashlib, io, json, logging, os, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import numpy as np
from PIL import Image, ImageFilter, ImageOps

CACHE=Path('assets/ai_cache')
BACKDROPS={
'beat1_lab_battery.jpg': 'Pixar 3D CGI animation style, dramatic high-tech dark blue laboratory table with a glowing glossy smartphone battery connected to a thick red wall power cable, cinematic volumetric lighting, Unreal Engine 5 render, no text',
'beat2_explosion.jpg': 'Pixar 3D CGI animation style, massive dramatic comic-book style electrical explosion on a lab table, bright orange fireballs, neon cyan lightning arcs, flying sparks, cinematic lighting, no text',
'beat3_firehose.jpg': "Pixar 3D CGI animation style, a giant red industrial firefighter hose nozzle violently blasting a high-pressure turbulent jet of glowing water back and forth, dynamic water droplets, dramatic lighting, no text",
'beat4_shattered_glass.jpg': 'Pixar 3D CGI animation style, a delicate crystal drinking glass shattering into glowing crystal shards under a violent high-pressure water blast, slow-motion cinematic action shot, Unreal Engine 5, no text',
'beat5_gentle_stream.jpg': 'Pixar 3D CGI animation style, a sleek futuristic glowing emerald water tap pouring a calm, smooth, peaceful crystal-clear stream into a glowing intact glass cup, warm magical lighting, no text',
'beat6_charger_factory.jpg': 'Pixar 3D CGI animation style, isometric cutaway inside a white smartphone charger brick revealing a miniature futuristic four-room glowing energy factory with tiny bridges, gears, and glowing pipes, tilt-shift miniature depth of field, no text',
'beat7_magnetic_canyon.jpg': 'Pixar 3D CGI animation style, inside a futuristic miniature factory, two giant glowing copper spirals separated by a deep canyon gap with glowing cyan magnetic energy rings leaping across thin air, epic lighting, no text',
}
CHARACTER=('Pixar style high quality 3D CGI character render, the same quirky young inventor Dr Volt, spiky electric cyan hair, expressive glowing futuristic blue goggles, white lab coat with cyan collar, warm brown skin, cyan lightning bolt badge, cinematic soft lighting, full body visible centered, no text, isolated on perfectly solid bright chroma key green #00FF00 background, no shadows on background. ')
POSES={
'dr_volt_curious.png':'Holding a glowing jumper cable with a mischievous curious grin.',
'dr_volt_shocked.png':'Hilarious shocked expression, face smudged with cartoon soot, hair blown back after an explosion.',
'dr_volt_pointing.png':'Energetic tour-guide pose pointing excitedly upward at the action.',
'dr_volt_mindblown.png':'Hands on cheeks in amazement watching the magnetic rings jump.',
}
SPECS=[(name,prompt,1080,1920,1601+i,False) for i,(name,prompt) in enumerate(BACKDROPS.items())]+[(name,CHARACTER+prompt,768,1024,98761,True) for name,prompt in POSES.items()]

def image_url(prompt,width,height,seed):
    return 'https://image.pollinations.ai/prompt/'+quote(prompt,safe='')+'?'+urlencode({'model':'flux','width':width,'height':height,'seed':seed,'nologo':'true'})

def cache_key(spec):return hashlib.sha256(json.dumps(spec,ensure_ascii=False).encode()).hexdigest()

def chroma_cutout(image):
    """Remove green screen, preserve cyan hair and feather alpha edges."""
    image=image.convert('RGB');rgb=np.asarray(image,dtype=np.float32)
    r,g,b=rgb[:,:,0],rgb[:,:,1],rgb[:,:,2]
    # Only strongly green colors are removed; cyan/blue goggles and hair remain.
    green=np.clip((g-np.maximum(r,b)*1.18-18)/65,0,1)
    alpha=Image.fromarray(np.uint8((1-green)*255)).filter(ImageFilter.GaussianBlur(1.0))
    coverage=1-np.asarray(alpha,dtype=np.float32).mean()/255
    if coverage<.08 or coverage>.95:
        raise ValueError(f'Chroma screen could not be extracted (background coverage {coverage:.1%})')
    out=image.convert('RGBA');out.putalpha(alpha)
    bbox=out.getchannel('A').getbbox()
    if not bbox: raise ValueError('Empty Dr Volt cutout')
    return out.crop(bbox)

def fetch_one(spec,cache=CACHE,attempts=3,timeout=35):
    name,prompt,width,height,seed,cutout=spec
    cache=Path(cache);cache.mkdir(parents=True,exist_ok=True);path=cache/name;meta=cache/(name+'.json')
    key=cache_key(spec)
    if path.exists() and meta.exists():
        try:
            if json.loads(meta.read_text())['key']==key:
                with Image.open(path) as im:im.verify()
                logging.info('Cache hit: %s',name);return path
        except (OSError,ValueError,KeyError): pass
    url=image_url(prompt,width,height,seed);error=None
    for attempt in range(attempts):
        try:
            req=Request(url,headers={'User-Agent':'STEMVideoFactoryPilot/1.0','Accept':'image/*'})
            with urlopen(req,timeout=timeout) as response:
                content=response.read(32*1024*1024+1);ctype=response.headers.get('Content-Type','')
                model=response.headers.get('x-model') or response.headers.get('x-pollinations-model') or 'not disclosed'
            if len(content)>32*1024*1024:raise ValueError('Image exceeds 32 MiB')
            if not ctype.lower().startswith('image/'):raise ValueError(f'Non-image response ({ctype})')
            with Image.open(io.BytesIO(content)) as src:
                src.load();source_size=src.size
                image=chroma_cutout(src) if cutout else ImageOps.fit(src.convert('RGB'),(width,height),method=Image.Resampling.LANCZOS)
                temp=path.with_suffix('.tmp');image.save(temp,format='PNG' if cutout else 'JPEG',quality=94)
            os.replace(temp,path)
            meta.write_text(json.dumps({'key':key,'requested_model':'flux','response_model_header':model,'source_dimensions':source_size}),encoding='utf8')
            logging.info('Received %s; service model header=%s; source dimensions=%s',name,model,source_size)
            return path
        except (OSError,ValueError,HTTPError) as exc:
            error=exc;logging.warning('%s attempt %d/%d: %s',name,attempt+1,attempts,exc)
            if attempt+1<attempts:time.sleep(min(15,3*(2**attempt)+(seed%4)))
    raise RuntimeError(f'Pollinations failed for {name}: {error}') from error

def generate_all(cache=CACHE,workers=6):
    """Fetch independently in parallel. Exactly seven backdrops were specified."""
    failures=[]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(fetch_one,s,cache):s[0] for s in SPECS}
        for f in as_completed(futures):
            try:f.result()
            except Exception as exc:failures.append(f'{futures[f]}: {exc}')
    if failures:raise RuntimeError('Could not obtain all required AI art:\n'+'\n'.join(failures))
    return Path(cache)

if __name__=='__main__':
    logging.basicConfig(level=logging.INFO,format='%(levelname)s %(message)s');generate_all()
