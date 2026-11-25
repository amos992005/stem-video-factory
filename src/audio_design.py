"""Deterministic synthesized C-minor-nine underscore and three short effects."""
from pathlib import Path
import argparse
import wave
import numpy as np

SAMPLE_RATE=44100


def write_wav(path, samples, sample_rate=SAMPLE_RATE):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    samples=np.asarray(samples,dtype=np.float64)
    pcm=(np.clip(samples,-1,1)*32767).astype('<i2')
    channels=1 if pcm.ndim==1 else pcm.shape[1]
    with wave.open(str(path),'wb') as out:
        out.setnchannels(channels); out.setsampwidth(2); out.setframerate(sample_rate)
        out.writeframes(pcm.tobytes())
    return path


def synth_pad(duration=18,sample_rate=SAMPLE_RATE):
    """Warm C3/Eb3/G3/Bb3/D4 chord with a slow spectral LFO and loop fades."""
    t=np.arange(round(sample_rate*duration))/sample_rate
    frequencies=[130.8128,155.5635,195.9977,233.0819,293.6648]
    signal=np.zeros_like(t)
    for i,f in enumerate(frequencies):
        signal += .42*np.sin(2*np.pi*f*t+i*.3) + (.08+.06*np.sin(2*np.pi*.11*t+i))*np.sin(2*np.pi*2*f*t+i)
    signal *= (.7+.12*np.sin(2*np.pi*.09*t))*.19
    fade=np.minimum(1,np.minimum(t/.35,(duration-t)/.35))
    return signal*np.maximum(0,fade)


def make_effect(kind,sample_rate=SAMPLE_RATE):
    durations={'zap':.8,'whoosh':1.35,'chime':2.2}
    if kind not in durations: raise ValueError(kind)
    duration=durations[kind]; t=np.arange(round(sample_rate*duration))/sample_rate
    rng=np.random.default_rng(1234)
    if kind=='zap':
        signal=(.35*np.sin(2*np.pi*60*t)+.2*np.sin(2*np.pi*(300*t+500*t*t))+ .15*rng.normal(size=len(t)))*np.exp(-5*t)
    elif kind=='whoosh':
        # Rising, filtered-noise-like texture with a soft sinusoidal sweep.
        noise=rng.normal(size=len(t)); noise=np.convolve(noise,np.ones(14)/14,mode='same')
        signal=(.35*noise+.12*np.sin(2*np.pi*(180*t+380*t*t)))*np.sin(np.pi*t/duration)**2
    else:
        signal=sum(.15*np.sin(2*np.pi*f*t)*np.exp(-t*(1.1+i*.3)) for i,f in enumerate([523.25,659.25,783.99,1046.5]))
        signal*=np.minimum(1,t/.03)
    return np.clip(signal,-.8,.8)


def generate(directory):
    directory=Path(directory); directory.mkdir(parents=True,exist_ok=True)
    write_wav(directory/'ambient.wav',synth_pad())
    for name in ('zap','whoosh','chime'): write_wav(directory/f'{name}.wav',make_effect(name))
    return directory


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--output',default='assets/audio/ep01')
    args=parser.parse_args(); print('Synthesized audio:',generate(args.output))
