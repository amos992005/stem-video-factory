"""Audit finished subtitled files; exclude the lower 20% from both metrics.

Motion: union of 6/255 adjacent-frame changes over every 2-second window at
5fps, using 320x180 grayscale. Composition: compare normalized 9x20 spatial
luminance maps for each contact-sheet frame i vs i+2; dim grid pixels are
excluded. Both are heuristics and cannot prove visual or editorial quality.
"""
import argparse
import subprocess
import json
from pathlib import Path
import numpy as np
from package_ep01 import FULL, SHORTS

FPS=5
WIDTH=320
HEIGHT=180
PIXEL_THRESHOLD=6
MIN_CHANGED=.025
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
    frame=np.where(frame>=24,frame,0)
    rows,cols=9,20
    tiles=np.array([[block.mean() if block.size else 0 for block in np.array_split(row,cols,axis=1)]
                    for row in np.array_split(frame,rows,axis=0)],dtype=np.float64).ravel()
    return tiles/(tiles.sum()+1e-9)


def composition_pairs(frames):
    if len(frames)<30: raise ValueError('Need 30 frames for composition audit')
    descriptors=[layout_descriptor(frame) for frame in frames[:30]]
    return [(i,i+2,float(np.abs(descriptors[i]-descriptors[i+2]).sum()/2)) for i in range(28)]


def contact_samples(decoded):
    n=len(decoded)
    if n<30: raise ValueError('Video is too short for a 30-frame contact sheet')
    return [decoded[min(n-1,int((i+.5)*n/30))] for i in range(30)]


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
    videos=[directory/(FULL+'.mp4')]+[directory/(name+'.mp4') for name in SHORTS.values()]
    contact_sheet(videos[0],directory/'visual_contact_sheet_16x9.png')
    contact_sheet(videos[1],directory/'visual_contact_sheet_short01.png',portrait=True)
    lines=['# Episode 01 motion and composition audit','','Method: 5 fps, 320×180 grayscale; '
           'adjacent-frame intensity change ≥6/255. Each overlapping 2-second window uses the union of changed pixels '
           'across 10 frame differences; windows slide by 0.2 seconds. The lower 20% is excluded so subtitles '
           'cannot make a static scene pass. Motion threshold: 2.5%. Composition compares normalized 9×20 coarse '
           'foreground-luminance maps of contact-sheet frames i and i+2, excluding the lower 20% and dark pixels '
           'below 24/255; minimum distance 0.22. These are heuristics, not proof of artistic quality.','','| Video | Minimum motion | Windows below 2.5% | Result |','|---|---:|---:|---|']
    failed=[];details=[]
    for video in videos:
        decoded=decode_frames(video)
        windows=motion_windows(decoded)
        bad=[(time,value) for time,value in windows if value<MIN_CHANGED]
        minimum=min(value for _,value in windows)
        lines.append(f'| {video.name} | {minimum*100:.2f}% | {len(bad)} / {len(windows)} | {"FAIL" if bad else "PASS"} |')
        if bad:
            failed.append(video.name+' (motion)')
            details.append(f'**{video.name} flagged window starts (seconds):** '+', '.join(f'{t:.1f}' for t,_ in bad[:100])+(' …' if len(bad)>100 else ''))
        if video==videos[0]:
            pairs=composition_pairs(contact_samples(decoded))
            bad_pairs=[(i,j,v) for i,j,v in pairs if v<MIN_DIVERSITY]
            details.append(f'**Contact-sheet composition:** minimum {min(v for _,_,v in pairs):.3f}; {len(bad_pairs)} / {len(pairs)} pairs below {MIN_DIVERSITY:.2f}: {"FAIL" if bad_pairs else "PASS"}.')
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
