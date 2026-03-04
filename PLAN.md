# NeuralRipper v2 - Implementation Plan

## Scope: What We Build vs What We Defer

### BUILD NOW (assignment + core product)
- Backend: FastAPI + SQLAlchemy + 4 tables + Google auth + JWT + WebSocket
- Frontend: React + shadcn/ui + 3 tabs (Playground, Results, About)
- Modal: modal_handler, multi-model concurrent inference
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

---

## Database: 4 Tables — DONE

All 4 SQLAlchemy ORM models implemented in `backend/db/`.

| File | Table | Status |
|------|-------|--------|
| `db/user.py` | `users` | DONE |
| `db/models.py` | `models` | DONE |
| `db/inference_session.py` | `inference_sessions` | DONE |
| `db/inference_result.py` | `inference_results` | DONE |
| `db/base.py` | DeclarativeBase | DONE |
| `db/connection.py` | async engine factory | DONE |

---

## Backend Structure — DONE (except WebSocket upgrade)

```
backend/
├── main.py                     # FastAPI app, lifespan, CORS, mount routers      ✅
├── settings.py                 # MySQL, JWT, Google client ID                    ✅
├── Dockerfile                  # python:3.11-slim + uv                          ✅
├── pyproject.toml              # all dependencies                                ✅
├── db/
│   ├── base.py                 # DeclarativeBase                                 ✅
│   ├── connection.py           # async engine factory                            ✅
│   ├── user.py                 # User ORM                                        ✅
│   ├── models.py               # Model ORM                                       ✅
│   ├── inference_session.py    # InferenceSession ORM                            ✅
│   └── inference_result.py     # InferenceResult ORM                             ✅
├── dependencies/
│   ├── auth.py                 # get_current_user (JWT Bearer)                   ✅
│   └── db.py                   # get_session (async session per request)         ✅
├── schemas/
│   ├── auth.py                 # GoogleLoginRequest, TokenResponse, UserInfo     ✅
│   ├── user.py                 # UserCreate, UserResponse                        ✅
│   ├── model.py                # ModelResponse                                   ✅
│   └── inference.py            # InferenceCreate, *Response schemas              ✅
├── routes/
│   ├── auth.py                 # POST /auth/google, GET /auth/me                 ✅
│   ├── user.py                 # POST /users                                     ✅
│   ├── model.py                # GET /models, GET /models/{id}                   ✅
│   └── inference.py            # POST/GET + SSE → needs WebSocket upgrade        🔧
├── handlers/
│   └── modal.py                # background Modal caller → needs WebSocket push  🔧
├── evaluation/
│   └── modal.py                # Modal GPU app (vLLM, A10G)                      ✅
└── tests/                      # integration tests                               ✅
```

### Backend API Endpoints — Current State

| Method | Path | Auth | Status |
|--------|------|------|--------|
| POST | `/auth/google` | No | DONE |
| GET | `/auth/me` | JWT | DONE |
| POST | `/users/` | No | DONE |
| GET | `/models/` | No | DONE |
| GET | `/models/{model_id}` | No | DONE |
| POST | `/inference/` | JWT | DONE |
| GET | `/inference/sessions` | No | DONE |
| GET | `/inference/sessions/{id}` | No | DONE |
| ~~GET~~ | ~~`/inference/{id}/stream`~~ | ~~JWT~~ | REMOVE (SSE, replaced by WebSocket) |
| WS | `/ws/inference/{session_id}` | JWT (first message) | **TODO** |

---

## Backend Change: SSE → WebSocket

### Why WebSocket over SSE

1. **Auth**: `EventSource` API cannot set custom headers — JWT has to go in query string (leaks into logs). WebSocket sends JWT as first message after connect.
2. **No DB polling**: current SSE polls MySQL every 1s. WebSocket pushes results directly the moment Modal returns. Zero wasted queries.
3. **Future token streaming**: when Modal's `run_inference` is upgraded to stream tokens, WebSocket can forward each token live. SSE + DB polling can't do per-token streaming without writing every token to DB.

### What to Change (2 files)

#### File 1: `routes/inference.py`

**Remove**: the `stream_results` SSE endpoint (lines 130-166)

**Add**: a WebSocket endpoint

```
@router.websocket("/ws/inference/{session_id}")
```

**Flow**:
1. Accept the WebSocket connection
2. Wait for the first message: `{"token": "Bearer <jwt>"}`
3. Verify JWT — if invalid, send `{"type": "error", "message": "..."}` and close
4. Load the session from DB, verify it belongs to this user
5. Load all InferenceResult rows for this session
6. For each result, `asyncio.create_task()` a function that:
   - Calls `run_modal_inference(result_id, model_id, prompt)`
   - When Modal returns, sends the result over the WebSocket
   - Saves the final result to DB
7. `asyncio.gather()` all tasks
8. Send `{"type": "session_complete"}`
9. Close WebSocket

**WebSocket message format** (server → client):
```json
{"type": "model_start",    "model_id": 1, "model_name": "Qwen2.5-0.5B"}
{"type": "model_complete", "model_id": 1, "result": {full InferenceResultResponse}}
{"type": "model_error",    "model_id": 1, "message": "..."}
{"type": "session_complete"}
```

#### File 2: `handlers/modal.py`

**Change**: `run_modal_inference` currently creates its own DB engine and runs as a fire-and-forget background task. Refactor it to:
- Accept a WebSocket parameter
- Push the result directly through the WebSocket when Modal returns
- Still save to DB (for the Results tab history)
- Return instead of fire-and-forget (the WebSocket endpoint orchestrates via asyncio.gather)

**New signature**:
```python
async def run_modal_inference(
    result_id: int,
    model_id: int,
    prompt: str,
    websocket: WebSocket,     # NEW: push results directly
    db_session: AsyncSession,  # NEW: reuse the WS endpoint's session
)
```

The handler does:
1. Look up model's `hf_model_id` from DB
2. Send `{"type": "model_start", "model_id": ..., "model_name": ...}` via WebSocket
3. Call `run_inference.remote(hf_model_id, prompt)` on Modal
4. When Modal returns: send `{"type": "model_complete", "model_id": ..., "result": {...}}` via WebSocket
5. Update InferenceResult row in DB with response + metrics
6. On error: send `{"type": "model_error", ...}` via WebSocket, mark DB row as failed

#### Also update: `routes/inference.py` POST `/inference/`

Currently the POST endpoint fires `asyncio.create_task(run_modal_inference(...))` as fire-and-forget (line 69). This no longer makes sense because the WebSocket now orchestrates Modal calls.

**Change POST to only**:
1. Create InferenceSession row
2. Create N InferenceResult rows (all `pending`)
3. Return `{session_id, result_ids}` — do NOT fire Modal tasks

The WebSocket endpoint takes over from here.

#### Update: `main.py`

Add `websockets` support — FastAPI has it built-in, but make sure CORS/allowed origins cover WebSocket upgrade. No code change needed for FastAPI, but nginx config (later) must proxy WebSocket with `Upgrade` headers.

---

## Frontend Structure

```
frontend/
├── index.html
├── package.json
├── vite.config.ts
├── .env                             # VITE_API_BASE_URL, VITE_GOOGLE_CLIENT_ID
├── Dockerfile
├── src/
│   ├── main.tsx                     # ReactDOM.createRoot, import global CSS
│   ├── App.tsx                      # GoogleOAuthProvider + AuthProvider + Layout
│   ├── lib/
│   │   ├── utils.ts                 # cn() helper (created by shadcn init)
│   │   └── api.ts                   # fetch wrapper with auto JWT
│   ├── hooks/
│   │   ├── useAuth.ts               # Google login, JWT storage, user state
│   │   └── useInferenceSocket.ts    # WebSocket hook for streaming inference
│   ├── components/
│   │   ├── Layout.tsx               # Header + Tabs container
│   │   ├── LoginButton.tsx          # Google Sign-In / user avatar dropdown
│   │   ├── Playground.tsx           # Prompt + model selection + streaming output
│   │   ├── Results.tsx              # DataTable of all past sessions
│   │   └── About.tsx               # Portfolio / about page
│   ├── components/ui/               # shadcn/ui generated (button, card, tabs, etc.)
│   └── types/
│       └── index.ts                 # User, Model, Session, Result interfaces
```

### Frontend File-by-File Guidance

**`src/types/index.ts`** — TypeScript interfaces matching backend schemas exactly.
```
User          { id, email, name, avatar_url }
Model         { id, name, hf_model_id, model_type, parameter_count, quantization, description, is_downloaded }
InferenceResult { id, model_id, status, response_text, ttft_ms, tpot_ms, tokens_per_second, total_tokens, e2e_latency_ms }
Session       { id, user_name, user_avatar, prompt, model_ids, created_at }
SessionDetail { ...Session, results: InferenceResult[] }

// WebSocket message types (server → client)
WsModelStart    { type: "model_start", model_id, model_name }
WsModelComplete { type: "model_complete", model_id, result: InferenceResult }
WsModelError    { type: "model_error", model_id, message }
WsSessionDone   { type: "session_complete" }
WsMessage = WsModelStart | WsModelComplete | WsModelError | WsSessionDone
```

**`src/lib/api.ts`** — thin fetch wrapper.
- Reads `VITE_API_BASE_URL` from env (default `http://localhost:8000`)
- Auto-attaches `Authorization: Bearer <token>` from localStorage
- Throws on non-OK responses with status + body
- Export named functions:
  - `googleLogin(credential)` → POST `/auth/google`
  - `getMe()` → GET `/auth/me`
  - `getModels()` → GET `/models/`
  - `createSession(prompt, modelIds)` → POST `/inference/`
  - `getSessions()` → GET `/inference/sessions`
  - `getSessionDetail(id)` → GET `/inference/sessions/{id}`

**`src/hooks/useAuth.ts`** — auth context + hook.
- `AuthProvider` component wraps the app, provides context
- State: `user` (User | null), `token` (string | null), `loading` (boolean)
- `login(googleCredential)`:
  1. POST `/auth/google` with the credential
  2. Receive `{access_token, token_type, user}`
  3. Store `access_token` in localStorage
  4. Set user + token state
- `logout()`: clear localStorage + state
- On mount (useEffect): check localStorage for token → call `getMe()` → if valid set user, if 401 clear

**`src/hooks/useInferenceSocket.ts`** — WebSocket hook.
- Input: `sessionId` (number | null), `token` (string | null)
- State: `modelResults` (Map<number, { name, status, result }>), `sessionStatus` ('idle' | 'streaming' | 'complete')
- When sessionId is set and not null:
  1. Open WebSocket: `new WebSocket(ws://host/ws/inference/{sessionId})`
  2. `onopen`: send `{"token": "Bearer <jwt>"}` as first message
  3. `onmessage`: parse JSON, dispatch by `type`:
     - `model_start` → add model to map with status `streaming`
     - `model_complete` → update model with result + status `completed`
     - `model_error` → update model with error + status `failed`
     - `session_complete` → set sessionStatus to `complete`
  4. `onclose` / `onerror`: cleanup
- Cleanup: close WebSocket on unmount or when sessionId changes
- Output: `{ modelResults, sessionStatus }`

**`src/components/Layout.tsx`** — app shell.
- Header: project title/logo on left, `<LoginButton>` on right
- Body: shadcn `<Tabs defaultValue="playground">`
  - `<TabsTrigger value="playground">` Playground
  - `<TabsTrigger value="results">` Results
  - `<TabsTrigger value="about">` About
  - Each `<TabsContent>` renders the corresponding component

**`src/components/LoginButton.tsx`** — two states.
- Not logged in: `<GoogleLogin onSuccess={...} />` from `@react-oauth/google`
- Logged in: shadcn `<Avatar>` with user pic, inside `<DropdownMenu>` with name + Sign Out

**`src/components/Playground.tsx`** — the core feature.
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
│  │ type of computation that │  │ quantum computing...     │  │
│  │ uses quantum mechanics   │  │                         │  │
│  │                          │  │ ⏳ Waiting for Modal...  │  │
│  │ ✅ Completed             │  │                         │  │
│  │ TTFT: 245ms              │  │                         │  │
│  │ Speed: 42.3 tok/s        │  │                         │  │
│  │ Tokens: 67               │  │                         │  │
│  └──────────────────────────┘  └─────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```
Flow:
1. On mount: fetch models via `GET /models/`
2. User types prompt, selects models via checkboxes
3. Submit (requires login): `POST /inference/` → get `session_id`
4. Pass `session_id` to `useInferenceSocket` → WebSocket connects
5. `model_start` messages → show model cards with "Waiting" state
6. `model_complete` messages → show response text + metrics in that card
7. `model_error` messages → show error in that card
8. `session_complete` → show final state

Built with: shadcn Card, Textarea, Button, Checkbox, Badge.

**`src/components/Results.tsx`** — public gallery of all past sessions.
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
- On mount: fetch `GET /inference/sessions`
- TanStack Table + shadcn `<Table>` components
- Define columns: #, User (avatar+name), Prompt (truncated), Models (count), Fastest, Time (relative)
- Click row → fetch `GET /inference/sessions/{id}` → expand with full detail

**`src/components/About.tsx`** — portfolio page.
- Copy content from `archive/frontend/src/components/portfolio/Portfolio.tsx`
- Restyle with shadcn Card components
- Static content, no API calls

### Frontend Dependencies
```
react, react-dom                    # core
@react-oauth/google                 # Google Sign-In (one component)
tailwindcss, @tailwindcss/vite      # styling (installed by shadcn init)
class-variance-authority, clsx,     # shadcn peer deps (installed by shadcn init)
tailwind-merge, lucide-react
@tanstack/react-table               # DataTable for Results tab
```

---

## Docker — PARTIALLY DONE

**`docker-compose.yml`** (root, local dev) — DONE, needs frontend service added later:
```yaml
services:
  mysql:        # ✅ done
  backend:      # ✅ done
  frontend:     # TODO: add after frontend is built
```

**`backend/Dockerfile`** — DONE (python:3.11-slim + uv)

**`frontend/Dockerfile`** — TODO
```dockerfile
# Stage 1: build
FROM node:22-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: serve
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
# SPA fallback: all routes → index.html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

**nginx.conf** (for production, WebSocket proxy) — TODO:
```nginx
# Must include WebSocket upgrade headers:
location /ws/ {
    proxy_pass http://backend:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

---

## Implementation Steps

### PHASE 1: Backend WebSocket Upgrade ✅→🔧

> These are code changes to 2 existing backend files.

**Step 1** — Update `routes/inference.py`:
1. Remove the `stream_results` SSE endpoint (the `@router.get("/{session_id}/stream")` function)
2. Remove `asyncio.create_task(run_modal_inference(...))` from the POST endpoint — POST should only create DB rows and return
3. Add `from fastapi import WebSocket, WebSocketDisconnect` to imports
4. Add `import jwt` and import `JWT_SECRET_KEY, JWT_ALGORITHM` from settings
5. Add the WebSocket endpoint `@router.websocket("/ws/inference/{session_id}")`
6. The WebSocket endpoint:
   - Accepts connection
   - Waits for first message with JWT, verifies it, extracts user_id
   - Loads session from DB, verifies user owns it
   - Loads all pending InferenceResult rows
   - For each result: creates a task that calls the refactored `run_modal_inference`
   - `asyncio.gather()` all tasks
   - Sends `{"type": "session_complete"}`
   - Closes connection
   - Wraps everything in try/except `WebSocketDisconnect`

**Step 2** — Update `handlers/modal.py`:
1. Add `WebSocket` to imports
2. Change `run_modal_inference` signature to accept `websocket` and `db_session` params
3. Remove the standalone engine creation (no longer fire-and-forget)
4. Send `model_start` message via WebSocket before calling Modal
5. Send `model_complete` or `model_error` via WebSocket after Modal returns
6. Still save results to DB (for Results tab history)

**Step 3** — Verify backend WebSocket:
```bash
# Start backend
docker compose up mysql
cd backend && uv run uvicorn main:app --host 0.0.0.0 --reload

# Test with websocat (install: brew install websocat)
websocat ws://localhost:8000/ws/inference/1

# First message: send JWT
{"token": "Bearer <your-jwt>"}

# Should receive model_start, model_complete, session_complete messages
```

---

### PHASE 2: Frontend Scaffold

**Step 4** — Create Vite + React project:
```bash
# from repo root
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```

**Step 5** — Initialize shadcn/ui:
```bash
npx shadcn@latest init
# Style: default | Base color: neutral/zinc | CSS variables: yes
```

**Step 6** — Add shadcn components:
```bash
npx shadcn@latest add button input textarea tabs card badge avatar dropdown-menu table checkbox
```

**Step 7** — Install extra dependencies:
```bash
npm install @react-oauth/google @tanstack/react-table
```

**Step 8** — Create `.env`:
```
VITE_API_BASE_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=your-client-id-here
VITE_WS_BASE_URL=ws://localhost:8000
```

**Step 9** — Verify: `npm run dev` → see default page at http://localhost:5173

---

### PHASE 3: Types + API Client

**Step 10** — Create `src/types/index.ts`:
- Define all interfaces matching backend schemas
- Define WebSocket message types

**Step 11** — Create `src/lib/api.ts`:
- Fetch wrapper with auto JWT attachment
- Named export functions for each endpoint

---

### PHASE 4: Auth

**Step 12** — Create `src/hooks/useAuth.ts`:
- AuthContext + AuthProvider + useAuth hook
- login, logout, auto-rehydrate on mount

**Step 13** — Create `src/components/LoginButton.tsx`:
- GoogleLogin component or Avatar+DropdownMenu

**Step 14** — Create `src/App.tsx`:
- GoogleOAuthProvider → AuthProvider → Layout

**Step 15** — Create `src/components/Layout.tsx`:
- Header + Tabs (Playground, Results, About)

**Step 16** — Verify auth:
```bash
# Terminal 1: backend (docker compose up)
# Terminal 2: cd frontend && npm run dev
# Browser: click Google Login → check Network tab → check localStorage
```

---

### PHASE 5: Playground

**Step 17** — Create `src/hooks/useInferenceSocket.ts`:
- WebSocket hook: connect, auth, dispatch messages, cleanup

**Step 18** — Create `src/components/Playground.tsx`:
- Model list (from GET /models)
- Prompt textarea + submit button
- On submit: POST /inference → open WebSocket via hook
- Side-by-side model cards showing status, response, metrics
- Card states: Waiting → Streaming → Completed/Failed

**Step 19** — Verify Playground:
- Login → type prompt → select models → submit
- Watch WebSocket messages in DevTools → Network → WS tab
- Cards update as model_start / model_complete arrive

---

### PHASE 6: Results

**Step 20** — Create `src/components/Results.tsx`:
- Fetch sessions on mount
- TanStack Table + shadcn Table components
- Columns: #, User, Prompt, Models, Fastest, Time
- Click row → expand with full session detail

---

### PHASE 7: About

**Step 21** — Create `src/components/About.tsx`:
- Port content from `archive/frontend/src/components/portfolio/Portfolio.tsx`
- Restyle with shadcn Card

---

### PHASE 8: Docker + Integration

**Step 22** — Create `frontend/Dockerfile` (two-stage: node build → nginx serve)

**Step 23** — Update root `docker-compose.yml`: add frontend service

**Step 24** — Verify full stack:
```bash
docker compose up --build
# localhost:3000 → frontend
# localhost:8000 → backend
# Full flow: login → playground → submit → stream → results tab
```

---

### PHASE 9: Deployment (Day 3)

**Step 25** — AWS: RDS MySQL, ECR images, EC2 deploy
**Step 26** — Route53 + SSL (certbot)
**Step 27** — nginx.conf with WebSocket proxy headers
**Step 28** — Infra repo: nightly.yml, smoke-test.sh, deploy.sh

---

## Key Technical Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Auth | Google ID token flow (not auth code) | Simplest: no backend redirect URI, 10 lines of code |
| JWT | PyJWT HS256 | Simple symmetric signing, no RSA key management |
| ORM | SQLAlchemy 2.0 async (Mapped/mapped_column) | Already implemented, modern pattern |
| Streaming | WebSocket (not SSE) | Auth via first message, no DB polling, future token streaming |
| Frontend state | React hooks + Context | No Redux/Zustand needed for 3 tabs |
| WebSocket | One WS per session, messages tagged by model_id | Simple multiplexing, no per-model connections |
| Modal | Reuse evaluation/modal.py as-is | Proven code, .remote() call pattern works |
| Admin | Swagger UI + seed script | No admin panel needed for MVP |

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
6. Copy Client ID → set as `GOOGLE_CLIENT_ID` env var + `VITE_GOOGLE_CLIENT_ID`
7. No client secret needed for this flow
