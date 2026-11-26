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

# These are requested provider/model combinations, not claims of availability.
HF_MODELS=(
    *(("black-forest-labs/FLUX.1-schnell",provider) for provider in ("auto","fal-ai","together","nebius","replicate")),
    ("stabilityai/stable-diffusion-xl-base-1.0","hf-inference"),
    ("stabilityai/stable-diffusion-xl-base-1.0","auto"),
    ("PlaygroundAI/playground-v2.5-1024px-aesthetic","hf-inference"),
    ("ByteDance/SDXL-Lightning","hf-inference"),
)
SPACES=("black-forest-labs/FLUX.1-schnell","multimodalart/FLUX.1-merged",
        "stabilityai/stable-diffusion-3.5-large-turbo","prodia/fast-stable-diffusion")


def inference_worker(prompt,path,token,deadline):
    # Run in an isolated process: sync clients and provider discovery can block
    # beyond their own HTTP timeout, so the parent can terminate them reliably.
    from huggingface_hub import InferenceClient
    for model,provider in HF_MODELS:
        remaining=deadline-time.monotonic()
        if remaining<=.15:break
        print(f'Trying HF provider={provider} model={model}',flush=True)
        try:
            client=InferenceClient(api_key=token,provider=provider,timeout=min(remaining,2.5))
            image=client.text_to_image(prompt,model=model,width=768,height=1344)
            data=io.BytesIO();image.save(data,format='PNG');save_image(data.getvalue(),path)
            print(f'Generated {path.name} with HF {provider} {model}',flush=True);return
        except Exception as exc:
            status=getattr(getattr(exc,'response',None),'status_code',None)
            print(safe_error(f'HF {provider} {model}: '+(f'HTTP {status}: ' if status else '')+f'{type(exc).__name__}: {exc}',token),flush=True)
    raise ImageGenerationError('HF provider attempts exhausted or timed out')


def space_arguments(spec,prompt):
    """Build kwargs from live schema; reject unknown mandatory inputs."""
    args={};saw_prompt=False
    for p in spec.get('parameters',[]):
        name=p.get('parameter_name') or p.get('name')
        if not name: return None
        label=(name+' '+str(p.get('label',''))).lower().replace('-','_')
        if 'negative' in label and 'prompt' in label:args[name]='blurry, distorted, text, watermark'
        elif 'prompt' in label or name in ('text','text_input'):
            args[name]=prompt;saw_prompt=True
        elif name in ('width','image_width'):args[name]=768
        elif name in ('height','image_height'):args[name]=1344
        elif name in ('num_inference_steps','steps','num_steps'):args[name]=4
        elif name in ('randomize_seed','random_seed'):args[name]=True
        elif name in ('seed','random_seed_value'):args[name]=42
        elif name in ('guidance_scale','guidance'):args[name]=3.5
        elif p.get('parameter_has_default',False):continue
        else:return None
    outputs=spec.get('returns',[])
    image_output=any(any(kind in str(p).lower() for kind in ('image','gallery','filepath','file')) for p in outputs)
    return args if saw_prompt and image_output else None


def space_result_file(result,root):
    """Only load files that gradio_client itself downloaded to its temp dir."""
    if isinstance(result,(tuple,list)):
        for item in result:
            found=space_result_file(item,root)
            if found:return found
    elif isinstance(result,dict):
        for key in ('path','image','url','data'):
            if key in result:
                found=space_result_file(result[key],root)
                if found:return found
    elif isinstance(result,str):
        p=Path(result)
        try:
            if p.resolve().is_relative_to(root.resolve()) and p.is_file():return p
        except OSError:pass
    return None


def spaces_worker(prompt,path,token,deadline):
    import tempfile
    from gradio_client import Client
    for space in SPACES:
        if deadline-time.monotonic()<=.15:break
        print(f'Trying HF Space {space}',flush=True)
        try:
            with tempfile.TemporaryDirectory(prefix='pilot-gradio-') as d:
                # hf_token is accepted by older versions; current versions use token.
                try:client=Client(space,hf_token=token,verbose=False,download_files=d)
                except TypeError:client=Client(space,token=token,verbose=False,download_files=d)
                try:info=client.view_api(return_format='dict',print_info=False)
                except TypeError:info=client.view_api(return_format='dict')
                endpoints=info.get('named_endpoints',{})
                candidates=[]
                for name,spec in endpoints.items():
                    args=space_arguments(spec,prompt)
                    if args is not None:candidates.append((name,args))
                if not candidates:raise ImageGenerationError('No compatible text-to-image named endpoint in live Space schema')
                # Prefer common inference routes but always use discovered names.
                candidates.sort(key=lambda item: 0 if item[0] in ('/infer','/predict','/generate') else 1)
                for name,args in candidates:
                    try:
                        result=client.predict(api_name=name,**args)
                        image=space_result_file(result,Path(d))
                        if not image:raise ImageGenerationError('Space returned no downloadable image file')
                        save_image(image.read_bytes(),path)
                        print(f'Generated {path.name} with Space {space} endpoint {name}',flush=True);return
                    except Exception as exc:
                        print(safe_error(f'Space {space} endpoint {name}: {type(exc).__name__}: {exc}',token),flush=True)
        except Exception as exc:
            status=getattr(getattr(exc,'response',None),'status_code',None)
            print(safe_error(f'Space {space}: '+(f'HTTP {status}: ' if status else '')+f'{type(exc).__name__}: {exc}',token),flush=True)
    raise ImageGenerationError('HF Space attempts exhausted or timed out')


async def isolated_worker(kind,index,prompt,directory,token,deadline,phase_seconds):
    import sys
    remaining=min(phase_seconds,deadline-time.monotonic())
    if remaining<=.15:return False
    path=shot_path(directory,index)
    env=os.environ.copy();env['HF_TOKEN']=token
    cmd=[sys.executable,str(Path(__file__).resolve()),'--worker',kind,'--index',str(index),
         '--directory',str(directory),'--worker-deadline',str(time.monotonic()+remaining)]
    proc=await asyncio.create_subprocess_exec(*cmd,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.STDOUT,env=env)
    async def read_output():
        while True:
            line=await proc.stdout.readline()
            if not line:break
            print(safe_error(line.decode('utf8','replace').rstrip(),token,os.environ.get('GEMINI_API_KEY','')),flush=True)
    reader=asyncio.create_task(read_output())
    try:
        await asyncio.wait_for(proc.wait(),timeout=max(.01,min(remaining,deadline-time.monotonic())))
    except (asyncio.TimeoutError,asyncio.CancelledError):
        try:proc.kill()
        except ProcessLookupError:pass
        await proc.wait()
        print(f'{kind} {path.name}: phase deadline reached; worker terminated',flush=True)
        if asyncio.current_task().cancelling():raise
    finally:
        await reader
        path.with_suffix('.tmp').unlink(missing_ok=True)
    return valid_shot(path)


async def horde_request(session,method,url,deadline,**kwargs):
    remaining=deadline-time.monotonic()
    if remaining<=.05:raise ImageGenerationError('AI Horde generation deadline exceeded')
    async with session.request(method,url,timeout=aiohttp.ClientTimeout(total=min(remaining,3)),**kwargs) as response:
        body=await response.read()
        if response.status>=400:
            raise ImageGenerationError(f'AI Horde HTTP {response.status}: {body.decode("utf8","replace")[:1200]}')
        return body


async def horde_one(session,index,prompt,directory,deadline):
    base='https://aihorde.net/api/v2';headers={'apikey':'0000000000','Client-Agent':'stem-video-factory:1.0:github.com/amos992005/stem-video-factory'}
    payload={'prompt':prompt,'params':{'width':576,'height':1024,'steps':4,'n':1},
             'models':['AlbedoBase XL (SDXL)','SDXL 1.0'],'nsfw':False,'censor_nsfw':True}
    job=None
    try:
        response=await horde_request(session,'POST',base+'/generate/async',deadline,headers=headers,json=payload)
        job=json.loads(response)['id'];print(f'AI Horde accepted {shot_path(directory,index).name}',flush=True)
        while deadline-time.monotonic()>1.1:
            await asyncio.sleep(1)
            check=json.loads(await horde_request(session,'GET',base+'/generate/check/'+job,deadline,headers=headers))
            if check.get('faulted'):raise ImageGenerationError(f'AI Horde job faulted: {check}')
            if check.get('done'):
                result=json.loads(await horde_request(session,'GET',base+'/generate/status/'+job,deadline,headers=headers))
                generations=result.get('generations',[])
                if not generations or generations[0].get('censored'):raise ImageGenerationError('AI Horde returned no usable image')
                img=generations[0].get('img','')
                if img.startswith('https://'):
                    blob=await horde_request(session,'GET',img,deadline)
                else:blob=base64.b64decode(img,validate=True)
                save_image(blob,shot_path(directory,index));job=None
                print(f'Generated shot_{index:02}.jpg with AI Horde',flush=True);return True
        raise ImageGenerationError('AI Horde job did not finish before deadline')
    except (aiohttp.ClientError,asyncio.TimeoutError,ValueError,KeyError,ImageGenerationError) as exc:
        print(f'AI Horde shot_{index:02}: {type(exc).__name__}: {exc}',flush=True);return False
    finally:
        if job:
            # Do not leave anonymous volunteer GPU jobs queued after our deadline.
            try:
                async with session.delete(base+'/generate/status/'+job,headers=headers,timeout=aiohttp.ClientTimeout(total=.4)):pass
            except (aiohttp.ClientError,asyncio.TimeoutError):pass


async def generate_one(session,index,prompt,directory,key,hf,deadline):
    path=shot_path(directory,index)
    if valid_shot(path):print(f'Cached {path.name}',flush=True);return path
    if hf:
        if await isolated_worker('providers',index,prompt,directory,hf,deadline,7):return path
        if await isolated_worker('spaces',index,prompt,directory,hf,deadline,4):return path
    else:print(f'{path.name}: HF_TOKEN is not set; trying AI Horde',flush=True)
    if await horde_one(session,index,prompt,directory,deadline):return path
    raise ImageGenerationError(f'{path.name}: no provider returned a validated AI image before deadline')

async def generate_all(directory=SHOT_DIR,key=None,hf=None,budget=BUDGET):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    missing=[i for i in range(1,11) if not valid_shot(shot_path(directory,i))]
    if not missing:print('All ten cached AI shots are valid; no image API call required.',flush=True);return directory
    key=key if key is not None else os.environ.get('GEMINI_API_KEY','')
    hf=hf if hf is not None else os.environ.get('HF_TOKEN','')
    if not hf and not key:raise ImageGenerationError('No API credential is configured and cache is incomplete')
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
    parser=argparse.ArgumentParser();parser.add_argument('--check-cache',action='store_true');parser.add_argument('--directory',default=str(SHOT_DIR))
    parser.add_argument('--worker',choices=('providers','spaces'));parser.add_argument('--index',type=int);parser.add_argument('--worker-deadline',type=float);a=parser.parse_args()
    if a.check_cache:raise SystemExit(0 if cache_complete(a.directory) else 1)
    if a.worker:
        try:
            token=os.environ.get('HF_TOKEN','');path=shot_path(a.directory,a.index)
            (inference_worker if a.worker=='providers' else spaces_worker)(SHOTS[a.index-1],path,token,a.worker_deadline)
        except Exception as exc:
            print(safe_error(f'{type(exc).__name__}: {exc}',os.environ.get('HF_TOKEN',''),os.environ.get('GEMINI_API_KEY','')),flush=True)
            raise SystemExit(1)
    else:asyncio.run(generate_all(a.directory))
