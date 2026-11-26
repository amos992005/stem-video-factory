"""Exact seven-beat Edge narration, tightly retimed to 28 seconds and SFX.

Edge's own word-boundary events drive ASS highlights; no Whisper model download
is necessary. Each beat is accelerated as needed instead of deleting words.
"""
from __future__ import annotations
import asyncio, difflib, math, re, subprocess, wave
from pathlib import Path
import numpy as np
from subtitle_engine import Word, group_words, write_ass

SCRIPT=(
"What would actually happen if you bypassed your phone charger and wired your battery straight to the wall?",
"It wouldn't charge faster—it would violently explode in seconds!",
"Why? Because wall power is like a massive firefighter's hose, blasting and sucking water back and forth sixty times a second!",
"Blast a fragile crystal glass with that firehose, and it shatters instantly!",
"Your phone battery needs a calm, one-way stream—like filling a glass from a gentle tap.",
"Inside this tiny plastic brick is a secret four-stage factory that tames that monster hose!",
"And in stage one, the electricity jumps across thin air without touching a wire! Follow for part two!",
)
RATE=24000
BEAT=4.0
DURATION=28.0
VOICE='en-US-AndrewMultilingualNeural'

def run(*args):subprocess.run([str(x) for x in args],check=True,stdout=subprocess.DEVNULL)

def read_wav(path):
    with wave.open(str(path),'rb') as f:
        if (f.getnchannels(),f.getsampwidth(),f.getframerate())!=(1,2,RATE):raise ValueError('Expected 24 kHz mono 16-bit WAV')
        return np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').astype(np.float32)/32768

def write_wav(path,samples):
    with wave.open(str(path),'wb') as f:
        f.setparams((1,2,RATE,0,'NONE','not compressed'))
        f.writeframes((np.clip(samples,-1,1)*32767).astype('<i2').tobytes())

def silence_bounds(samples, threshold=.009):
    """10ms RMS trim, retaining 40 ms of consonant breathing room."""
    n=240; padded=np.pad(samples,(0,(-len(samples))%n)); rms=np.sqrt(np.mean(padded.reshape(-1,n)**2,axis=1))
    hits=np.flatnonzero(rms>threshold)
    if not len(hits):raise ValueError('Narration clip is silent')
    return max(0,int(hits[0]*n-0.04*RATE)), min(len(samples),int((hits[-1]+1)*n+0.04*RATE))

def tempo_filters(ratio):
    """FFmpeg atempo chained within its high-quality 0.5–2.0 range."""
    if ratio<=0:raise ValueError('Invalid tempo ratio')
    values=[]
    while ratio>2:values.append(2.0);ratio/=2
    while ratio<.5:values.append(.5);ratio/=.5
    values.append(ratio)
    return ','.join(f'atempo={v:.9f}' for v in values)

async def synthesize_one(index,text,tmp):
    import edge_tts
    voice=edge_tts.Communicate(text,VOICE,rate='+12%',pitch='+2Hz',boundary='WordBoundary',connect_timeout=12,receive_timeout=35)
    path=tmp/f'voice_{index}.mp3';events=[]
    with open(path,'wb') as out:
        async for chunk in voice.stream():
            if chunk['type']=='audio':out.write(chunk['data'])
            elif chunk['type']=='WordBoundary':events.append(Word(chunk['text'],chunk['offset']/1e7,(chunk['offset']+chunk['duration'])/1e7))
    if not path.stat().st_size or not events:raise RuntimeError(f'No audio or word boundaries for beat {index+1}')
    return path,events

async def synthesize_all(tmp):
    return await asyncio.gather(*(synthesize_one(i,t,tmp) for i,t in enumerate(SCRIPT)))

def align_source(text,events,trim,ratio,offset):
    """Use timed Edge boundaries and preserve source punctuation/words exactly."""
    tokens=text.split();norm=lambda s:re.sub(r'[^a-z0-9]','',s.lower())
    a=[norm(t) for t in tokens];b=[norm(w.text) for w in events]
    result=[None]*len(tokens)
    for op,i,j,k,l in difflib.SequenceMatcher(a=a,b=b,autojunk=False).get_opcodes():
        if op=='equal':
            for ai,bi in zip(range(i,j),range(k,l)):
                w=events[bi];result[ai]=(w.start,w.end)
        elif i<j:
            start=events[k-1].end if k else trim
            end=events[l].start if l<len(events) else events[-1].end
            end=max(end,start+.01*(j-i));step=(end-start)/(j-i)
            for n in range(i,j):result[n]=(start+(n-i)*step,start+(n-i+1)*step)
    words=[]
    for token,(start,end) in zip(tokens,result):
        start=max(0.,min(BEAT-.01,(start-trim)/ratio));end=max(start+.01,min(BEAT,(end-trim)/ratio))
        if words:start=max(start,words[-1].start+.01)
        end=max(start+.01,end)
        words.append(Word(token,offset+start,offset+min(BEAT,end)))
    return words

def build_voice(tmp):
    tmp=Path(tmp);clips=asyncio.run(synthesize_all(tmp));all_words=[];audios=[];ratios=[]
    for i,(mp3,events) in enumerate(clips):
        source=tmp/f'raw_{i}.wav';run('ffmpeg','-v','error','-y','-i',mp3,'-ac','1','-ar',RATE,'-c:a','pcm_s16le',source)
        samples=read_wav(source);a,b=silence_bounds(samples);trim=tmp/f'trim_{i}.wav';write_wav(trim,samples[a:b])
        # Leave 60 ms at each boundary; no speech is omitted.
        target=3.88;ratio=(b-a)/RATE/target;ratios.append(ratio)
        adjusted=tmp/f'beat_{i}.wav'
        run('ffmpeg','-v','error','-y','-i',trim,'-af',tempo_filters(ratio)+',adelay=60,apad,atrim=0:4','-ac','1','-ar',RATE,'-c:a','pcm_s16le',adjusted)
        beat=read_wav(adjusted);beat=np.pad(beat,(0,max(0,int(BEAT*RATE)-len(beat))))[:int(BEAT*RATE)];audios.append(beat)
        all_words+=align_source(SCRIPT[i],events,a/RATE,ratio,i*BEAT+.06)
        print(f'Beat {i+1}: {len(samples)/RATE:.2f}s source, trim {(b-a)/RATE:.2f}s, additional tempo {ratio:.2f}x',flush=True)
    voice=np.concatenate(audios);write_wav(tmp/'voice.wav',voice)
    groups=group_words(all_words,portrait=True);ass=tmp/'pilot.ass'
    write_ass(ass,groups,portrait=True,margin_v=480)
    return voice,ass,ratios

def synth_sfx():
    """Deterministic transition accents, explosion, spray and glass, in seconds."""
    mix=np.zeros(round(DURATION*RATE),dtype=np.float32);rng=np.random.default_rng(7403)
    def add(at,sound,vol=1):
        i=round(at*RATE);length=min(len(sound),len(mix)-i)
        if length>0:mix[i:i+length]+=np.asarray(sound[:length],dtype=np.float32)*vol
    def timebase(d):return np.arange(round(d*RATE),dtype=np.float32)/RATE
    for at in (4,8,12,16,20,24):
        t=timebase(.35);noise=rng.normal(0,1,len(t));add(at,noise*np.sin(np.pi*t/.35)**2,.07)
    t=timebase(2.4);add(0,np.sin(2*np.pi*(70*t+130*t*t))*np.minimum(1,t/2.4)*.12)
    t=timebase(1.8);boom=np.sin(2*np.pi*(43*t+20*np.log1p(t*8)))*np.exp(-t*3.2);crackle=rng.normal(size=len(t))*np.exp(-t*7);add(4,boom*.43+crackle*.12)
    t=timebase(2.6);spray=rng.normal(size=len(t));spray=np.convolve(spray,np.ones(5)/5,mode='same');add(8,spray*np.sin(np.pi*t/2.6)**1.5,.18)
    t=timebase(1.4);glass=sum(np.sin(2*np.pi*f*t+rng.random()*6)*np.exp(-t*decay) for f,decay in [(1320,5),(2210,7),(3270,9),(4560,12)]);add(12,glass,.075)
    for at in (20,24):
        t=timebase(2.4);pad=sum(np.sin(2*np.pi*f*t)*np.sin(np.pi*t/2.4)**2 for f in (261.63,329.63,392,523.25));add(at,pad,.055)
    return mix

def mix_and_envelope(voice,tmp):
    mixed=voice*.82+synth_sfx();peak=max(1.,float(np.max(np.abs(mixed)))/.94);write_wav(Path(tmp)/'mix.wav',mixed/peak)
    # Normalize RMS robustly for animated cutout squash/stretch.
    n=RATE//30;rms=np.sqrt(np.mean(voice[:len(voice)//n*n].reshape(-1,n)**2,axis=1))
    return np.clip(rms/.13,0,1)
