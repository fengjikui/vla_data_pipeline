"""Source-clock causal PTS selection, without asserting measured hardware sync."""
import av
import numpy as np
from PIL import Image


def past_indices(frame_times,decision_times,max_age):
    frames=np.asarray(frame_times,dtype=float);times=np.asarray(decision_times,dtype=float)
    if not len(frames) or np.any(np.diff(frames)<=0):raise ValueError('Invalid video PTS sequence')
    ids=np.searchsorted(frames,times,side='right')-1
    if np.any(ids<0):raise ValueError('No past video frame for observation')
    if np.any(times-frames[ids]>max_age):raise ValueError('Video frame too stale')
    return ids


def decode_at(ep, indices, size=64):
    targets=ep.timestamps[indices]+ep.video_offset
    if ep.video_end is not None and np.any(targets>=ep.video_end+1e-6):raise ValueError('Observation exceeds v3 episode video boundary')
    # Tiny floating-point disagreements between encoded rational PTS and float32
    # source timestamps are limited to 1 microsecond, recorded in the recipe.
    tolerance=1e-6
    imgs=[];pts=[]
    with av.open(str(ep.video)) as container:
        stream=container.streams.video[0]
        container.seek(max(0,int((float(targets[0])-1)/float(stream.time_base))),stream=stream,backward=True,any_frame=False)
        last_pts=None;last_img=None;j=0
        for frame in container.decode(stream):
            if frame.pts is None:continue
            ts=float(frame.pts*frame.time_base)
            if ts < ep.video_offset-tolerance:continue
            if last_pts is not None and ts<=last_pts:raise ValueError('Non-increasing video timestamps')
            while j<len(targets) and targets[j]+tolerance<ts:
                if last_img is None:raise ValueError('No past frame in episode')
                imgs.append(last_img);pts.append(last_pts);j+=1
            if j==len(targets):break
            # Resize only a frame which can precede an anchor (small window <=1 frame).
            last_pts=ts
            last_img=np.asarray(frame.to_image().resize((size,size),Image.Resampling.BILINEAR))
        while j<len(targets):
            if last_img is None:raise ValueError('Empty video stream')
            imgs.append(last_img);pts.append(last_pts);j+=1
    ages=targets-np.asarray(pts)
    if np.any(ages < -tolerance) or np.any(ages>1.5/ep.fps):raise ValueError('Video timestamp alignment outside tolerance')
    return np.stack(imgs),np.asarray(pts),{'max_age_seconds':float(ages.max()),'min_age_seconds':float(ages.min()),'clock_assumption':'source common clock; physical latency not measured'}
