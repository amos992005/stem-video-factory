"""Audit finished subtitled files; exclude the lower 20% from both metrics.

Motion: union of 6/255 adjacent-frame changes over every 2-second window at
5fps, using 320x180 grayscale. Composition: compare normalized 9x20 spatial maps of above-median
luminance for contact-sheet frames separated by at least nine seconds. This
reduces uniform gradient influence without using captions or shot metadata. Both are heuristics and cannot prove visual or editorial quality.
"""
import argparse
import subprocess
import json
from pathlib import Path
import numpy as np
from package_ep01 import FULL, SHORTS as LEGACY_SHORTS
SHORTS=tuple(LEGACY_SHORTS.values())

FPS=5
WIDTH=320
HEIGHT=180
PIXEL_THRESHOLD=6
MIN_CHANGED=.03
MIN_DIVERSITY=.22


def motion_windows(frames, fps=FPS, pixel_threshold=PIXEL_THRESHOLD):
    frames=np.asarray(frames,dtype=np.uint8)
    if frames.ndim != 3 or len(frames)<2*fps+1:
        raise ValueError('at least 2 seconds plus one frame are required')
    frames=frames[:,:int(frames.shape[1]*.8),:]
    diffs=np.abs(frames[1:].astype(np.int16)-frames[:-1].astype(np.int16))>=pixel_threshold
    n=2*fps
    return [(i/fps,float(np.logical_or.reduce(diffs[i:i+n],axis=0).mean())) for i in range(len(diffs)-n+1)]


def layout_descriptor(frame):
    frame=np.asarray(frame,dtype=np.float32)
    frame=frame[:int(frame.shape[0]*.8)]
    # Remove the broad background field so bright foreground shapes, rather
    # than a constant full-frame gradient, determine spatial composition.
    frame=np.maximum(frame-np.median(frame),0)
    rows,cols=9,20
    tiles=np.array([[block.mean() if block.size else 0 for block in np.array_split(row,cols,axis=1)]
                    for row in np.array_split(frame,rows,axis=0)],dtype=np.float64).ravel()
    return tiles/(tiles.sum()+1e-9)


def composition_pairs(frames, stride=2):
    if len(frames)<30: raise ValueError('Need 30 frames for composition audit')
    if not 1<=stride<30: raise ValueError('Invalid composition stride')
    descriptors=[layout_descriptor(frame) for frame in frames[:30]]
    return [(i,i+stride,float(np.abs(descriptors[i]-descriptors[i+stride]).sum()/2)) for i in range(30-stride)]



def sheet_samples(path):
    """Decode the actual landscape contact sheet into its thirty 320×180 cells."""
    command=['ffmpeg','-v','error','-i',str(path),'-vf','scale=1600:1080,format=gray','-frames:v','1','-f','rawvideo','-']
    data=subprocess.run(command,check=True,stdout=subprocess.PIPE).stdout
    expected=1600*1080
    if len(data)!=expected: raise ValueError('Could not decode the contact sheet')
    return split_sheet(np.frombuffer(data,dtype=np.uint8).reshape(1080,1600))


def split_sheet(sheet):
    if sheet.shape!=(1080,1600): raise ValueError('Unexpected contact sheet dimensions')
    return [sheet[row*180:(row+1)*180,col*320:(col+1)*320] for row in range(6) for col in range(5)]

def duration(path):
    data=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(path)]))
    return float(data['format']['duration'])


def decode_frames(path):
    cmd=['ffmpeg','-v','error','-i',str(path),'-vf',f'fps={FPS},scale={WIDTH}:{HEIGHT},format=gray','-f','rawvideo','-']
    p=subprocess.run(cmd,check=True,stdout=subprocess.PIPE)
    unit=WIDTH*HEIGHT
    if len(p.stdout)%unit: raise ValueError(f'incomplete decoded frame: {path}')
    return np.frombuffer(p.stdout,dtype=np.uint8).reshape(-1,HEIGHT,WIDTH)


def contact_sheet(path,dest,portrait=False):
    length=duration(path)
    dimensions='270:480' if portrait else '480:270'
    vf=f'fps=30/{length},scale={dimensions}:flags=lanczos,tile=5x6:nb_frames=30'
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(path),'-vf',vf,'-frames:v','1','-update','1',str(dest)],check=True)
    if not Path(dest).is_file(): raise RuntimeError(f'Could not create {dest}')


def audit(directory,strict=True):
    directory=Path(directory)
    videos=[directory/(FULL+'.mp4')]+[directory/(name+'.mp4') for name in SHORTS]
    contact_sheet(videos[0],directory/'visual_contact_sheet_16x9.png')
    for i, video in enumerate(videos[1:], 1):
        contact_sheet(video,directory/f'visual_contact_sheet_short{i:02}.png',portrait=True)
    lines=['# Episode 01 motion and composition audit','','Method: 5 fps, 320×180 grayscale; '
           'adjacent-frame intensity change ≥6/255. Each overlapping 2-second window uses the union of changed pixels '
           'across 10 frame differences; windows slide by 0.2 seconds. The lower 20% is excluded so subtitles '
           'cannot make a static scene pass. Motion threshold: strictly greater than 3%. Composition compares normalized 9×20 coarse '
           'above-median foreground-luminance maps of contact-sheet frames at least nine seconds apart, excluding the lower 20%; '
           'minimum distance 0.22. Median subtraction reduces the influence of uniform gradients. '
           'These are heuristics, not proof of artistic quality.','','| Video | Minimum motion | Windows at or below 3% | Result |','|---|---:|---:|---|']
    failed=[];details=[]
    for video in videos:
        decoded=decode_frames(video)
        windows=motion_windows(decoded)
        bad=[(time,value) for time,value in windows if value<=MIN_CHANGED]
        minimum=min(value for _,value in windows)
        lines.append(f'| {video.name} | {minimum*100:.2f}% | {len(bad)} / {len(windows)} | {"FAIL" if bad else "PASS"} |')
        if bad:
            failed.append(video.name+' (motion)')
            details.append(f'**{video.name} flagged window starts (seconds):** '+', '.join(f'{t:.1f}' for t,_ in bad[:100])+(' …' if len(bad)>100 else ''))
        sheet = directory/('visual_contact_sheet_16x9.png' if video==videos[0] else f'visual_contact_sheet_short{videos.index(video):02}.png')
        stride=min(29,max(2,int(np.ceil(9*30/duration(video)))))
        pairs=composition_pairs(sheet_samples(sheet),stride=stride)
        bad_pairs=[(i,j,v) for i,j,v in pairs if v<MIN_DIVERSITY]
        details.append(f'**{video.name} contact-sheet composition** (stride {stride}): minimum {min(v for _,_,v in pairs):.3f}; {len(bad_pairs)} / {len(pairs)} pairs below {MIN_DIVERSITY:.2f}: {"FAIL" if bad_pairs else "PASS"}.')
        if bad_pairs:
            details.append('Flagged pairs (1-based): '+', '.join(f'{i+1}–{j+1} ({v:.3f})' for i,j,v in bad_pairs))
            failed.append(video.name+' (composition)')
    lines.extend(['']+details)
    report=directory/'motion_audit_report.md';report.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(report.read_text(),flush=True)
    if failed and strict: raise RuntimeError('Visual audit failed: '+', '.join(failed))
    return not failed


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--directory',default='output/ep01_phone_charger');parser.add_argument('--flag-only',action='store_true')
    args=parser.parse_args();audit(args.directory,strict=not args.flag_only)
