# EchoLens
### Turn customer conversations into insight.

## Overview

Customer support teams sit on thousands of hours of recorded calls, yet most of this data is never analyzed. Valuable signals about customer frustration, recurring issues, and operational failures remain buried in audio files, making it difficult for managers to act proactively.

**EchoLens** is a full-stack, AI-powered customer support analytics platform that transforms raw customer support calls into **structured intelligence, actionable trends, and executive-ready insights**. It combines speech-to-text, large language models, scalable backend systems, and interactive dashboards to help organizations understand *what customers are saying, why issues are happening, and where intervention is required*.

The system is designed as a **production-grade, cloud-native application**, emphasizing scalability, cost efficiency, and responsible AI usage.

---

## Problem Statement

- Customer support calls are unstructured and difficult to analyze at scale.
- Organizations often already store call recordings in **AWS S3**, but lack tools to extract insights from them.
- Managers have limited visibility into recurring issues, sentiment shifts, and escalation risks.
- Manual call reviews are expensive, slow, and inconsistent.
- Naive AI systems make excessive LLM calls, leading to high operational costs.

EchoLens addresses these challenges by directly integrating with S3-based call storage, converting audio into structured data, computing analytics efficiently, and using LLMs only where they add real value.

---

## Key Features

### ☁️ Cloud-Native Ingestion (AWS S3)
- **Direct integration with AWS S3** for audio ingestion.
- Supports two enterprise-friendly workflows:
  - Upload new calls via **presigned S3 URLs**.
  - Pull and process existing call archives **directly from S3 buckets and prefixes**.
- Eliminates the need for data migration or format changes.
- Workers fetch audio directly from S3, enabling large-scale batch processing.

### 🎤 AI-Powered Speech Transcription
- Converts support call audio into text using OpenAI Whisper.
- Supports common audio formats (WAV, MP3, M4A, OGG, WebM).
- Robust error handling and fallback logic for production reliability.

### 🤖 Structured LLM Analysis
- Uses Groq LLMs to extract **structured JSON** from transcripts:
  - Customer sentiment
  - Issue topic classification
  - Resolution status
  - Confidence score
- Enforced with **strict Pydantic schema validation** and bounded retries.
- Safe fallbacks prevent malformed outputs or hallucinations.

### 💰 Cost-Efficient AI Design
- LLMs are **not called unnecessarily**.
- Redis is used to:
  - Cache transcription and analysis results
  - Avoid duplicate LLM calls for the same audio or metrics
  - Cache analytics results for dashboards
- LLMs are used only for:
  - Initial structured extraction
  - Executive-level insight generation
- This design keeps the system **cost-efficient and scalable**.

### 🔄 Asynchronous Processing Pipeline
- Background processing using Celery and Redis.
- Decouples ingestion, transcription, analysis, and storage.
- Designed for horizontal scalability and fault tolerance.

### 📊 Advanced Analytics & Insights
- Weekly topic trend detection with growth indicators.
- Resolution effectiveness metrics by topic.
- Escalation risk scoring with explainable drivers.
- Automated alerts for negative or rapidly growing issues.

### 🧠 LLM-Generated Executive Summary
- Generates concise, executive-ready summaries from **pre-computed structured metrics**, not raw transcripts.
- Ensures explainability, traceability, and cost control.
- Demonstrates responsible and practical LLM usage.

### 📈 Interactive Analytics Dashboard
- Built with React and TypeScript.
- Visualizes trends, risks, and performance metrics.
- Designed for managerial decision-making rather than raw data inspection.

---

## Core Technical Concepts Demonstrated

- **Cloud-native file ingestion with AWS S3**
- **Presigned upload workflows**
- **End-to-end AI pipeline design**
- **Speech-to-text integration**
- **LLM orchestration with schema enforcement**
- **Cost-aware LLM usage and caching**
- **Asynchronous background processing**
- **Relational data modeling for analytics**
- **Explainable metric computation**
- **Full-stack system architecture**

---

## System Architecture

```
React Frontend (Vite + TypeScript)
        ↓  (presigned uploads)
AWS S3 (Call Recordings)
        ↓  (workers pull objects)
FastAPI Backend (REST APIs)
        ↓  (async job queue)
Celery Workers + Redis
        ↓
OpenAI Transcription → Groq LLM Analysis
        ↓
PostgreSQL (Structured Data & Metrics)
        ↓
Analytics APIs → Dashboard
```

---

## Tech Stack

### Frontend
- React
- TypeScript
- Vite
- Recharts

### Backend
- FastAPI
- SQLAlchemy 2.0
- Alembic
- Celery
- Redis

### AI / ML
- OpenAI Whisper (`whisper-1`)
- Groq LLM (`llama-3.3-70b-versatile`)
- Pydantic

### Data & Infrastructure
- PostgreSQL
- AWS S3
- Redis

---

## License

MIT
