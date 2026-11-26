"""Procedural, scene-synchronous sound effects and speech-ducked mixing."""
import numpy as np
RATE=24000

def make_sfx(timeline,length):
    out=np.zeros(length,np.float32);rng=np.random.default_rng(40103)
    def add(at,signal,amp=1):
        i=max(0,round(at*RATE));n=min(len(signal),len(out)-i)
        if n>0:out[i:i+n]+=np.asarray(signal[:n],np.float32)*amp
    def t(d):return np.arange(round(d*RATE),dtype=np.float32)/RATE
    def noise(d):return rng.normal(0,1,round(d*RATE)).astype('float32')
    # J-cut whip-pan before each visible camera transition.
    for beat in timeline[1:]:
        tt=t(.36);add(max(0,beat['start']-.22),noise(.36)*np.sin(np.pi*tt/.36)**2,.19)
    # Explosion, zap, shattering, magnetic hum, metallic turnstile and chime.
    tt=t(.8);add(timeline[0].get('cues',{}).get('boom',timeline[0]['start']+timeline[0]['duration']*.68),np.sin(2*np.pi*(53*tt+10*np.log1p(tt*10)))*np.exp(-tt*5)+noise(.8)*np.exp(-tt*11)*.4,.52)
    for scene in (0,1,2,4):
        tt=t(.4);add(timeline[scene]['start']+.45,noise(.4)*np.exp(-tt*10)*np.sin(2*np.pi*(500*tt+1300*tt*tt)),.22)
    tt=t(1.2);glass=sum(np.sin(2*np.pi*f*tt)*np.exp(-tt*d) for f,d in [(1412,4),(2320,6),(3460,8),(4320,10)])
    add(timeline[2]['start']+timeline[2]['duration']*.68,glass,.09)
    tt=t(min(3,timeline[4]['duration']));add(timeline[4]['start']+.1,np.sin(2*np.pi*92*tt)*np.sin(np.pi*tt/max(tt[-1],.01))**2,.2)
    for j in range(5):
        at=timeline[5]['start']+.4+j*.55
        if at<timeline[5]['start']+timeline[5]['duration']:
            tt=t(.16);add(at,(np.sin(2*np.pi*960*tt)+.7*np.sin(2*np.pi*1780*tt))*np.exp(-tt*28),.17)
    tt=t(1.0);chime=sum(np.sin(2*np.pi*f*tt)*np.exp(-tt*(2+i)) for i,f in enumerate((523.25,659.25,783.99)))
    add(timeline[8]['start']+.5,chime,.16)
    return out

def mix(voice,timeline):
    sfx=make_sfx(timeline,len(voice));rms_voice=float(np.sqrt(np.mean(voice.astype('float64')**2)))
    rms_sfx=float(np.sqrt(np.mean(sfx.astype('float64')**2)))
    gain=(rms_voice*10**(-14/20)/rms_sfx) if rms_sfx>1e-9 else 0
    # Smooth 10ms RMS envelope; narration activity ducks effects by 3 dB.
    step=RATE//100;padded=np.pad(voice,(0,(-len(voice))%step));rms=np.sqrt(np.mean(padded.reshape(-1,step)**2,axis=1))
    activity=np.clip(rms/.04,0,1);smooth=np.convolve(activity,np.ones(11)/11,mode='same')
    duck=np.repeat(1-(1-10**(-3/20))*smooth,step)[:len(voice)]
    master=voice*.88+sfx*gain*duck
    peak=max(1.,float(np.max(np.abs(master)))/.94)
    return (master/peak).astype('float32')
