"""Create contact sheets and measure motion on every overlapping 2-second window.

Video is sampled at 5 fps in grayscale at 320x180. A pixel is marked changed if
its intensity differs by at least 6/255 in *consecutive sampled frames*. For a
2-second window we report the union of marked pixel positions over its ten
frame differences, divided by the frame pixel count. Windows slide by 0.2 s.
This is a reproducible proxy for motion, not a judgment of artistic quality.
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
MIN_CHANGED=.01


def motion_windows(frames, fps=FPS, pixel_threshold=PIXEL_THRESHOLD):
    frames=np.asarray(frames,dtype=np.uint8)
    if frames.ndim != 3 or len(frames) < 2*fps+1:
        raise ValueError('at least 2 seconds plus one frame are required')
    diffs=np.abs(frames[1:].astype(np.int16)-frames[:-1].astype(np.int16))>=pixel_threshold
    n=2*fps
    windows=[]
    for i in range(len(diffs)-n+1):
        changed=np.logical_or.reduce(diffs[i:i+n],axis=0)
        windows.append((i/fps,float(changed.mean())))
    return windows


def duration(path):
    data=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(path)]))
    return float(data['format']['duration'])


def decode_frames(path):
    cmd=['ffmpeg','-v','error','-i',str(path),'-vf',f'fps={FPS},scale={WIDTH}:{HEIGHT},format=gray','-f','rawvideo','-']
    p=subprocess.run(cmd,check=True,stdout=subprocess.PIPE)
    unit=WIDTH*HEIGHT
    if len(p.stdout)%unit: raise ValueError(f'incomplete decoded frame: {path}')
    return np.frombuffer(p.stdout,dtype=np.uint8).reshape(-1,HEIGHT,WIDTH)


def contact_sheet(path, dest, portrait=False):
    length=duration(path)
    dimensions='270:480' if portrait else '480:270'
    # 30 evenly spaced presentation timestamps; first and last are near the ends.
    vf=f'fps=30/{length},scale={dimensions}:flags=lanczos,tile=5x6:nb_frames=30'
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(path),'-vf',vf,'-frames:v','1','-update','1',str(dest)],check=True)
    if not Path(dest).is_file(): raise RuntimeError(f'Could not create {dest}')


def audit(directory, strict=True):
    directory=Path(directory)
    videos=[directory/(FULL+'.mp4')]+[directory/(name+'.mp4') for name in SHORTS.values()]
    contact_sheet(videos[0],directory/'visual_contact_sheet_16x9.png')
    contact_sheet(videos[1],directory/'visual_contact_sheet_short01.png',portrait=True)
    lines=['# Episode 01 motion audit','','Method: 5 fps, 320×180 grayscale, adjacent-frame intensity change ≥6/255. '
           'Each 2-second window uses the union of changed pixels across its 10 consecutive frame differences. '
           'Windows slide by 0.2 seconds. Threshold: at least 1% of frame pixels. '
           'The metric detects static frames; it does not establish visual quality.','','| Video | Minimum | Windows below 1% | Result |','|---|---:|---:|---|']
    failed=[]
    for video in videos:
        windows=motion_windows(decode_frames(video))
        bad=[(time,value) for time,value in windows if value<MIN_CHANGED]
        minimum=min(value for _,value in windows)
        lines.append(f'| {video.name} | {minimum*100:.2f}% | {len(bad)} / {len(windows)} | {"FAIL" if bad else "PASS"} |')
        if bad:
            failed.append(video.name)
            lines.append('')
            lines.append(f'**{video.name} flagged window starts (seconds):** '+', '.join(f'{t:.1f}' for t,_ in bad[:100]))
            if len(bad)>100: lines.append(f'... and {len(bad)-100} more.')
            lines.append('')
    report=directory/'motion_audit_report.md'
    report.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(report.read_text(),flush=True)
    if failed and strict: raise RuntimeError('Motion audit failed: '+', '.join(failed))
    return not failed


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--directory',default='output/ep01_phone_charger');parser.add_argument('--flag-only',action='store_true')
    args=parser.parse_args();audit(args.directory,strict=not args.flag_only)
