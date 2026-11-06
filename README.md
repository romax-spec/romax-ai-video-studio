# ROMAX AI VIDEO STUDIO

A runnable, self-hosted AI-assisted short-form video editor starter. It includes a React/TypeScript editing workspace, FastAPI API, SQLite project persistence (PostgreSQL-ready schema path), FFmpeg rendering, optional faster-whisper transcription, editable captions, style presets, generated original sound effects, upload/render job status, and MP4 download.

> **Honest scope:** this is a working foundation, not a claim of parity with CapCut or a fully autonomous multimodal editing model. Scene/shot suggestions are deterministic FFmpeg/OpenCV analysis; transcription is real when `faster-whisper` is installed and its model is available. The editor requires a local FFmpeg binary. Authentication, cloud storage, GPU 4K and production-scale queue infrastructure are deployment extensions described below.

## Quick start (Docker)

1. Install Docker and Docker Compose.
2. Copy `.env.example` to `.env` and adjust `CORS_ORIGINS` if needed.
3. Run `docker compose up --build`.
4. Open http://localhost:5173.

The API docs are at http://localhost:8000/docs.

## Local development

### Backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Install FFmpeg and ensure `ffmpeg` and `ffprobe` are on PATH. Optional real speech recognition:
```bash
pip install -r requirements-ai.txt
```
Set `WHISPER_MODEL=small` (or `base` for faster CPU use). The first transcription downloads model weights. Sinhala (`si`), Tamil (`ta`) and English (`en`) are supported by Whisper's multilingual models; automatic language detection is enabled by default.

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Set `VITE_API_URL=http://localhost:8000` if the API is hosted elsewhere.

## Main workflow
1. Upload an MP4/MOV/WebM file. Uploads stream to disk and return a project ID.
2. Run Analyze. FFprobe extracts metadata; FFmpeg scene detection produces candidate cuts; optional faster-whisper produces timed transcript segments. Without the optional model, transcription is clearly marked unavailable rather than fabricated.
3. Choose Auto or one of ten styles. Recommendations are suggestions; original footage is retained.
4. Edit caption text, start/end times, style, aspect ratio, resolution, and audio mix.
5. Preview source video and timeline. Save project. Render a new MP4; source upload is never overwritten.
6. Download the completed MP4.

## API
- `POST /api/projects` multipart upload (`file`, optional `title`)
- `GET /api/projects`
- `GET /api/projects/{id}`
- `PATCH /api/projects/{id}` project JSON updates
- `POST /api/projects/{id}/analyze`
- `POST /api/projects/{id}/render`
- `GET /api/jobs/{job_id}`
- `GET /api/projects/{id}/download`
- `DELETE /api/projects/{id}`

## Environment
See `.env.example`. SQLite is the default for zero-setup local development. `DATABASE_URL` accepts a SQLAlchemy URL; install `psycopg[binary]` and use PostgreSQL for multi-user deployments. Do not expose this development server publicly without adding authentication, rate limits, private object storage, malware scanning, and per-user authorization.

## Production deployment checklist
- Add OIDC/Supabase Auth and enforce ownership in every project query.
- Move uploads and outputs to private S3-compatible storage with signed URLs and resumable multipart uploads.
- Replace in-process background tasks with Celery/RQ + Redis; run isolated FFmpeg workers with CPU/memory/time limits.
- Use managed PostgreSQL migrations (Alembic), backups, retention policies, and audit logs.
- Put API behind HTTPS reverse proxy; configure CORS, secrets, quotas, request-size limits, and observability.
- Add licensed music catalogue and user license records. Bundled SFX are generated original assets.
- For 4K, use a worker with sufficient disk, RAM and GPU/CPU; this app only checks FFmpeg availability and does not promise hardware capability.

## Tests
```bash
cd backend
pytest
```
Tests cover API project creation/listing and safe project update behavior. A real render/transcription test requires FFmpeg and, for transcription, the optional model weights. Run `python scripts/smoke_test.py` from the repository root after starting the API to exercise upload, analysis and rendering against a local clip.

## License
MIT for the application source. Generated SFX assets are original and may be used with this project. Users are responsible for rights to uploaded footage, fonts and external audio.
