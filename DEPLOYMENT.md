# NeuroSim Web Platform — Production Deployment Guide

NeuroSim is a medical-grade EEG cognitive workload analytics platform featuring a Python API, real-time WebSocket telemetry hub, dual-engine PostgreSQL (Supabase) and SQLite persistence, and a high-performance clinical frontend.

This guide details our recommended **Decoupled Cloud Architecture**:
- **Frontend**: **Vercel** (Global Edge CDN, Instant Static Deploys, Auto HTTPS)
- **Backend**: **Railway** (Python API Gateway, WebSocket Telemetry Hub, Container Runtime)
- **Database**: **Supabase** (Hosted PostgreSQL, 21 CFR Part 11 Audit Trail, Connection Pooling)

---

## Architecture Overview

```
   [ Vercel Edge CDN ] ──── (Clinical Frontend: HTML5 / Canvas / WebAudio / PWA)
           │
           │  HTTPS API Calls (/api/*) & Secure WebSockets (/ws)
           ▼
   [ Railway Cloud Container ] ──── (Nginx Reverse Proxy on $PORT)
           ├── /ws  ────────▶ [ WebSocket Streaming Hub :8765 ]
           └── /api ────────▶ [ Python 3.11 FastAPI / HTTP Server :8001 ]
                                      │
                                      ▼
                        [ Supabase Cloud Database ]
                   (PostgreSQL with Pooled Connections & RLS)
                   (Automatic fallback to SQLite WAL if offline)
```

---

## Quick Deployment (3 Simple Steps)

### Step 1: Create Supabase PostgreSQL Database

1. Sign up or log in at [supabase.com](https://supabase.com).
2. Click **New Project**, choose a name (e.g. `neurosim-db`), set a database password, and select your nearest region.
3. Once provisioned, open the **SQL Editor** from the left navigation.
4. Open [`supabase_schema.sql`](supabase_schema.sql) in this repository, copy its entire contents, paste it into the Supabase SQL editor, and click **Run**.
5. Go to **Project Settings** → **Database** → **Connection String**:
   - Select **URI** and **Session pooler** (or Transaction pooler on port `6543`).
   - Copy the URI string:
     ```
     postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
     ```
   - Replace `[YOUR-PASSWORD]` with your actual database password. Keep this string ready for Step 2.

---

### Step 2: Deploy Backend to Railway

Railway runs our hardened container containing the Python API, WebSocket telemetry relay, and DSP classification engine.

1. Sign up or log in at [railway.app](https://railway.app).
2. Click **New Project** → **Deploy from GitHub repo**.
3. Select your repository (`Barathwaj2006/Brain-Computer-Interface---Cognitive-Load-Analysis`).
4. Railway automatically detects [`Dockerfile`](Dockerfile) and [`railway.json`](railway.json).
5. Click on the newly created service → **Variables**:
   - Add variable: `SUPABASE_DB_URL`
   - Value: Paste your Supabase connection string from Step 1.
   - *(Optional)* Add variable: `PORT` with value `8000` (Railway injects this automatically if omitted).
6. Go to **Settings** → **Networking** → Click **Generate Domain**.
7. Copy your public Railway backend URL (e.g. `https://neurosim-production.up.railway.app`).
8. Verify health: Open `https://<your-railway-domain>/api/health` in your browser. You should see:
   ```json
   {
     "status": "healthy",
     "database": {
       "engine": "PostgreSQL (Supabase)",
       "status": "connected"
     }
   }
   ```

---

### Step 3: Deploy Frontend to Vercel

Vercel serves the clinical dashboard with sub-millisecond edge latency and global SSL.

1. Sign up or log in at [vercel.com](https://vercel.com).
2. Click **Add New...** → **Project**.
3. Import your GitHub repository.
4. In the Project Configuration:
   - **Framework Preset**: Leave as `Other` (Static Site).
   - **Root Directory**: `.` (Default). Vercel reads [`vercel.json`](vercel.json) which automatically sets `"outputDirectory": "web"`.
5. Click **Deploy**.
6. Once deployed, open your live Vercel URL (e.g. `https://neurosim.vercel.app`).
7. **Connect Frontend to Backend**:
   - In the top status bar, click the **☁️ CLOUD** button.
   - Paste your Railway backend URL (e.g. `https://neurosim-production.up.railway.app`).
   - Click **TEST PING** to verify real-time latency and database connectivity.
   - Click **Save & Connect**.
   - Your frontend will now stream live biopotentials and sync all patient records directly to Supabase via Railway!

---

## Alternative Deployment Options

### Option A: 1-Click Cloud on Render.com
Render builds our multi-process Docker container directly from [`render.yaml`](render.yaml):
1. Sign in to [render.com](https://render.com).
2. Click **New +** → **Blueprint** → Select repository.
3. Add environment variable `SUPABASE_DB_URL` under service settings.
4. Click **Apply**.

### Option B: Self-Hosted Docker / VPS
For clinical environments, university laboratories, or local hospital networks:
```bash
git clone https://github.com/Barathwaj2006/Brain-Computer-Interface---Cognitive-Load-Analysis.git neurosim
cd neurosim

# Run container with volume persistence & port mapping
docker compose up -d --build
```
- Clinical Dashboard: `http://localhost:8000`
- API Health Check: `http://localhost:8000/api/health`
- WebSocket Telemetry Hub: `ws://localhost:8000/ws`
- Hardware UDP Ingest: Port `5005` (UDP)

### Option C: Instant Tunnel via Cloudflare (Zero Port Forwarding)
If running locally on your laptop with real ESP32 Wi-Fi hardware:
```powershell
# Terminal 1:
python server.py --no-browser

# Terminal 2:
cloudflared tunnel --url http://localhost:8000
```
Open the generated `https://xxxx.trycloudflare.com` on any smartphone or tablet.

---

## Environment Variables Reference

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `SUPABASE_DB_URL` | *(none)* | Supabase / PostgreSQL pooled connection string. When omitted, falls back to SQLite WAL mode. |
| `DATABASE_URL` | *(none)* | Standard PostgreSQL connection string (alias for `SUPABASE_DB_URL`). |
| `PORT` | `8000` | Public port exposed by Nginx in the container (automatically assigned by Railway/Render). |
| `INTERNAL_HTTP_PORT` | `8001` | Internal Python HTTP server port within container. |
| `WS_PORT` | `8765` | Internal WebSocket telemetry hub port. |
| `UDP_PORT` | `5005` | ESP32 hardware UDP telemetry datagram port. |

---

## Database Architecture & Compliance

- **Dual-Engine Auto-Detection**: If `SUPABASE_DB_URL` is set, NeuroSim transparently uses PostgreSQL. If the cloud database is temporarily unreachable, it gracefully falls back to local SQLite with WAL journaling to prevent data loss.
- **21 CFR Part 11 Audit Trail**: All authentication events, session creations, and overrides generate an immutable SHA-256 Merkle hash chain.
- **Verification Endpoint**: `GET /api/audit/verify` cryptographically audits all records from genesis and reports any tampering attempts.
- **Atomic Backups**: `GET /api/backup` exports a full database snapshot (JSON for Supabase PostgreSQL, `.db` binary for SQLite).
