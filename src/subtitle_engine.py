"""Word-timed, single-line ASS captions and matching editable SRT subtitles.

Transcribe the clean narration before the music bed is mixed. ASS emits one
non-overlapping event per word with exactly one active word highlighted; timings
come from faster-whisper, not evenly distributed estimates.
"""
from dataclasses import dataclass
from pathlib import Path
import math
import re


@dataclass(frozen=True)
class Word:
    text: str
    start: float
    end: float


def collect_words(segments):
    words=[]
    for segment in segments:
        for item in segment.words or []:
            text=' '.join(item.word.strip().split())
            if not text: continue
            start=float(item.start); end=float(item.end)
            if not math.isfinite(start) or not math.isfinite(end):
                raise ValueError('Non-finite Whisper timestamp')
            start=max(0.,start)
            # Whisper can output zero-duration or slightly overlapping words.
            if words:
                start=max(start,words[-1].start+.01)
                prev=words[-1]
                if prev.end>start:
                    words[-1]=Word(prev.text,prev.start,start)
            end=max(start+.01,end)
            words.append(Word(text,start,end))
    if not words: raise RuntimeError('Whisper did not return any word timestamps')
    return words


def group_words(words, portrait=False):
    """Use 6–8 words landscape or 3–4 portrait, with natural punctuation breaks.

    Long words may force an earlier line break to avoid spilling outside margins.
    """
    max_words,min_words,max_chars=(4,3,28) if portrait else (8,6,58)
    groups=[]; current=[]
    for word in words:
        candidate=' '.join(w.text for w in [*current,word])
        if current and (len(current)>=max_words or len(candidate)>max_chars):
            groups.append(current);current=[]
        current.append(word)
        if len(current)>=min_words and re.search(r'[.!?;:]$',word.text):
            groups.append(current);current=[]
    if current: groups.append(current)
    return groups


def timestamp(seconds, ass=False):
    unit=100 if ass else 1000
    ticks=max(0,round(seconds*unit)); h,ticks=divmod(ticks,3600*unit);m,ticks=divmod(ticks,60*unit);s,frac=divmod(ticks,unit)
    return f'{h}:{m:02d}:{s:02d}.{frac:02d}' if ass else f'{h:02d}:{m:02d}:{s:02d},{frac:03d}'


def write_srt(path,groups):
    entries=[]
    for i,group in enumerate(groups,1):
        entries.append(f"{i}\n{timestamp(group[0].start)} --> {timestamp(group[-1].end)}\n"+' '.join(w.text for w in group))
    Path(path).write_text('\n\n'.join(entries)+'\n',encoding='utf-8')


def _escape(text):
    # Prevent source text from becoming ASS override tags or multiline markup.
    return text.replace('\\','').replace('{','(').replace('}',')').replace('\n',' ')


def write_ass(path,groups,portrait=False):
    w,h=(1080,1920) if portrait else (1920,1080)
    font_size=62 if portrait else 58
    outline=5 if portrait else 4
    margin_v=240 if portrait else 50
    header=f'''[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
ScaledBorderAndShadow: yes
WrapStyle: 2
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,{font_size},&H00FFFFFF,&H00FFFFFF,&H00140805,&H80000000,-1,0,0,0,100,100,0,0,1,{outline},2,2,80,80,{margin_v},1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    events=[]
    for group in groups:
        for i,word in enumerate(group):
            start=word.start
            # Hold the highlight until the next word starts; clamp pathological
            # overlapping timestamps so ASS events do not overlap.
            end=group[i+1].start if i+1<len(group) else word.end
            start_cs=round(start*100); end_cs=max(start_cs+1,round(end*100))
            parts=[]
            for j,wrd in enumerate(group):
                text=_escape(wrd.text)
                parts.append(r'{\1c&H20D7FF&}'+text+r'{\1c&HFFFFFF&}' if i==j else text)
            events.append(f'Dialogue: 0,{timestamp(start_cs/100,True)},{timestamp(end_cs/100,True)},Default,,0,0,0,,'+ ' '.join(parts))
    Path(path).write_text(header+'\n'.join(events)+'\n',encoding='utf-8')


def transcribe(model,source,portrait=False):
    segments,_=model.transcribe(str(source),language='en',word_timestamps=True,vad_filter=False,beam_size=5)
    return group_words(collect_words(segments),portrait)
