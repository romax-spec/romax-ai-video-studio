import uuid, json, shutil, asyncio
from pathlib import Path
from datetime import datetime, timezone
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from .config import UPLOAD_DIR, OUTPUT_DIR, MAX_UPLOAD_MB, CORS_ORIGINS
from .db import Base, engine, get_db
from .models import Project
from .schemas import ProjectUpdate, RenderRequest
from .services.media import probe, scenes, transcribe
from .services.render import render
Base.metadata.create_all(bind=engine)
app=FastAPI(title="ROMAX AI VIDEO STUDIO API", version="1.0.0")
app.add_middleware(CORSMiddleware,allow_origins=CORS_ORIGINS,allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
JOBS={}
def serialize(p):
    return {"id":p.id,"title":p.title,"status":p.status,"duration":p.duration,"width":p.width,"height":p.height,"createdAt":p.created_at.isoformat(),"updatedAt":p.updated_at.isoformat(),"project":json.loads(p.project_json or "{}"),"hasExport":bool(p.output_path and Path(p.output_path).exists())}
@app.get("/api/health")
def health(): return {"ok":True,"ffmpeg":bool(shutil.which("ffmpeg"))}
@app.post("/api/projects")
async def create_project(file:UploadFile=File(...),title:str=Form("Untitled edit"),db:Session=Depends(get_db)):
    ext=Path(file.filename or "clip.mp4").suffix.lower()
    if ext not in {".mp4",".mov",".m4v",".webm",".mkv"}: raise HTTPException(400,"Upload MP4, MOV, M4V, WebM or MKV.")
    pid=str(uuid.uuid4()); dest=UPLOAD_DIR/f"{pid}{ext}"; size=0
    try:
        with dest.open("wb") as out:
            while chunk:=await file.read(1024*1024):
                size+=len(chunk)
                if size>MAX_UPLOAD_MB*1024*1024: raise HTTPException(413,"Upload exceeds configured size limit.")
                out.write(chunk)
        meta=probe(dest)
        p=Project(id=pid,title=title or "Untitled edit",source_path=str(dest),duration=meta["duration"],width=meta["width"],height=meta["height"],project_json=json.dumps({"aspect":"9:16","resolution":"1080p","style":"Viral TikTok","captions":[],"trimStart":0,"trimEnd":meta["duration"],"speed":1}))
        db.add(p); db.commit(); db.refresh(p)
        return {**serialize(p),"metadata":meta}
    except HTTPException: dest.unlink(missing_ok=True); raise
    except Exception as e: dest.unlink(missing_ok=True); raise HTTPException(400,str(e))
@app.get("/api/projects")
def list_projects(db:Session=Depends(get_db)):
    return [serialize(p) for p in db.query(Project).order_by(Project.updated_at.desc()).all()]
@app.get("/api/projects/{pid}")
def get_project(pid:str,db:Session=Depends(get_db)):
    p=db.get(Project,pid)
    if not p: raise HTTPException(404,"Project not found")
    return serialize(p)
@app.patch("/api/projects/{pid}")
def update_project(pid:str,payload:ProjectUpdate,db:Session=Depends(get_db)):
    p=db.get(Project,pid)
    if not p: raise HTTPException(404,"Project not found")
    if payload.title is not None: p.title=payload.title[:240]
    if payload.project is not None: p.project_json=json.dumps(payload.project)
    p.updated_at=datetime.now(timezone.utc); db.commit(); db.refresh(p); return serialize(p)
@app.post("/api/projects/{pid}/analyze")
async def analyze(pid:str,background:BackgroundTasks,db:Session=Depends(get_db)):
    p=db.get(Project,pid)
    if not p: raise HTTPException(404,"Project not found")
    jid=str(uuid.uuid4()); JOBS[jid]={"status":"running","progress":5,"message":"Inspecting footage"}
    background.add_task(run_analysis,pid,jid)
    return {"jobId":jid}
def run_analysis(pid,jid):
    from .db import SessionLocal
    db=SessionLocal()
    try:
        p=db.get(Project,pid); meta=probe(Path(p.source_path)); cut=scenes(Path(p.source_path)); speech=transcribe(Path(p.source_path))
        data=json.loads(p.project_json or "{}"); data.update({"analysis":{"metadata":meta,"scenes":cut,"transcription":speech,"recommendations":[{"title":"Review scene changes","detail":f"{len(cut)} possible scene changes detected."},{"title":"Choose a short-form hook","detail":"Review the first 3–5 seconds and keep the strongest opening moment."},{"title":"Keep source footage intact","detail":"Suggested trims are non-destructive until you export."}]}})
        if speech["available"]: data["captions"]=speech["segments"]
        p.project_json=json.dumps(data); p.status="analyzed"; p.updated_at=datetime.now(timezone.utc); db.commit()
        JOBS[jid]={"status":"completed","progress":100,"message":"Analysis ready","result":data["analysis"]}
    except Exception as e: JOBS[jid]={"status":"failed","progress":100,"message":str(e)}
    finally: db.close()
@app.get("/api/jobs/{jid}")
def get_job(jid:str):
    if jid not in JOBS: raise HTTPException(404,"Job not found")
    return JOBS[jid]
@app.post("/api/projects/{pid}/render")
def start_render(pid:str,payload:RenderRequest,background:BackgroundTasks,db:Session=Depends(get_db)):
    p=db.get(Project,pid)
    if not p: raise HTTPException(404,"Project not found")
    jid=str(uuid.uuid4()); JOBS[jid]={"status":"queued","progress":0,"message":"Queued for rendering"}
    background.add_task(run_render,pid,jid,payload.project or json.loads(p.project_json or "{}"))
    return {"jobId":jid}
def run_render(pid,jid,data):
    from .db import SessionLocal
    db=SessionLocal()
    try:
        p=db.get(Project,pid); JOBS[jid]={"status":"running","progress":10,"message":"Rendering MP4"}
        dest=OUTPUT_DIR/f"{pid}-{jid[:8]}.mp4"; render(Path(p.source_path),dest,data)
        p.output_path=str(dest); p.status="exported"; p.updated_at=datetime.now(timezone.utc); db.commit()
        JOBS[jid]={"status":"completed","progress":100,"message":"Export complete"}
    except Exception as e: JOBS[jid]={"status":"failed","progress":100,"message":str(e)}
    finally: db.close()
@app.get("/api/projects/{pid}/source")
def source_video(pid:str,db:Session=Depends(get_db)):
    p=db.get(Project,pid)
    if not p or not Path(p.source_path).exists(): raise HTTPException(404,"Source video not found")
    return FileResponse(p.source_path,media_type="video/mp4")
@app.get("/api/projects/{pid}/download")
def download(pid:str,db:Session=Depends(get_db)):
    p=db.get(Project,pid)
    if not p or not p.output_path or not Path(p.output_path).exists(): raise HTTPException(404,"No completed export found")
    return FileResponse(p.output_path,media_type="video/mp4",filename=f"romax-{pid[:8]}.mp4")
@app.delete("/api/projects/{pid}")
def delete_project(pid:str,db:Session=Depends(get_db)):
    p=db.get(Project,pid)
    if not p: raise HTTPException(404,"Project not found")
    for path in [p.source_path,p.output_path]:
        if path: Path(path).unlink(missing_ok=True)
    db.delete(p); db.commit(); return {"deleted":True}
