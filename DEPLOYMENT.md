# MEDVISION — Production Deployment & Operational Reliability Guide

This document defines the production architecture, deployment procedures, environment configurations, security controls, backup strategies, and recovery workflows for the MEDVISION AI explainable medical imaging system.

---

## 1. Supported Runtimes & Infrastructure Targets

| Component | Single-Instance Deployment | Multi-Worker / Clustered Production |
| :--- | :--- | :--- |
| **Backend API** | Python 3.11–3.13 (FastAPI + Uvicorn) | Python 3.11–3.13 (Gunicorn + Uvicorn Workers / Docker / K8s) |
| **AI Inference** | PyTorch 2.0+ (CPU or CUDA 11.8+) | PyTorch 2.0+ on Dedicated GPU Nodes |
| **Frontend UI** | Static SPA (served via Nginx / Caddy / CDN) | Static SPA (Cloudflare Pages / AWS S3+CloudFront / Nginx) |
| **Database** | SQLite 3.35+ (WAL mode, single-host persistent) | PostgreSQL 15+ (Cloud SQL / AWS RDS / Managed cluster) |
| **Rate Limiter** | In-Memory Sliding Window (thread-safe deque) | Distributed Sliding Window (Redis 6.x+ cluster or Sentinel) |

---

## 2. Environment Variables & Startup Validations

Configuration is loaded from environment variables or a local `.env` file via Pydantic `BaseSettings`.

### Production & Staging Startup Invariants
When `ENVIRONMENT=production` or `ENVIRONMENT=staging`, the application strictly validates the following invariants at bootstrap and **refuses to start** if any condition is violated:
1. `DEBUG` must be `False`.
2. `API_SECRET_KEY` must be configured with a cryptographically secure key of at least 16 characters.
3. `BACKEND_CORS_ORIGINS` must not contain wildcard `*` or wildcard subdomains (`http://*`, `https://*`).
4. Strict Transport Security (HSTS) and Content Security Policy (CSP) headers are automatically injected on all responses.
5. In `production`, Swagger/OpenAPI documentation routes (`/docs`, `/redoc`, `openapi.json`) are disabled.

### Backend Environment Variables (`backend/.env` or root `.env`)

| Variable Name | Required in Prod/Staging | Default | Description |
| :--- | :---: | :--- | :--- |
| `ENVIRONMENT` | **Yes** | `development` | Deployment environment (`development`, `staging`, or `production`). |
| `DEBUG` | **Yes** | `False` | Debug mode. **Must be `False` in staging and production.** |
| `API_SECRET_KEY` | **Yes** | `None` | Authentication secret key (minimum 16 characters). Protects prediction and chat mutation endpoints. |
| `BACKEND_CORS_ORIGINS` | **Yes** | `["http://localhost:5173"]` | JSON array or comma-separated list of allowed origins. Wildcards (`*`) are prohibited in staging/prod. |
| `DATABASE_URL` | **Yes** | `sqlite:///./medvision.db` | Database connection URL. SQLite for single-instance, or `postgresql://user:pass@host:5432/medvision` for multi-instance. |
| `REDIS_URL` | Optional | `None` | Redis connection URL (e.g. `redis://redis.internal:6379/0`) for distributed rate limiting across multiple workers. |
| `RATE_LIMIT_ENABLED` | No | `True` | Master switch for rate limiting middleware. |
| `RATE_LIMIT_CHAT_PER_MINUTE` | No | `30` | Rate limit for `/api/v1/chat/message` per client IP. |
| `RATE_LIMIT_INFERENCE_PER_MINUTE`| No | `20` | Rate limit for `/retina/...` and `/chest-xray/...` inference per client IP. |
| `RATE_LIMIT_GENERAL_PER_MINUTE` | No | `120` | Rate limit for general API endpoints per client IP. |
| `TRUSTED_PROXIES` | No | `["127.0.0.1", "::1"]` | Whitelist of reverse proxy IPs permitted to supply `X-Forwarded-For`. |
| `RATE_LIMIT_STRICT_FAIL_CLOSED` | No | `False` | If `True`, rejects requests (429/503) when Redis fails. If `False`, falls back to in-memory limiting. |
| `MAX_UPLOAD_SIZE_MB` | No | `10` | Hard cap on image uploads (in megabytes). |
| `MAX_JSON_PAYLOAD_BYTES` | No | `1048576` | Hard cap on JSON bodies (1 MB defense-in-depth). |
| `MAX_CONTENT_LENGTH_BYTES` | No | `15728640` | Hard cap on upload payloads (15 MB defense-in-depth). |
| `GEMINI_API_KEY` | Optional | `None` | Google Gemini API key for MedAssist conversational assistant. |
| `OPENAI_API_KEY` | Optional | `None` | Optional secondary provider API key for automated failover. |

### Frontend Environment Variables (`frontend/.env` or build environment)

| Variable Name | Required in Prod | Default | Description |
| :--- | :---: | :--- | :--- |
| `VITE_API_BASE_URL` | **Yes** | `http://localhost:8000` | Fully qualified base URL of the backend API (e.g. `https://api.medvision.yourdomain.com`). Injected at build time. |

> **Security Rule: Never embed shared API secrets into the frontend build.**  
> The client bundle is public and downloadable by any user. Shared server keys (`API_SECRET_KEY`, `GEMINI_API_KEY`) must NEVER be exposed in `VITE_*` environment variables.

---

## 3. Authentication Architecture & Gateway Integration

MedVision supports three distinct authentication integration tiers depending on hosting environment:

```
[User Browser]
      │
      ▼ (HTTPS)
[Ingress / Reverse Proxy / Auth Gateway (e.g. Cloudflare Access, AWS Cognito, Keycloak)]
      │
      ├─► Passes Authenticated Session Header: Bearer <token> or X-API-Key: <key>
      ▼
[FastAPI Backend: app.core.security.verify_api_key]
      │
      ├─► Constant-time verification against API_SECRET_KEY
      └─► Unauthenticated requests rejected with 401 Unauthorized
```

### 1. Local Research Demonstration Tier
- `API_SECRET_KEY` is omitted or empty.
- Endpoints remain accessible for local exploration without requiring credentials.

### 2. Private Staging / Lab Gateway Tier
- `API_SECRET_KEY` is configured in `.env` (minimum 16 characters).
- Authentication supports both **static gateway keys** and **HMAC-SHA256 compact signed bearer tokens** (`header.payload.signature`).
- Calls without a valid key receive `HTTP 401 Unauthorized`.
- Bearer tokens contain standard claims: `sub` (subject/user), `iat` (issued at), `exp` (expiration timestamp), and `iss` (`medvision-auth-gateway`).
- Expired tokens (`exp < now`) are strictly rejected with `HTTP 401 Unauthorized: Authentication token has expired.`
- Tampered signatures or malformed tokens are immediately rejected with `HTTP 401 Unauthorized`.

#### Generating Staging Access Tokens
Staging operators or authentication gateways can generate time-limited signed bearer tokens using Python:
```bash
python -c "from app.core.security import create_access_token; print(create_access_token('staging-evaluator', expires_in_seconds=3600))"
```
Or for custom expiration (e.g. 8-hour test session):
```bash
python -c "from app.core.security import create_access_token; print(create_access_token('lab-physician-42', expires_in_seconds=28800, extra_claims={'role': 'investigator'}))"
```

### 3. Public Production / Healthcare Enterprise Gateway Tier
- The frontend client utilizes the in-memory `setAuthToken(sessionToken)` API in `frontend/src/services/api.js`.
- The token is retrieved dynamically from the institutional Single Sign-On (SSO / OIDC) login flow and held strictly in memory.
- The token is attached to outbound API mutation requests (`Authorization: Bearer <token>`).
- If using an API gateway (e.g. Kong, Apigee, AWS API Gateway, Cloudflare Access), the gateway validates user tokens and passes authenticated tokens downstream.
- If `API_SECRET_KEY` is unset in staging or production, the backend terminates requests with `HTTP 500 Configuration Error` to prevent silent authentication bypass.

---

## 4. Multi-Worker & Multi-Container Scaling (Redis & PostgreSQL)

When scaling beyond a single Uvicorn process:

### 1. Distributed Rate Limiting (Redis)
In-memory rate limiters track requests per OS process. If Uvicorn runs with `--workers 4`, in-memory rate limiting allows 4x the configured threshold unless backed by a shared cache.
- Configure `REDIS_URL=redis://redis-cluster:6379/0`.
- The rate limiter automatically activates the distributed Redis sorted-set engine.
- If Redis becomes temporarily unreachable, the system logs an error and automatically falls back to in-memory sliding window protection (preventing complete service outages while maintaining local abuse boundaries).

### 2. Clustered Database Persistence (PostgreSQL)
Multi-container deployments (Kubernetes, AWS ECS, Google Cloud Run) require a centralized PostgreSQL database:
- Configure `DATABASE_URL=postgresql://user:pass@db.internal:5432/medvision?sslmode=require`.
- SQLAlchemy automatically activates connection pooling (`pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`).
- Run the migration utility to transfer existing SQLite audit records:
  ```bash
  python database/migrate_to_postgres.py --sqlite-path medvision.db --postgres-url "postgresql://user:pass@db.internal:5432/medvision"
  ```

---

## 5. Hardened Reverse Proxy Configuration

Production deployments must terminate TLS at a secure reverse proxy (Nginx or Caddy) and forward verified headers.

### Nginx Production Configuration (`/etc/nginx/sites-available/medvision.conf`)

```nginx
# Rate limiting zone for public ingress abuse prevention
limit_req_zone $binary_remote_addr zone=medvision_api:10m rate=30r/m;

server {
    listen 80;
    server_name api.medvision.yourdomain.com app.medvision.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.medvision.yourdomain.com;

    # Modern TLS configuration (TLS 1.2 / TLS 1.3 only)
    ssl_certificate /etc/letsencrypt/live/api.medvision.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.medvision.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Enforce request payload limits
    client_max_body_size 15M;

    # API Proxy pass
    location / {
        limit_req zone=medvision_api burst=10 nodelay;

        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;

        # Forward trusted client identifiers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;

        # Timeouts matching MedAssist deadlines
        proxy_connect_timeout 60s;
        proxy_read_timeout 60s;
        proxy_send_timeout 60s;
    }
```

### Nginx Private Staging Configuration (`/etc/nginx/sites-available/medvision-staging.conf`)
For controlled private staging, the reverse proxy must restrict access strictly to internal laboratory VPNs/subnets and prohibit public Internet ingress:

```nginx
# Rate limiting zone for staging ingress
limit_req_zone $binary_remote_addr zone=medvision_staging:10m rate=60r/m;

server {
    listen 80;
    server_name staging.medvision.internal;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name staging.medvision.internal;

    # Internal lab / enterprise CA or self-signed cert for private testing
    ssl_certificate /etc/ssl/certs/medvision-staging.crt;
    ssl_certificate_key /etc/ssl/private/medvision-staging.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # STRICT ACCESS CONTROL: Allow only private laboratory VPN / local subnets
    allow 10.0.0.0/8;      # Enterprise VPN
    allow 172.16.0.0/12;   # Internal Docker/K8s network
    allow 192.168.0.0/16;  # Local lab LAN
    allow 127.0.0.1;       # Localhost
    deny all;              # BLOCK ALL PUBLIC INTERNET TRAFFIC

    # Request payload limits
    client_max_body_size 15M;

    # Forward to backend FastAPI
    location /api/ {
        limit_req zone=medvision_staging burst=20 nodelay;

        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;

        # Forward client identity securely
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;

        proxy_connect_timeout 60s;
        proxy_read_timeout 60s;
        proxy_send_timeout 60s;
    }

    # Serve staging frontend SPA static files
    location / {
        root /var/www/medvision-staging/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
}
```

---

## 6. Build & Startup Commands

### Step 1: Build Frontend Assets
```bash
cd frontend

# Set production API URL
export VITE_API_BASE_URL="https://api.medvision.yourdomain.com"
# On Windows PowerShell:
# $env:VITE_API_BASE_URL="https://api.medvision.yourdomain.com"

# Build static production bundle into frontend/dist/
npm run build
```

### Step 2: Start Backend Application
```bash
cd backend

# Activate virtual environment
source venv/bin/activate
# On Windows PowerShell:
# .\venv\Scripts\Activate.ps1

# Start multi-worker production server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 --no-access-log
```

---

## 7. Health Check Endpoints & Monitoring

MEDVISION exposes isolated status endpoints for external monitoring probes:

1. **Service Liveness & Readiness**: `GET /api/health`
   - Returns HTTP 200 with service version, operating status, and timestamp.
   - Independent of external LLM credentials or PyTorch weights.
2. **RetinaGuard Model Status**: `GET /api/v1/retina/model-status`
   - Returns model readiness, active weights file, device (CPU/CUDA), and Grad-CAM availability.
3. **Chest X-Ray Model Status**: `GET /api/v1/chest-xray/model-status`
   - Returns DenseNet-121 model readiness, supported 18 pathologies, and hardware device.
4. **MedAssist AI Status**: `GET /api/v1/chat/status`
   - Returns provider readiness (`gemini` / `openai` / `unconfigured`) without exposing keys.

---

## 8. Incident Response & Operational Runbook

### Incident: LLM Provider Quota Exhaustion (HTTP 502 / 503)
1. **Automated Defense**: MedAssist automatically attempts failover to secondary provider (`OPENAI_API_KEY`) if configured.
2. **Detection**: Monitor log lines with `[WARN] External provider quota exhausted`.
3. **Mitigation**:
   - Verify quota status in Google Cloud / OpenAI console.
   - Switch active provider or update API key in `.env`.
   - Reload server gracefully (`kill -HUP <master_pid>`).

### Incident: In-Memory / Redis Rate Limiter Outage
1. **Behavior**: If Redis is configured but fails, logs report `Redis rate limit check failed. Active policy: FALLBACK_MEMORY`.
2. **Mitigation**: Verify Redis connectivity (`redis-cli ping`). Restart Redis container/service.

### Incident: Database Lock Contention (SQLite)
1. **Behavior**: If concurrent write load spikes on single-instance SQLite, requests wait up to 30s (`busy_timeout=30000`).
2. **Mitigation**:
   - Check WAL file size (`ls -lh medvision.db-wal`).
   - Run manual WAL checkpoint: `sqlite3 medvision.db "PRAGMA wal_checkpoint(TRUNCATE);"`.
   - If traffic exceeds single-host capacity, execute PostgreSQL migration plan.

---

## 9. Deployment Readiness Evaluation Matrix

| Criterion | Local Demo | Private Staging | Public Production |
| :--- | :---: | :---: | :---: |
| **Authentication Enforced** | Optional (bypassed) | **Required** (`API_SECRET_KEY`) | **Required** (SSO Gateway / OAuth2) |
| **Rate Limiting Active** | In-Memory (Active) | In-Memory / Redis | **Redis Distributed Cluster** |
| **Database Architecture** | Local SQLite (WAL) | Single-Node SQLite (WAL) | **Managed PostgreSQL** |
| **TLS / HTTPS Enforced** | HTTP Localhost | TLS 1.2+ Required | **TLS 1.3 + Strict HSTS / CSP** |
| **Medical Regulatory Clearance**| Research Prototype | Internal Evaluation Only | **NO-GO** (Requires FDA 510(k) / CE SaMD) |
| **FINAL DECISION** | **GO** | **GO (Conditional)** | **NO-GO** |

---

## 10. Private Staging Disaster Recovery, Verification & Cost Analysis

### 1. SQLite Online Hot Backup & Restore Runbook
SQLite allows live hot backups while the application continues to process read queries:

#### A. Hot Backup
```bash
# Using the sqlite3 online backup API (safe during concurrent WAL reads)
sqlite3 medvision.db ".backup medvision_backup_$(date +%Y%m%d_%H%M%S).db"

# Verify backup integrity
sqlite3 medvision_backup.db "PRAGMA integrity_check;"
# Expected output: ok
```

#### B. Integrity and Record Count Verification
```bash
# Query record count from backup
sqlite3 medvision_backup.db "SELECT count(*) FROM analysis_sessions;"
```

#### C. Restore Procedure
1. Stop backend services: `pkill -f "uvicorn app.main:app"`
2. Archive damaged file: `mv medvision.db medvision_damaged_$(date +%s).db`
3. Restore from verified backup: `cp medvision_backup.db medvision.db`
4. Verify restored database: `sqlite3 medvision.db "PRAGMA quick_check;"`
5. Restart backend services.

### 2. PostgreSQL Migration Dry-Run & Production Cutover
Before migrating to clustered PostgreSQL:
```bash
# Execute non-destructive dry run
python database/migrate_to_postgres.py \
  --sqlite-path medvision.db \
  --postgres-url "postgresql://meduser:medpass@postgres.internal:5432/medvision_staging" \
  --dry-run

# Run migration on disposable staging database first
python database/migrate_to_postgres.py \
  --sqlite-path medvision.db \
  --postgres-url "postgresql://meduser:medpass@postgres.internal:5432/medvision_disposable"
```

### 3. Redis Rate-Limiter Resilience & Policies
- **Multi-Worker Synchronization**: When `REDIS_URL` is set, all Uvicorn/Gunicorn workers share a single atomic sorted-set key per client IP (`rl:{ip}:{endpoint}`).
- **Fail-Soft Fallback (`RATE_LIMIT_STRICT_FAIL_CLOSED=False`)**: If Redis crashes or experiences network partitioning, the backend gracefully downgrades to per-process in-memory sliding windows with alert logging.
- **Fail-Closed Policy (`RATE_LIMIT_STRICT_FAIL_CLOSED=True`)**: In high-security private staging, requests during Redis downtime are immediately rejected with `HTTP 429 Too Many Requests` or `HTTP 503 Service Unavailable`.

### 4. Automated Staging Verification Suite
MEDVISION includes an automated 20-point verification test suite validating all staging invariants:
```bash
# Run complete staging deployment verification
pytest tests/test_staging_verification.py -v

# Run full security and deployment suite
pytest tests/test_staging_verification.py tests/test_deployment_config.py tests/test_security_audit.py -v
```

### 5. Estimated Deployment Costs Breakdown

| Environment | Infrastructure Components | Estimated Monthly Cost |
| :--- | :--- | :---: |
| **Local Demonstration** | Local Developer Workstation (CPU/GPU) | **$0** |
| **Private Staging** | 1x Dedicated Cloud VPS (4 vCPU, 16GB RAM, SSD)<br>1x Local Redis container<br>Self-contained SQLite WAL on persistent volume<br>Google Gemini 1.5 Flash API (low-volume testing) | **~$45 – $85 / mo** |
| **Public Production** | Multi-AZ Managed Kubernetes / Container Service<br>Managed PostgreSQL HA (Cloud SQL / AWS RDS db.m6i.xlarge)<br>Managed Redis Cluster (AWS ElastiCache / MemoryStore)<br>Dedicated GPU Inference Nodes (NVIDIA T4 / A10G)<br>Cloudflare Enterprise / AWS WAF + DDoS Shield<br>HIPAA BAA & Regulatory Compliance Auditing | **~$850 – $2,500+ / mo** |
