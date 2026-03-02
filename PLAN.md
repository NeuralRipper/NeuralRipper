# NeuralRipper v2 - Final Implementation Plan (2-3 Days)

## Scope: What We Build vs What We Defer

### BUILD NOW (assignment + core product)
- Backend: FastAPI + SQLAlchemy + 4 tables + Google auth + JWT + WebSocket
- Frontend: React + shadcn/ui + 3 tabs (Playground, Results, About)
- Modal: reuse modal_handler, multi-model concurrent streaming
- Docker: docker-compose (local MySQL), Dockerfiles (backend, frontend, nginx)
- Deploy: RDS, ECR, EC2, Route53, SSL
- Infra repo: nightly workflow

### DEFER (post-assignment)
- lm-evaluation-harness benchmarks (MMLU, HellaSwag, etc.)
- CNN/Vision models
- Benchmark tables (latency_metrics, throughput_metrics, quality_metrics, system_metrics)
- Comparison page / radar charts
- Admin panel UI (seed models via script or Swagger)
- Rate limiting (trivial to add later, just a DB count query)
- Semantic Release + RC (bonus, do if time permits)
- Blog tutorial (write after everything works)

### WHY this scope works
The assignment needs: SPA + MySQL + Docker + CI/CD + Route53 + SSL.
The 7-min demo shows: user logs in → types prompt → 2-3 models respond simultaneously
with live metrics → results stored in MySQL → everyone can see all past results.
That's impressive and covers every requirement. Benchmarks are a feature addition, not
a structural change -- same DB, same frontend, just new backend endpoints + Modal functions.

---

## Database: 4 Tables

```sql
CREATE TABLE users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    google_id     VARCHAR(255) NOT NULL UNIQUE,
    email         VARCHAR(255) NOT NULL UNIQUE,
    name          VARCHAR(255),
    avatar_url    VARCHAR(500),
    is_admin      BOOLEAN DEFAULT FALSE,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE models (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(255) NOT NULL UNIQUE,     -- "Qwen2.5-0.5B"
    hf_model_id     VARCHAR(255) NOT NULL,            -- "Qwen/Qwen2.5-0.5B-Instruct"
    model_type      ENUM('llm','cnn') DEFAULT 'llm',
    parameter_count BIGINT,                           -- 500000000
    quantization    VARCHAR(20) DEFAULT 'FP16',
    description     TEXT,
    is_downloaded   BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE inference_sessions (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL,
    prompt      TEXT NOT NULL,
    model_ids   JSON NOT NULL,                        -- [1, 2, 3]
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_user_time (user_id, created_at)         -- for future rate limiting
);

CREATE TABLE inference_results (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    session_id        INT NOT NULL,
    model_id          INT NOT NULL,
    status            ENUM('pending','streaming','completed','failed') DEFAULT 'pending',
    response_text     TEXT,
    ttft_ms           FLOAT,          -- time to first token
    tpot_ms           FLOAT,          -- time per output token
    tokens_per_second FLOAT,
    total_tokens      INT,
    e2e_latency_ms    FLOAT,          -- end to end
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES inference_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (model_id) REFERENCES models(id)
);
```

Seed models via a Python script or Swagger UI POST -- no admin panel needed for now.

---

## Backend Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI app, lifespan, CORS, mount routers
│   ├── config.py                # Settings class (MySQL, JWT secret, Google client ID, Modal app name)
│   ├── database/
│   │   ├── connection.py        # create_engine, SessionLocal, get_db dependency
│   │   └── models.py           # 4 SQLAlchemy ORM classes
│   ├── auth/
│   │   ├── google.py            # verify_google_token() → {sub, email, name, picture}
│   │   ├── jwt.py               # create_token(), verify_token()
│   │   └── dependencies.py     # get_current_user() FastAPI Depends
│   ├── schemas/
│   │   ├── auth.py              # GoogleLoginRequest, TokenResponse
│   │   ├── model.py             # ModelResponse
│   │   └── inference.py         # SessionCreate, SessionResponse, ResultResponse
│   ├── routers/
│   │   ├── auth_router.py       # POST /auth/google, GET /auth/me
│   │   ├── model_router.py      # GET /models, GET /models/{id}, POST /models (admin)
│   │   └── inference_router.py  # POST /playground/sessions, GET /playground/sessions,
│   │                            # GET /playground/sessions/{id}, WS /ws/inference/{id}
│   ├── handlers/
│   │   ├── modal_handler.py     # [COPY FROM ARCHIVE] Modal streaming interface
│   │   └── inference_handler.py # run_session() with asyncio.gather, _stream_single_model()
│   └── evaluation/
│       └── modal_app.py         # [COPY FROM ARCHIVE] Modal app def (vLLM, HF download)
├── pyproject.toml               # fastapi, uvicorn, sqlalchemy, pymysql, PyJWT, google-auth, modal
├── Dockerfile
└── seed.py                      # Script to insert 2-3 models into DB
```

### File-by-File Guidance

**`app/main.py`** -- 6 things: create app, lifespan (init DB + modal_handler), CORS, mount 3 routers, health check.
```python
# Key pattern: lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.database.init import init_database
    init_database()                              # create_all tables
    app.state.modal_handler = ModalHandler()     # reuse from archive
    yield

app = FastAPI(default_response_class=ORJSONResponse, lifespan=lifespan)
# CORS, include_router x3, GET / health
```

**`app/config.py`** -- flat Settings class, all from env vars with defaults.
```python
class Settings:
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    # ... MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
    DATABASE_URL = property(...)   # mysql+pymysql://...
    JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-prod")
    JWT_EXPIRY_HOURS = 24
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    MODAL_APP_NAME = os.getenv("MODAL_APP_NAME", "neuralripper-inference")
```

**`app/database/connection.py`** -- 3 things: engine, SessionLocal, get_db generator.
```python
# Key: pool_pre_ping=True handles stale MySQL connections
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, pool_size=5)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db():          # FastAPI Depends(get_db)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**`app/database/models.py`** -- SQLAlchemy 2.0 style with `DeclarativeBase`, `Mapped`, `mapped_column`.
```python
# Key pattern:
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    google_id: Mapped[str] = mapped_column(String(255), unique=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    # ...
```

**`app/auth/google.py`** -- one function, ~10 lines.
```python
# pip install google-auth
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

def verify_google_token(token: str, client_id: str) -> dict:
    """Returns {"sub": "...", "email": "...", "name": "...", "picture": "..."}"""
    return id_token.verify_oauth2_token(token, google_requests.Request(), client_id)
    # Raises ValueError if token invalid/expired
```

**`app/auth/jwt.py`** -- two functions, ~15 lines.
```python
# pip install PyJWT
import jwt
from datetime import datetime, timedelta, timezone

def create_token(user_id: int, email: str, secret: str, hours: int = 24) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=hours),
    }
    return jwt.encode(payload, secret, algorithm="HS256")

def verify_token(token: str, secret: str) -> dict:
    return jwt.decode(token, secret, algorithms=["HS256"])
    # Raises jwt.ExpiredSignatureError, jwt.InvalidTokenError
```

**`app/auth/dependencies.py`** -- FastAPI dependency that extracts user from JWT.
```python
from fastapi import Header, HTTPException, Depends

async def get_current_user(
    authorization: str = Header(...),   # "Bearer <jwt>"
    db: Session = Depends(get_db),
) -> User:
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = verify_token(token, settings.JWT_SECRET)
    except Exception:
        raise HTTPException(401, "Invalid token")
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(401, "User not found")
    return user
```

**`app/routers/auth_router.py`** -- 2 endpoints.
```python
@router.post("/auth/google")
# 1. Receive {token: "google_id_token"} from frontend
# 2. verify_google_token(token) → {sub, email, name, picture}
# 3. Upsert user in DB (INSERT ... ON DUPLICATE KEY UPDATE)
# 4. create_token(user.id, user.email) → JWT
# 5. Return {access_token: jwt, user: {id, name, email, avatar_url}}

@router.get("/auth/me")
# 1. Depends(get_current_user) → user
# 2. Return user info
```

**`app/routers/model_router.py`** -- 2 endpoints for MVP (GET list, GET detail).
```python
@router.get("/models")           # Query all from DB, return list
@router.get("/models/{id}")      # Query one + its inference_results (JOIN)
```

**`app/routers/inference_router.py`** -- 3 endpoints (the core).
```python
@router.post("/playground/sessions")
# Depends(get_current_user) for auth
# Create inference_session + N inference_result rows
# Return {session_id: int}

@router.get("/playground/sessions")
# List all sessions with user info + result summaries, paginated
# No auth needed (public gallery)

@router.get("/playground/sessions/{id}")
# Full session detail with all results + metrics

@router.websocket("/ws/inference/{session_id}")
# Accept, load session from DB, resolve model names
# Call inference_handler.run_session() with asyncio.gather
# (detailed code already in plan v4 -- the full concurrent streaming flow)
```

**`app/handlers/modal_handler.py`** -- COPY from `archive/backend/app/handlers/modal_handler.py`.
Zero changes needed. It already provides `async stream_inference()` yielding tokens.

**`app/handlers/inference_handler.py`** -- the concurrent orchestrator.
Full code already in plan v4 above. Key methods:
- `run_session()` → `asyncio.create_task()` per model → `asyncio.gather()`
- `_stream_single_model()` → `async for token in modal_handler.stream_inference()` → websocket.send_json()
- `_save_result()` → UPDATE inference_results row with final metrics

**`app/evaluation/modal_app.py`** -- COPY from `archive/backend/app/utils/modal_deploy.py`.
This is the Modal-side code (runs on Modal GPU, not on our backend):
- Already has: `download_model_from_huggingface()`, vLLM `Model` class, `generate_stream()`
- Deploy separately with `modal deploy modal_app.py`
- No changes needed for MVP

**`seed.py`** -- run once to populate models table.
```python
# python seed.py
# Inserts: Qwen2.5-0.5B, Llama-3.2-1B, Phi-3-mini-4k (or whatever models you have on Modal)
```

### Dependencies (`pyproject.toml`)
```
fastapi, uvicorn, orjson           # web framework
sqlalchemy, pymysql, cryptography  # database
PyJWT, google-auth                 # auth
modal                              # GPU inference
```

---

## Frontend Structure

```
frontend/
├── src/
│   ├── main.tsx                      # ReactDOM.createRoot
│   ├── App.tsx                       # GoogleOAuthProvider + Layout with 3 tabs
│   ├── lib/
│   │   └── api.ts                    # fetch wrapper: auto-attaches JWT, base URL
│   ├── hooks/
│   │   ├── useAuth.ts                # Google login, JWT storage, user state
│   │   └── useInferenceSocket.ts     # WebSocket for streaming inference
│   ├── components/
│   │   ├── Layout.tsx                # Header (logo + login button) + Tabs container
│   │   ├── LoginButton.tsx           # Google Sign-In / user avatar dropdown
│   │   ├── Playground.tsx            # Prompt input + model checkboxes + streaming output
│   │   ├── Results.tsx               # DataTable of all past sessions + metrics
│   │   └── About.tsx                 # [COPY FROM ARCHIVE] Portfolio page
│   ├── components/ui/                # shadcn/ui generated components
│   │   ├── button.tsx, input.tsx, tabs.tsx, card.tsx,
│   │   ├── table.tsx, badge.tsx, avatar.tsx,
│   │   ├── dropdown-menu.tsx, dialog.tsx, checkbox.tsx
│   │   └── (generated via: npx shadcn@latest add button input tabs ...)
│   └── types/
│       └── index.ts                  # Model, Session, Result, User interfaces
├── package.json                      # react, react-dom, @react-oauth/google, recharts
├── tailwind.config.js
├── vite.config.ts
├── Dockerfile
└── index.html
```

### File-by-File Guidance

**`src/App.tsx`** -- wraps everything in GoogleOAuthProvider + 3 shadcn Tabs.
```tsx
import { GoogleOAuthProvider } from '@react-oauth/google';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

// 3 tabs: Playground, Results, About
// AuthProvider context wraps everything
// No react-router needed -- SPA with tabs
```

**`src/hooks/useAuth.ts`** -- core auth hook.
```tsx
// State: {user, token, isLoggedIn}
// login(googleCredential):
//   1. POST /auth/google with Google's credential.credential (ID token)
//   2. Receive {access_token, user}
//   3. Store token in localStorage
//   4. Set user state
// logout(): clear localStorage + state
// On mount: check localStorage for existing token, call GET /auth/me to validate
```
Reference: `@react-oauth/google` provides `<GoogleLogin onSuccess={credentialResponse => ...} />`
The `credentialResponse.credential` is the Google ID token string.

**`src/hooks/useInferenceSocket.ts`** -- WebSocket hook for streaming.
```tsx
// Input: sessionId (number | null)
// When sessionId changes and is not null:
//   1. Open WebSocket to ws://host/ws/inference/{sessionId}
//   2. On message: parse JSON, dispatch by type:
//      "token"           → append token to model's response buffer, update live metrics
//      "model_complete"  → mark model done, store final metrics
//      "model_error"     → mark model failed
//      "session_complete" → mark session done
//   3. On close: cleanup
// Output: {
//   modelResults: Map<string, {tokens: string[], metrics: LiveMetrics, status: string}>,
//   sessionStatus: 'idle' | 'streaming' | 'complete',
// }
```
Pattern reference: `archive/frontend/src/hooks/useEvalWebSocket.ts` (same idea, simpler message format)

**`src/components/Playground.tsx`** -- the core UI.
```
┌──────────────────────────────────────────────────────────────┐
│  Enter your prompt:                                          │
│  ┌────────────────────────────────────────────────┐ [Submit] │
│  │ Explain quantum computing in simple terms      │          │
│  └────────────────────────────────────────────────┘          │
│                                                              │
│  Models: ☑ Qwen2.5-0.5B  ☑ Llama-3.2-1B  ☐ Phi-3-mini     │
│                                                              │
│  ┌─── Qwen2.5-0.5B ────────┐  ┌─── Llama-3.2-1B ────────┐  │
│  │ Quantum computing is a   │  │ In simple terms,        │  │
│  │ type of computation...█  │  │ quantum computing...█   │  │
│  │                          │  │                         │  │
│  │ TTFT: 245ms              │  │ TTFT: 380ms             │  │
│  │ Speed: 42.3 tok/s        │  │ Speed: 28.1 tok/s       │  │
│  │ Tokens: 67               │  │ Tokens: 43              │  │
│  └──────────────────────────┘  └─────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```
Flow:
1. User types prompt, checks models, clicks Submit (requires login)
2. POST /playground/sessions → get session_id
3. useInferenceSocket(session_id) → WebSocket opens
4. Tokens arrive tagged by model → render in side-by-side cards
5. Live metrics update below each model's response
6. On complete, show final metrics

Built with: shadcn Card, Input, Button, Checkbox, Badge.
Streaming text: just a `<p>` that appends tokens as they arrive (state update per token).
Metrics: shadcn Badge or simple `<span>` elements.

**`src/components/Results.tsx`** -- DataTable of all past sessions.
```
┌────────────────────────────────────────────────────────────────────────┐
│  # │ User     │ Prompt              │ Models │ Fastest    │ Time      │
│────│──────────│─────────────────────│────────│────────────│───────────│
│ 42 │ Alice    │ Explain quantum...  │ 3      │ Qwen 42t/s │ 2 min ago │
│ 41 │ Bob      │ Write a poem about..│ 2      │ Llama 35t/s│ 5 min ago │
│ 40 │ Alice    │ What is DNA?        │ 3      │ Qwen 38t/s │ 1 hr ago  │
└────────────────────────────────────────────────────────────────────────┘
Click row → expand to see full prompt, all model responses, all metrics
```
Built with: shadcn DataTable (TanStack Table). Fetch from GET /playground/sessions.
Expandable rows show full detail from GET /playground/sessions/{id}.

**`src/components/About.tsx`** -- copy `archive/frontend/src/components/portfolio/Portfolio.tsx`,
strip v1-specific styling, wrap in a shadcn Card. Keep all personal content.

**`src/components/LoginButton.tsx`** -- Google Sign-In or user avatar.
```tsx
// If not logged in: <GoogleLogin onSuccess={...} /> from @react-oauth/google
// If logged in: <Avatar> with <DropdownMenu> showing name + Sign Out
```

**`src/lib/api.ts`** -- thin fetch wrapper.
```tsx
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function api<T>(path: string, options?: RequestInit): Promise<T> {
    const token = localStorage.getItem('token');
    const res = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...options?.headers,
        },
    });
    if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
    return res.json();
}
```

### Frontend Dependencies
```
react, react-dom                    # core
@react-oauth/google                 # Google Sign-In (one component)
tailwindcss, @tailwindcss/vite      # styling
class-variance-authority, clsx,     # shadcn/ui peer deps
tailwind-merge, lucide-react
@tanstack/react-table               # DataTable (shadcn uses this)
```

---

## Docker

**`backend/Dockerfile`:**
```dockerfile
FROM python:3.11-slim
# Install uv, copy pyproject.toml, uv sync --frozen, copy app/, CMD uvicorn
```

**`frontend/Dockerfile`:**
```dockerfile
FROM node:22-slim AS build
# npm install, npm run build (vite outputs to dist/)
FROM nginx:alpine
# Copy dist/ to /usr/share/nginx/html, copy nginx.conf for SPA fallback
# Or: use `npx serve dist` for simplicity
```

**`docker/Dockerfile.nginx`:**
```dockerfile
FROM nginx:alpine
# Copy nginx.conf, SSL certs mount, htpasswd if needed
```

**`docker/docker-compose.yml`** (local dev):
```yaml
services:
  mysql:
    image: mysql:8.0
    ports: ["3306:3306"]
    environment: { MYSQL_ROOT_PASSWORD: root, MYSQL_DATABASE: neuralripper,
                   MYSQL_USER: neuralripper, MYSQL_PASSWORD: dev }
    volumes: [mysql_data:/var/lib/mysql]
    healthcheck: {test: ["CMD", "mysqladmin", "ping"], interval: 10s, retries: 5}
  backend:
    build: {context: .., dockerfile: backend/Dockerfile}
    ports: ["8000:8000"]
    depends_on: {mysql: {condition: service_healthy}}
    environment:
      MYSQL_HOST: mysql
      MYSQL_USER: neuralripper
      MYSQL_PASSWORD: dev
      MYSQL_DATABASE: neuralripper
      JWT_SECRET: dev-secret
      GOOGLE_CLIENT_ID: ${GOOGLE_CLIENT_ID}
  frontend:
    build: {context: .., dockerfile: frontend/Dockerfile}
    ports: ["3000:3000"]
volumes:
  mysql_data:
```

**`docker/docker-compose.prod.yml`** (production -- ECR images, RDS):
```yaml
services:
  backend:
    image: public.ecr.aws/i5n9j8u1/neuralripper:backend
    environment:
      MYSQL_HOST: ${RDS_ENDPOINT}        # from Secrets Manager
      MYSQL_USER: ${RDS_USER}
      MYSQL_PASSWORD: ${RDS_PASSWORD}
      # ... JWT_SECRET, GOOGLE_CLIENT_ID from Secrets Manager
  frontend:
    image: public.ecr.aws/i5n9j8u1/neuralripper:frontend
  nginx:
    image: public.ecr.aws/i5n9j8u1/neuralripper:nginx
    ports: ["80:80", "443:443"]
    volumes:
      - /etc/letsencrypt:/etc/letsencrypt:ro
```

**`nginx.conf`:**
```nginx
# HTTP → HTTPS redirect
# SSL with Let's Encrypt certs
# / → frontend (port 3000)
# /api/ → backend (port 8000), with WebSocket upgrade headers
```

---

## Infra Repo

```
neuralripper-infra/
├── .github/workflows/
│   └── nightly.yml
├── scripts/
│   ├── smoke-test.sh
│   └── deploy.sh
└── README.md
```

**`nightly.yml`** -- 3 jobs:
1. **smoke-test**: launch temp EC2 → clone source repo → docker compose up → curl health endpoints → terminate
2. **build-push**: checkout source → docker build → push to ECR
3. **deploy-qa**: SSH into QA EC2 → docker pull → docker compose up

**`smoke-test.sh`:**
```bash
curl -f http://localhost:8000/           # backend health
curl -f http://localhost:8000/models     # API works
curl -f http://localhost:3000/           # frontend serves
```

---

## 3-Day Schedule

### Day 1: Backend + Database + Docker

**Morning: Scaffold + Database**
1. `git tag v1-archive && mkdir archive && mv backend frontend docker notebooks nginx.conf archive/`
2. Create `backend/` with FastAPI scaffold (main.py, config.py)
3. Create `backend/app/database/` (connection.py, models.py -- 4 ORM classes)
4. Create `docker/docker-compose.yml` with MySQL service
5. Create `backend/Dockerfile`
6. Verify: `docker compose up`, backend starts, tables created in MySQL

**Afternoon: Auth + API Endpoints**
7. Create `backend/app/auth/` (google.py, jwt.py, dependencies.py)
8. Create `backend/app/routers/auth_router.py` (POST /auth/google, GET /auth/me)
9. Create `backend/app/routers/model_router.py` (GET /models, GET /models/{id})
10. Create `backend/app/schemas/` (auth.py, model.py, inference.py)
11. Create `seed.py`, run it to insert 2-3 models
12. Create `backend/app/routers/inference_router.py`:
    - POST /playground/sessions (JWT required)
    - GET /playground/sessions (public)
    - GET /playground/sessions/{id} (public)
13. Verify: Swagger UI at :8000/docs, all endpoints return data

**Evening: Modal + WebSocket**
14. Copy `archive/backend/app/handlers/modal_handler.py` → `backend/app/handlers/`
15. Copy `archive/backend/app/utils/modal_deploy.py` → `backend/app/evaluation/modal_app.py`
16. Create `backend/app/handlers/inference_handler.py` (concurrent streaming)
17. Add WebSocket endpoint to inference_router.py
18. Wire inference_handler into main.py lifespan
19. Verify: create session via Swagger, connect WebSocket via Postman/websocat, tokens stream

### Day 2: Frontend + Integration

**Morning: Scaffold + Auth**
1. `npm create vite@latest frontend -- --template react-ts`
2. `npx shadcn@latest init` (setup Tailwind + shadcn)
3. `npx shadcn@latest add button input tabs card badge avatar dropdown-menu table checkbox`
4. `npm install @react-oauth/google @tanstack/react-table`
5. Create Google OAuth Client ID in Google Cloud Console
6. Create `src/lib/api.ts` (fetch wrapper)
7. Create `src/hooks/useAuth.ts` (Google login + JWT)
8. Create `src/components/LoginButton.tsx`
9. Create `src/App.tsx` with GoogleOAuthProvider + Tabs shell
10. Verify: Google login works, JWT stored, /auth/me returns user

**Afternoon: Playground + Results**
11. Create `src/hooks/useInferenceSocket.ts` (WebSocket hook)
12. Create `src/components/Playground.tsx`:
    - Fetch models from GET /models
    - Prompt input + model checkboxes + Submit button
    - On submit: POST /playground/sessions → open WebSocket → stream tokens
    - Side-by-side model cards with streaming text + live metrics
13. Create `src/components/Results.tsx`:
    - Fetch sessions from GET /playground/sessions
    - shadcn DataTable with columns: #, user, prompt, models, fastest, time
    - Click row to expand with full detail
14. Verify: full flow works -- login → prompt → streaming → results table

**Evening: About + Docker**
15. Copy Portfolio.tsx from archive, adapt styling to shadcn
16. Create `frontend/Dockerfile`
17. Create `docker/Dockerfile.nginx` + `nginx.conf`
18. Update `docker/docker-compose.yml` with all services
19. Verify: `docker compose up` runs full stack locally

### Day 3: Deployment + Infra

**Morning: AWS Setup**
1. Provision RDS MySQL (db.t3.micro, us-east-1)
2. Add RDS creds to Secrets Manager
3. Update Dockerfile.backend to fetch secrets at startup
4. Create `docker/docker-compose.prod.yml`
5. Build all images, push to ECR
6. Deploy on EC2 (3.224.99.183)
7. Verify: http://3.224.99.183 shows the app

**Afternoon: DNS + SSL + Infra Repo**
8. Route53: migrate neuralripper.com (update NS records at Name.com)
9. Certbot: `certbot certonly --standalone -d neuralripper.com -d www.neuralripper.com`
10. Update nginx.conf for SSL, restart
11. Verify: https://neuralripper.com works

12. Create `neuralripper-infra` repo on GitHub
13. Create `.github/workflows/nightly.yml`
14. Create `scripts/smoke-test.sh`, `scripts/deploy.sh`
15. Set GitHub secrets (AWS creds, SSH key)
16. Verify: trigger workflow manually

**Evening: Polish + (Bonus)**
17. Test full flow end-to-end on production
18. If time: semantic release + RC (bonus 25%)
19. If time: start blog tutorial

---

## Google Cloud Console Setup (5 min)

1. Go to https://console.cloud.google.com/apis/credentials
2. Create Project (or use existing)
3. Create OAuth 2.0 Client ID → Web Application
4. Authorized JavaScript origins:
   - `http://localhost:3000`
   - `http://localhost:5173`
   - `https://neuralripper.com`
5. No redirect URIs needed (using ID token flow, not authorization code)
6. Copy Client ID → set as `GOOGLE_CLIENT_ID` env var
7. No client secret needed for this flow

---

## Key Technical Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Auth | Google ID token flow (not auth code) | Simplest: no backend secret, no redirect URI, 10 lines of code |
| JWT | PyJWT HS256 | Simple symmetric signing, no RSA key management |
| ORM | SQLAlchemy 2.0 (Mapped/mapped_column) | Already in pyproject.toml, modern pattern |
| Frontend state | React hooks (useState/useEffect) | No Redux/Zustand needed for 3 tabs |
| WebSocket | One WS per session, messages tagged by model | Simple multiplexing, no per-model connections |
| Modal streaming | Reuse modal_handler as-is | Proven code, async generator pattern works |
| Admin | Swagger UI + seed script | No admin panel needed for MVP |
| Rate limiting | Defer | Just a COUNT query on inference_sessions -- add in 30 min when needed |
