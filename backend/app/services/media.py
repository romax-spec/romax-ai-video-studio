import json, subprocess, shutil
from pathlib import Path
def run(args):
    p = subprocess.run(args, capture_output=True, text=True)
    if p.returncode: raise RuntimeError(p.stderr[-1800:] or "Media command failed")
    return p.stdout + "\n" + p.stderr
def probe(path: Path):
    if not shutil.which("ffprobe"): raise RuntimeError("FFprobe/FFmpeg is not installed. Install FFmpeg and add it to PATH.")
    data=json.loads(run(["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(path)]))
    v=next((s for s in data.get("streams",[]) if s.get("codec_type")=="video"),{})
    return {"duration":float(data.get("format",{}).get("duration",0) or 0),"width":int(v.get("width",0) or 0),"height":int(v.get("height",0) or 0),"fps":v.get("r_frame_rate","0/1")}
def scenes(path: Path):
    if not shutil.which("ffmpeg"): return []
    try:
        raw=run(["ffmpeg","-hide_banner","-i",str(path),"-vf","select='gt(scene,0.32)',showinfo","-an","-f","null","-"])
        import re
        return [{"time":float(x),"label":"Potential scene change","kind":"scene"} for x in re.findall(r"pts_time:([0-9.]+)",raw)]
    except Exception: return []
def transcribe(path: Path):
    from ..config import ENABLE_WHISPER, WHISPER_MODEL
    if not ENABLE_WHISPER:
        return {"available":False,"language":None,"segments":[],"message":"Transcription is off. Set ENABLE_WHISPER=true and install requirements-ai.txt to enable faster-whisper."}
    try:
        from faster_whisper import WhisperModel
        model=WhisperModel(WHISPER_MODEL, device="auto", compute_type="int8")
        segs, info=model.transcribe(str(path), language=None, word_timestamps=True, vad_filter=True)
        out=[]
        for seg in segs:
            words=getattr(seg,"words",None) or []
            if words:
                out.extend([{"start":w.start,"end":w.end,"text":w.word.strip(),"words":[w.word.strip()]} for w in words if w.word.strip()])
            else: out.append({"start":seg.start,"end":seg.end,"text":seg.text.strip(),"words":seg.text.strip().split()})
        return {"available":True,"language":info.language,"segments":out,"message":f"Detected language: {info.language}"}
    except Exception as e:
        return {"available":False,"language":None,"segments":[],"message":f"Whisper unavailable: {str(e)[:240]}"}
