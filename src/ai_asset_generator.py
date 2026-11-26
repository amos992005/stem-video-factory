"""Generate and cache ten real AI images; never synthesize substitute artwork.

API keys are sent only as headers, never in URLs, logs, metadata, or Git.
Requests run concurrently within a bounded 15-second generation deadline.
"""
from __future__ import annotations
import argparse, asyncio, base64, io, json, os, time
from pathlib import Path
import aiohttp
from PIL import Image, ImageOps

SHOT_DIR=Path('assets/pilot_shots')
SHOTS=(
"3D Pixar CGI movie frame, vertical 9:16. Dr. Volt (charismatic young inventor, spiky electric-cyan hair, glowing goggles, white lab coat) stands in a dramatic dark-blue high-tech laboratory holding thick red wall power cables next to a glossy smartphone battery on a workbench. Volumetric lighting, Unreal Engine 5, no text.",
"3D Pixar CGI movie frame, vertical 9:16, extreme close-up macro shot. A heavy red power plug touching a glowing smartphone battery terminal as bright blue electric sparks begin to arc. Dr. Volt's wide excited eyes and goggles reflected in the background, cinematic depth of field, no text.",
"3D Pixar CGI movie frame, vertical 9:16, explosive action shot. The smartphone battery on the lab table erupts in a massive, colorful comic-style electrical explosion with neon cyan lightning bolts, bright orange fireballs, and flying glowing sparks, cinematic lighting, no text.",
"3D Pixar CGI movie frame, vertical 9:16, close-up portrait. Dr. Volt (spiky cyan hair blown backward, crooked glowing goggles, funny cartoon soot smudges on his face, coughing a small puff of smoke) looking shocked and amazed at the camera after the explosion, Pixar animation style, no text.",
"3D Pixar CGI movie frame, vertical 9:16, dynamic action angle. Dr. Volt struggling to hold a massive red firefighter's hose nozzle that is violently blasting a turbulent high-pressure jet of glowing blue water forward and backward, flying water droplets, dramatic lighting, no text.",
"3D Pixar CGI movie frame, vertical 9:16, slow-motion macro impact shot. A delicate crystal drinking glass shattering into dozens of glowing crystal shards as a violent high-pressure jet of water slams into it, dramatic rim lighting, Unreal Engine 5, no text.",
"3D Pixar CGI movie frame, vertical 9:16. A sleek futuristic glowing emerald faucet pouring a calm, smooth, peaceful crystal-clear stream of glowing water into an intact crystal drinking glass while Dr. Volt smiles approvingly in the background, warm magical lighting, no text.",
"3D Pixar CGI movie frame, vertical 9:16. Dr. Volt holding up a translucent glowing white smartphone charger brick in his hand like a glowing magical artifact, intricate miniature golden and cyan circuits glowing inside it, cinematic lighting, no text.",
"3D Pixar CGI movie frame, vertical 9:16, isometric tilt-shift miniature view inside a cutaway smartphone charger brick revealing a bustling four-room futuristic energy factory with glowing bridges, pipes, and turbine coils, Pixar production design, no text.",
"3D Pixar CGI movie frame, vertical 9:16, epic low-angle shot. Inside the miniature factory, two giant glowing copper spiral coils separated by a deep empty canyon gap, with brilliant neon cyan magnetic energy rings leaping across thin air while tiny Dr. Volt points upward in amazement, no text.",
)
# The requested 2.0/Imagen models are retired; include current Gemini image
# models as well, rather than assuming an API key makes old models available.
MODELS=('gemini-2.0-flash-exp-image-generation','gemini-3.1-flash-image-preview',
        'gemini-2.5-flash-image','gemini-2.0-flash-preview-image-generation',
        'gemini-2.0-flash-exp','imagen-3.0-generate-002')
BUDGET=15.0

class ImageGenerationError(RuntimeError):pass

def shot_path(directory,index):return Path(directory)/f'shot_{index:02}.jpg'

def valid_shot(path):
    try:
        with Image.open(path) as im:
            if im.format!='JPEG' or im.size!=(1080,1920):return False
            im.verify()
        return True
    except (OSError,ValueError):return False

def cache_complete(directory=SHOT_DIR):return all(valid_shot(shot_path(directory,i)) for i in range(1,11))

def save_image(data,path):
    if len(data)>30*1024*1024:raise ImageGenerationError('Image response exceeds 30 MiB')
    try:
        with Image.open(io.BytesIO(data)) as im:
            im.load()
            if im.width<384 or im.height<640:raise ValueError(f'image too small: {im.size}')
            image=ImageOps.fit(im.convert('RGB'),(1080,1920),method=Image.Resampling.LANCZOS)
            tmp=Path(path).with_suffix('.tmp');image.save(tmp,format='JPEG',quality=94,subsampling=0)
        os.replace(tmp,path)
    except (OSError,ValueError) as exc:raise ImageGenerationError(f'Invalid image response: {exc}') from exc

def safe_error(text,*secrets):
    for secret in secrets:
        if secret:text=text.replace(secret,'[REDACTED]')
    return text[:1600]

def decode_google(data):
    for candidate in data.get('candidates',[]):
        for part in candidate.get('content',{}).get('parts',[]):
            inline=part.get('inlineData') or part.get('inline_data') or {}
            if inline.get('data'):return base64.b64decode(inline['data'],validate=True)
    for item in data.get('predictions',[]):
        raw=item.get('bytesBase64Encoded') or item.get('bytes_base64_encoded')
        if raw:return base64.b64decode(raw,validate=True)
    raise ImageGenerationError('HTTP 200 but response contained no image data (model refusal or unsupported output)')

async def post(session,url,headers,payload,deadline,secrets,model):
    for attempt in range(2):
        remaining=deadline-time.monotonic()
        if remaining<=.1:raise ImageGenerationError(f'{model}: generation deadline exceeded')
        limit=min(remaining, 8.0 if model.startswith('gemini-3') or model.startswith('gemini-2.5') or model=='HF' else 2.5)
        try:
            async with session.post(url,headers=headers,json=payload,timeout=aiohttp.ClientTimeout(total=limit)) as response:
                data=await response.read()
                if response.status>=400:
                    detail=safe_error(data.decode('utf8','replace'),*secrets)
                    error=f'{model}: HTTP {response.status}: {detail}'
                    print(error,flush=True)
                    if response.status==429 and attempt==0 and deadline-time.monotonic()>.5:
                        await asyncio.sleep(.2);continue
                    raise ImageGenerationError(error)
                if model=='HF':
                    if not response.headers.get('Content-Type','').startswith('image/'):
                        raise ImageGenerationError(f'HF: HTTP {response.status} non-image response: '+safe_error(data.decode('utf8','replace'),*secrets))
                    return data
                return decode_google(json.loads(data))
        except asyncio.TimeoutError:
            error=f'{model}: request timed out after {limit:.1f}s';print(error,flush=True);raise ImageGenerationError(error)
        except (aiohttp.ClientError,ValueError,KeyError) as exc:
            error=f'{model}: {safe_error(str(exc),*secrets)}';print(error,flush=True);raise ImageGenerationError(error) from exc
    raise ImageGenerationError(f'{model}: retry exhausted')

async def generate_one(session,index,prompt,directory,key,hf,deadline):
    path=shot_path(directory,index)
    if valid_shot(path):print(f'Cached {path.name}',flush=True);return path
    errors=[];secrets=(key,hf)
    for model in MODELS:
        if deadline-time.monotonic()<.2:break
        endpoint=f'https://generativelanguage.googleapis.com/v1beta/models/{model}'
        if model.startswith('imagen'):
            url=endpoint+':predict';payload={'instances':[{'prompt':prompt}],'parameters':{'sampleCount':1,'aspectRatio':'9:16'}}
        else:
            url=endpoint+':generateContent';payload={'contents':[{'parts':[{'text':'Generate a vertical 9:16 3D animated movie frame: '+prompt}]}], 'generationConfig':{'responseModalities':['TEXT','IMAGE']}}
            if model.startswith(('gemini-3','gemini-2.5')):payload['generationConfig']['imageConfig']={'aspectRatio':'9:16'}
        try:
            result=await post(session,url,{'x-goog-api-key':key,'Content-Type':'application/json'},payload,deadline,secrets,model)
            save_image(result,path);print(f'Generated {path.name} with {model}',flush=True);return path
        except ImageGenerationError as exc:
            errors.append(str(exc))
            # If Google rate-limits, promptly try the optional authenticated HF
            # backend rather than waiting out the whole deadline.
            if 'HTTP 429' in str(exc) and hf:
                try:
                    blob=await post(session,'https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell',{'Authorization':f'Bearer {hf}'},{'inputs':prompt,'parameters':{'width':768,'height':1344}},deadline,secrets,'HF')
                    save_image(blob,path);print(f'Generated {path.name} with HF FLUX.1-schnell',flush=True);return path
                except ImageGenerationError as backup:errors.append(str(backup))
    if hf and deadline-time.monotonic()>.2:
        try:
            blob=await post(session,'https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell',{'Authorization':f'Bearer {hf}'},{'inputs':prompt,'parameters':{'width':768,'height':1344}},deadline,secrets,'HF')
            save_image(blob,path);print(f'Generated {path.name} with HF FLUX.1-schnell',flush=True);return path
        except ImageGenerationError as exc:errors.append(str(exc))
    raise ImageGenerationError(f'{path.name}: all available image providers failed: '+ ' | '.join(errors))

async def generate_all(directory=SHOT_DIR,key=None,hf=None,budget=BUDGET):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    missing=[i for i in range(1,11) if not valid_shot(shot_path(directory,i))]
    if not missing:print('All ten cached AI shots are valid; no image API call required.',flush=True);return directory
    key=key if key is not None else os.environ.get('GEMINI_API_KEY','')
    hf=hf if hf is not None else os.environ.get('HF_TOKEN','')
    if not key:raise ImageGenerationError('GEMINI_API_KEY is not set and cache is incomplete')
    deadline=time.monotonic()+budget
    async with aiohttp.ClientSession() as session:
        tasks=[asyncio.create_task(generate_one(session,i,SHOTS[i-1],directory,key,hf,deadline)) for i in missing]
        try:
            async with asyncio.timeout(budget):
                results=await asyncio.gather(*tasks,return_exceptions=True)
                errors=[str(result) for result in results if isinstance(result,BaseException)]
                if errors:raise ImageGenerationError('Failed to generate all shots: '+' | '.join(errors))
        except BaseException as exc:
            for task in tasks:task.cancel()
            await asyncio.gather(*tasks,return_exceptions=True)
            if isinstance(exc,TimeoutError):
                raise ImageGenerationError(f'Image generation did not complete within {budget:.1f} seconds; see preceding HTTP errors.') from None
            raise
    if not cache_complete(directory):raise ImageGenerationError('Generated shots failed cache validation')
    return directory

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check-cache',action='store_true');parser.add_argument('--directory',default=str(SHOT_DIR));a=parser.parse_args()
    if a.check_cache:raise SystemExit(0 if cache_complete(a.directory) else 1)
    asyncio.run(generate_all(a.directory))
