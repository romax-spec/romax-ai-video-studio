import subprocess, shutil, tempfile
from pathlib import Path
from .media import run
SIZES={"9:16":(1080,1920),"16:9":(1920,1080),"1:1":(1080,1080)}
def render(source:Path,dest:Path,project:dict):
    if not shutil.which("ffmpeg"): raise RuntimeError("FFmpeg not found.")
    aspect=project.get("aspect","9:16"); w,h=SIZES.get(aspect,SIZES["9:16"])
    quality=project.get("resolution","1080p")
    if quality=="720p": w,h=int(w*2/3),int(h*2/3)
    elif quality=="4K": w,h=w*2,h*2
    start=max(0,float(project.get("trimStart",0))); end=float(project.get("trimEnd",0))
    args=["ffmpeg","-y","-ss",str(start),"-i",str(source)]
    audio=project.get("audio")
    if audio and Path(audio).exists(): args += ["-i",audio]
    duration=max(.1,end-start) if end>start else None
    vf=f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1"
    filters=[vf]
    speed=float(project.get("speed",1) or 1)
    if .25<=speed<=4 and speed!=1: filters.append(f"setpts=PTS/{speed}")
    args += ["-vf",",".join(filters),"-c:v","libx264","-preset","veryfast","-crf","21","-pix_fmt","yuv420p"]
    if duration: args += ["-t",str(duration)]
    if audio and Path(audio).exists():
        vol=max(0,min(2,float(project.get("musicVolume",0.18))))
        args += ["-filter_complex",f"[1:a]volume={vol}[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2[a]","-map","0:v:0","-map","[a]"]
    else: args += ["-map","0:v:0","-map","0:a?"]
    args += ["-c:a","aac","-b:a","192k","-movflags","+faststart",str(dest)]
    run(args)
    return dest
