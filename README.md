# Customer Support Auditor - Phase 3: AI-Driven Analytics & Executive Insights

A multi-modal customer support call auditing system that transcribes audio calls using **OpenAI Whisper**, analyzes sentiment and topics using **Groq LLM**, and provides advanced analytics with AI-generated executive insights.

## 🎯 Phase 3 Features

- 🎤 **OpenAI Transcription**: Uses `whisper-1` model (with automatic fallback if preferred model fails)
- 🤖 **Groq LLM Analysis**: Uses `llama-3.3-70b-versatile` for structured JSON extraction
- ✅ **Pydantic Validation**: Strict schema validation with retry logic
- 🔄 **Background Processing**: Celery + Redis for async processing
- 📊 **Advanced Analytics**: Weekly trends, resolution effectiveness, escalation risk scoring
- 💡 **AI Executive Summary**: LLM-powered insights generated from structured metrics
- 📈 **Interactive Dashboard**: Professional analytics dashboard with trend charts and risk panels
- ⚠️ **Smart Alerts**: Week-over-week spike detection
- 🌐 **Clean API Layer**: FastAPI-based REST endpoints for uploads, call retrieval, metrics, and analytics keep the system modular and easy to integrate.
- 🗄️ **Relational Database Backbone**: PostgreSQL + SQLAlchemy 2.0 store calls, transcripts, and analyses with clear schemas for reliable querying and aggregation.
- ☁️ **Cloud-Native Storage**: Audio recordings are stored in AWS S3 using secure presigned URLs and well-defined prefixes (`upload/`, S3 import prefixes) for scalable, durable storage.

## Architecture

```
React Frontend (Vite + TS)
  ↓ presigned upload
S3-Compatible Storage (MinIO)
  ↓
FastAPI Backend
  ↓
Celery Worker
  ↓
OpenAI Transcription → Groq LLM Analysis
  ↓
PostgreSQL Database
  ↓
Dashboard Metrics + Alerts
```

## Prerequisites

- **Python 3.11+** (with venv support)
- **PostgreSQL 15+**
- **Redis 7+**
- **MinIO** (or S3-compatible storage)
- **Node.js 18+** (for frontend)
- **OpenAI API Key** (for transcription)
- **Groq API Key** (for analysis)

## Quick Start

### 1. Install System Dependencies

**macOS** (using Homebrew):
```bash
brew install postgresql@15 redis minio node
brew services start postgresql@15
brew services start redis
```

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib redis-server nodejs npm
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
sudo mv minio /usr/local/bin/

sudo systemctl start postgresql
sudo systemctl start redis
```

### 2. Setup Database

**Quick Setup (Recommended - macOS):**
```bash
# Use the automated setup script
chmod +x setup-database.sh
./setup-database.sh
```

**Manual Setup:**

**Option A: Using PostgreSQL utilities (if installed via Homebrew)**

First, ensure PostgreSQL bin directory is in PATH:
```bash
# Add to ~/.zshrc or ~/.bash_profile
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"  # Apple Silicon
# OR
export PATH="/usr/local/opt/postgresql@15/bin:$PATH"     # Intel Mac

# Reload shell
source ~/.zshrc
```

Then create user and database:
```bash
createuser -s app
createdb -O app auditor
```

**Option B: Using psql directly (if PostgreSQL is installed but not in PATH)**

Find PostgreSQL installation:
```bash
# macOS Homebrew - Apple Silicon
/opt/homebrew/opt/postgresql@15/bin/createuser -s app
/opt/homebrew/opt/postgresql@15/bin/createdb -O app auditor

# macOS Homebrew - Intel
/usr/local/opt/postgresql@15/bin/createuser -s app
/usr/local/opt/postgresql@15/bin/createdb -O app auditor

# Or find it:
find /opt /usr/local -name createuser 2>/dev/null
```

**Option C: Using psql SQL commands (works if psql is available)**

```bash
# Connect as postgres superuser
psql postgres

# Then run these SQL commands:
CREATE USER app WITH PASSWORD 'app';
CREATE DATABASE auditor OWNER app;
\q
```

**Option D: Install PostgreSQL if not installed**

**macOS (Homebrew):**
```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install PostgreSQL
brew install postgresql@15

# Start PostgreSQL service
brew services start postgresql@15

# Add to PATH (add to ~/.zshrc)
echo 'export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Now create user and database
createuser -s app
createdb -O app auditor
```

### 3. Setup Backend

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Copy and configure environment variables
cp .env.example .env
# Edit .env and add your API keys (see Configuration section)

# Run database migrations
alembic upgrade head
```

### 4. Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env
```

### 5. Configure API Keys

Edit `backend/.env`:

```bash
# Required: Get from https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_TRANSCRIBE_MODEL=whisper-1

# Required: Get from https://console.groq.com/keys
GROQ_API_KEY=gsk-your-groq-api-key-here
GROQ_MODEL=llama-3.3-70b-versatile

# Database (already configured)
DATABASE_URL=postgresql+psycopg://app:app@localhost:5432/auditor

# Redis (already configured)
REDIS_URL=redis://localhost:6379/0

# MinIO (defaults)
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=calls

# Providers (set to use real AI)
TRANSCRIBE_PROVIDER=openai
LLM_PROVIDER=groq
```

**Get API Keys:**
- **OpenAI**: https://platform.openai.com/api-keys
- **Groq**: https://console.groq.com/keys

### 6. Start Services

**Terminal 1 - MinIO**:
```bash
mkdir -p ~/minio-data
MINIO_ROOT_USER=minioadmin MINIO_ROOT_PASSWORD=minioadmin minio server ~/minio-data --console-address ":9001"
```

**Terminal 2 - Backend API**:
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 3 - Celery Worker**:
```bash
cd backend
source venv/bin/activate
celery -A app.core.celery_app worker --loglevel=info --concurrency=2
```

**Terminal 4 - Frontend**:
```bash
cd frontend
npm run dev
```

### 7. Access Application

- **Frontend Dashboard**: http://localhost:5173
- **API Documentation**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)

## Usage

### Uploading a Call

1. Go to http://localhost:5173/upload
2. Click upload zone and select an audio file (WAV, MP3, etc.)
3. Click "Upload & Process"
4. The system will:
   - Upload file to MinIO
   - Queue processing task
   - Transcribe using OpenAI
   - Analyze using Groq LLM
   - Save results to PostgreSQL

### Viewing Results

1. Go to http://localhost:5173 (Dashboard)
2. Dashboard shows:
   - **Calls by Topic**: Bar chart from real AI analysis
   - **System Status**: Processing statistics
   - **Recent Calls**: Latest uploads with status (with manual Refresh button)
   - **Alert Banner**: Week-over-week spikes with negative sentiment

3. Use the "Refresh" button to manually update the dashboard data when needed

## Phase 3: AI-Driven Analytics & Executive Insights

### Overview

Phase 3 adds advanced analytics capabilities with AI-powered executive insights. All analytics are computed from structured metrics stored in the database, ensuring explainability and traceability.

**Key Principles**:
- ✅ **Analytics logic ≠ LLM wording**: Metrics are computed first, then LLM formats insights
- ✅ **Grounded in data**: LLM operates on structured metrics, not raw transcripts
- ✅ **Explainable**: All scores and trends have clear calculation methods
- ✅ **Business value**: Focus on actionable insights for management

### Analytics Endpoints

#### 1. Weekly Topic Trend Analysis

**Endpoint**: `GET /analytics/topic_trends?weeks=8`

**Returns**: Weekly counts and negative sentiment rates by topic, with trend indicators (up/down/flat) and percentage change.

**Calculation Logic**:
- Groups calls by ISO week number
- Compares latest week vs previous week
- Percentage change: `(current - previous) / max(previous, 1)`
- Trend thresholds:
  - **up**: > +15% change
  - **down**: < -15% change
  - **flat**: otherwise

**Use Case**: Identify which topics are growing/declining over time and spot trends early.

#### 2. Resolution Effectiveness by Topic

**Endpoint**: `GET /analytics/resolution_effectiveness`

**Returns**: Resolution rate, negative sentiment rate, and average confidence score by topic.

**Calculation Logic**:
- Resolution rate: `resolved_calls / total_calls`
- Negative rate: `negative_calls / total_calls`
- Average confidence: `AVG(confidence)` from analysis records

**Use Case**: Identify which topics have the best/worst resolution rates and correlate with sentiment.

#### 3. Escalation Risk Scoring

**Endpoint**: `GET /analytics/escalation_risk`

**Returns**: Risk score (0-1) for each topic with explainable drivers.

**Risk Score Calculation** (explainable, additive):
- **+0.4** if negative sentiment rate > 60%
- **+0.3** if resolution rate < 40%
- **+0.3** if week-over-week growth > 30%
- Score clamped between 0 and 1

**Drivers**: Each risk factor is listed with specific percentages for transparency.

**Use Case**: Prioritize topics that need immediate attention based on multiple risk factors.

#### 4. LLM-Generated Executive Summary

**Endpoint**: `GET /analytics/executive_summary`

**Core Feature**: AI-powered executive summary generated from computed metrics.

**How It Works**:

1. **Gather Metrics** (NOT raw transcripts):
   - Total calls in last 7 days
   - Top 5 topics by volume
   - Fastest growing topic with percentage
   - Most negative topic with rate
   - Highest risk topics (score ≥ 0.6)
   - Overall negative sentiment rate

2. **Pass to LLM** (Structured JSON input):
   ```json
   {
     "time_window": "Last 7 days vs previous 7 days",
     "total_calls": 150,
     "top_topics": [...],
     "fastest_growing_topic": {"topic": "billing_issue", "pct_change": 0.32},
     "most_negative_topic": {"topic": "tech_support", "negative_rate": 0.65},
     "highest_risk_topics": [...],
     "overall_negative_rate": 0.58
   }
   ```

3. **LLM Generates Summary** (2-4 sentences):
   - Professional, executive-level tone
   - Focus on trends, risks, actionable insights
   - Uses specific percentages and numbers from metrics
   - Validated with Pydantic schema

4. **Fallback**: If LLM fails, uses deterministic summary based on metrics

**Example Output**:
> "Billing issues increased 32% week-over-week and now represent the highest escalation risk due to rising negative sentiment (65%) and low resolution rates (38%). Shipping complaints are growing quickly but remain mostly neutral. Overall customer sentiment declined slightly this week, with 58% negative sentiment across all topics."

**Key Benefits**:
- ✅ **Traceable**: Every number in summary can be traced to database metrics
- ✅ **No Hallucinations**: LLM only uses provided structured data
- ✅ **Explainable**: Summary generation is deterministic (metrics → LLM → text)
- ✅ **Business Value**: Executive-ready insights for management decisions

### Dashboard Enhancements

#### Executive Summary Card
- **Location**: Top of dashboard (highlighted gradient card)
- **Data Source**: `/analytics/executive_summary`
- **Features**: 
  - Large, readable text block
  - "AI-Generated Weekly Insight" subtitle
  - Auto-refreshes on dashboard load

#### Trend Analysis Chart
- **Location**: Main dashboard grid
- **Data Source**: `/analytics/topic_trends`
- **Features**:
  - Line chart showing call volume or negative % over time
  - Toggle between "Volume" and "Negative %" views
  - Multiple topic lines with distinct colors
  - Time range: Configurable (default 8 weeks)

#### Escalation Risk Panel
- **Location**: Side panel on dashboard
- **Data Source**: `/analytics/escalation_risk`
- **Features**:
  - List topics with risk scores ≥ 0.6 (filterable)
  - Color-coded severity (green/yellow/red)
  - Show risk drivers beneath each topic
  - Risk score displayed as percentage badge

#### Resolution Effectiveness Table
- **Location**: Bottom section of dashboard
- **Data Source**: `/analytics/resolution_effectiveness`
- **Features**:
  - Sortable columns (Topic, Resolution %, Negative %, Confidence)
  - Color-coded metrics (green/yellow/red thresholds)
  - Professional table layout with tooltips

### Dashboard UX Features

- **Loading States**: Skeleton loaders for async data fetching
- **Empty States**: Friendly messages when no data available
- **Error Handling**: Graceful degradation if analytics endpoints fail
- **Tooltips**: Explanations for risk scores and trend calculations
- **Refresh Button**: Manual refresh for real-time updates

### Analytics Architecture

```
Database (PostgreSQL)
  ↓ SQL Aggregations
Computed Metrics (Structured Data)
  ↓
Analytics Endpoints (FastAPI)
  ├─ Weekly Trends (SQL + Python logic)
  ├─ Resolution Effectiveness (SQL aggregations)
  ├─ Escalation Risk (SQL + Python scoring)
  └─ Executive Summary (Metrics → LLM → Text)
  ↓
Frontend Dashboard (React)
  ├─ Trend Charts (Recharts)
  ├─ Risk Panels (React components)
  ├─ Executive Summary (AI-generated text)
  └─ Resolution Table (Sortable, filterable)
```

**Separation of Concerns**:
- Analytics logic: Pure Python/SQL (explainable, deterministic)
- LLM wording: Groq API (professional, readable)
- Visualization: React/Recharts (interactive, responsive)

### Performance

- **Fast Queries**: Optimized SQL with indexes on `created_at`, `topic`, `sentiment`
- **Caching Ready**: Analytics endpoints can be cached (metrics are time-windowed)
- **Parallel Loading**: Frontend loads all analytics endpoints in parallel
- **Incremental Updates**: Weekly trends calculated incrementally (ISO week grouping)

## Phase 2: Real AI Implementation

### OpenAI Transcription

- **Default Model**: `whisper-1` (more reliable, supports multiple formats)
- **Fallback Logic**: If preferred model (e.g., `gpt-4o-mini-transcribe`) fails with format errors, automatically falls back to `whisper-1`
- **Service**: `app/services/transcribe.py`
- **Flow**: Audio file → OpenAI API (direct REST call) → Transcript text
- **Response Formats**: 
  - `whisper-1`: Supports `text` or `json` (uses `text` for simpler parsing)
  - `gpt-4o-mini-transcribe` / `gpt-4o-transcribe`: Only supports `json`
- **Error Handling**: Automatic fallback to `whisper-1` on format errors, mock provider on other failures

### Groq LLM Analysis

- **Model**: `llama-3.3-70b-versatile` (configurable)
- **Service**: `app/services/analyze.py`
- **Output Schema** (Pydantic validated):
  ```json
  {
    "customer_sentiment": "positive" | "neutral" | "negative",
    "topic": "billing_issue" | "tech_support" | "cancellation" | "shipping" | "other",
    "problem_resolved": true | false,
    "summary": "string (max 240 chars)",
    "confidence": 0.0-1.0
  }
  ```

**Features**:
- ✅ Strict JSON-only output enforcement
- ✅ Pydantic validation with retry (up to 2 retries)
- ✅ Safe fallback on repeated failures
- ✅ Structured prompts for consistent output

### Processing Pipeline

1. **Upload**: User uploads audio → MinIO storage
2. **Queue**: Backend enqueues Celery task
3. **Download**: Worker downloads audio from MinIO
4. **Transcribe**: OpenAI API transcribes audio
5. **Analyze**: Groq LLM analyzes transcript
6. **Save**: Results stored in PostgreSQL
7. **Update**: Status changed to DONE

## API Endpoints

### Phase 2 Endpoints (Upload & Processing)

```bash
# Upload flow
POST /upload/presign?content_type=audio/wav&filename=audio.mp3
POST /upload/complete/{call_id}

# Retrieval
GET /calls?limit=50
GET /calls/{call_id}

# Basic Metrics
GET /metrics/topic_counts
GET /metrics/negativity_by_topic
GET /metrics/weekly_spikes
```

### Phase 3 Endpoints (Advanced Analytics)

```bash
# Analytics Endpoints
GET /analytics/topic_trends?weeks=8        # Weekly trend analysis by topic
GET /analytics/resolution_effectiveness     # Resolution metrics by topic
GET /analytics/escalation_risk              # Risk scoring with drivers
GET /analytics/executive_summary            # AI-generated executive summary

# Health
GET /health
GET /docs  # OpenAPI documentation
```

Full API docs: http://localhost:8000/docs

## Configuration

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `OPENAI_API_KEY` | Yes | OpenAI API key | `sk-...` |
| `OPENAI_TRANSCRIBE_MODEL` | No | Transcription model (falls back to `whisper-1` on format errors) | `whisper-1` |
| `GROQ_API_KEY` | Yes | Groq API key | `gsk-...` |
| `GROQ_MODEL` | No | Analysis model | `llama-3.3-70b-versatile` |
| `DATABASE_URL` | Yes | PostgreSQL connection | `postgresql+psycopg://...` |
| `REDIS_URL` | Yes | Redis connection | `redis://localhost:6379/0` |
| `S3_ENDPOINT` | Yes | MinIO/S3 endpoint | `http://localhost:9000` |
| `S3_ACCESS_KEY` | Yes | S3 access key | `minioadmin` |
| `S3_SECRET_KEY` | Yes | S3 secret key | `minioadmin` |
| `S3_BUCKET` | Yes | Bucket name | `calls` |
| `TRANSCRIBE_PROVIDER` | Yes | `openai` or `mock` | `openai` |
| `LLM_PROVIDER` | Yes | `groq` or `mock` | `groq` |

### Switching to Mock Providers (Testing)

For testing without API keys, set in `.env`:

```bash
TRANSCRIBE_PROVIDER=mock
LLM_PROVIDER=mock
```

## Troubleshooting

### OpenAI API Errors

**Error**: `OpenAI API error: Invalid API key`
- **Fix**: Check `OPENAI_API_KEY` in `.env` file
- **Verify**: Key starts with `sk-` and is active at https://platform.openai.com

**Error**: `Model not found` or `unsupported_format` with `param: "messages"`
- **Fix**: The system automatically falls back to `whisper-1` if the preferred model fails. If you want to use `whisper-1` directly, set `OPENAI_TRANSCRIBE_MODEL=whisper-1` in `.env`
- **Note**: `gpt-4o-mini-transcribe` has known compatibility issues with certain audio formats. Using `whisper-1` is recommended for reliability.
- **Check Models**: Available models: https://platform.openai.com/docs/models

**Error**: `Rate limit exceeded`
- **Fix**: You've hit OpenAI rate limits. Wait or upgrade plan
- **Workaround**: Use mock provider temporarily: `TRANSCRIBE_PROVIDER=mock`

### Groq API Errors

**Error**: `Groq API error: Invalid API key`
- **Fix**: Check `GROQ_API_KEY` in `.env` file
- **Verify**: Key starts with `gsk-` and is active at https://console.groq.com

**Error**: `Model not found: llama-3.3-70b-versatile`
- **Fix**: Check available models at https://console.groq.com/docs/models
- **Update**: Change `GROQ_MODEL` in `.env` to available model (e.g., `llama-3.1-70b-versatile`)

**Error**: `JSON decode error` or `Pydantic validation error`
- **Note**: This triggers automatic retry (up to 2 retries)
- **Fix**: If persists, check Groq API status. Falls back to safe default after retries
- **Check logs**: Look for "Retrying..." messages in worker logs

### Database Issues

**Error**: `Connection refused` or `database does not exist`
```bash
# Check PostgreSQL is running
pg_isready

# Create database if missing
createdb -O app auditor

# Run migrations
cd backend
source venv/bin/activate
alembic upgrade head
```

### Redis Issues

**Error**: `Connection refused to Redis`
```bash
# Check Redis is running
redis-cli ping  # Should return PONG

# Start Redis
# macOS:
brew services start redis
# Linux:
sudo systemctl start redis
```

### Worker Not Processing

**Check worker logs**:
```bash
# Worker should show task received/processing logs
tail -f logs/worker.log  # if running in background
# Or check terminal running worker
```

**Common issues**:
- Redis not running → Start Redis
- API keys not set → Check `.env` file
- Database connection error → Check `DATABASE_URL`

### MinIO Issues

**Error**: `Bucket not found`
- **Fix**: Backend creates bucket automatically on startup
- **Manual**: Access http://localhost:9001, login, create bucket `calls`

**Error**: `Connection refused`
- **Fix**: Ensure MinIO is running on port 9000
- **Check**: `curl http://localhost:9000/minio/health/live`

### Environment Variables Not Loading

**Issue**: Changes to `.env` not taking effect

**Fix**:
```bash
# Backend/Worker: Just restart (variables auto-load via pydantic-settings)
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Variables automatically load from .env file via pydantic-settings
# No need to export manually
```

### Frontend Not Loading

**Error**: `Network error` or `CORS error`
- **Fix**: Ensure backend is running on port 8000
- **Check**: `curl http://localhost:8000/health`
- **CORS**: Backend allows `http://localhost:5173` by default

## Development

### Running Locally (No Docker)

See **Quick Start** section above for complete setup.

### Project Structure

```
customer-support-auditor/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routes
│   │   ├── core/             # Config, Celery
│   │   ├── db/               # Models, session
│   │   ├── services/         # transcribe.py, analyze.py
│   │   ├── tasks/            # process_call.py
│   │   └── main.py
│   ├── alembic/              # Migrations
│   ├── requirements.txt      # Python dependencies
│   └── .env.example          # Environment template
├── frontend/
│   ├── src/                  # React components
│   ├── package.json
│   └── .env.example
└── README.md
```

### Code Changes from Phase 1

**New/Updated Files**:
- `backend/app/services/transcribe.py` - OpenAI integration
- `backend/app/services/analyze.py` - Groq integration with retry logic
- `backend/app/core/config.py` - Added OpenAI/Groq config
- `backend/app/tasks/process_call.py` - Updated for tuple return
- `backend/requirements.txt` - Added `openai`, `groq`, `python-dotenv`

**Unchanged**:
- All API endpoints remain the same
- Frontend code unchanged
- Database schema unchanged

### Testing

**Test with mock providers** (no API keys needed):
```bash
# In backend/.env
TRANSCRIBE_PROVIDER=mock
LLM_PROVIDER=mock
```

**Test with real AI**:
```bash
# Set API keys in backend/.env
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk-...
TRANSCRIBE_PROVIDER=openai
LLM_PROVIDER=groq
```

## Production Deployment

### Security Checklist

- [ ] Change all default passwords
- [ ] Use environment variable secrets (not .env files)
- [ ] Enable HTTPS/TLS
- [ ] Restrict CORS origins
- [ ] Add rate limiting
- [ ] Use managed PostgreSQL (e.g., AWS RDS)
- [ ] Use managed Redis (e.g., AWS ElastiCache)
- [ ] Use production S3 (not MinIO)
- [ ] Add authentication/authorization
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure log aggregation
- [ ] Add backup policies

### Performance Optimization

- Use Gunicorn/Uvicorn workers for FastAPI
- Scale Celery workers horizontally
- Add Redis caching for metrics
- Configure PostgreSQL connection pooling
- Use CDN for frontend assets

## License

MIT License - feel free to use for your projects!

## Support

**Common Issues**:
- See **Troubleshooting** section above
- Check API docs: http://localhost:8000/docs
- View worker logs for processing errors
- Verify API keys are valid

**API Status**:
- OpenAI: https://status.openai.com
- Groq: https://console.groq.com/status

---

**Phase 3 Complete! Built with ❤️ using FastAPI, OpenAI, Groq, React, PostgreSQL, and Advanced Analytics**
