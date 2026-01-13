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
<img width="1236" height="1024" alt="SystemArch" src="https://github.com/user-attachments/assets/a4930073-a204-462f-bae2-d509317c7360" /> 

---

## AI-Driven Analytics & Executive Insights

This module adds advanced analytics and **LLM-powered executive insights** built entirely on structured, explainable metrics stored in the database.

### Design Principles
- Metrics are computed first; LLMs only generate summaries.
- LLMs operate on structured data, not raw transcripts.
- All trends, scores, and insights are explainable and traceable.
- Focused on actionable, management-level insights.

---

### Analytics Endpoints

#### 1. Weekly Topic Trends  
**GET** `/analytics/topic_trends?weeks=8`  

Tracks weekly call volume and negative sentiment by topic, with trend classification (**up / down / flat**) based on week-over-week change.

**Use case:** Early detection of emerging or declining customer issues.

---

#### 2. Resolution Effectiveness  
**GET** `/analytics/resolution_effectiveness`  

Computes resolution rate, negative sentiment rate, and average confidence score per topic.

**Use case:** Identify issue categories that are poorly resolved and driving dissatisfaction.

---

#### 3. Escalation Risk Scoring  
**GET** `/analytics/escalation_risk`  

Generates an explainable risk score (0–1) per topic based on:
- High negative sentiment  
- Low resolution rate  
- Rapid week-over-week growth  

**Use case:** Prioritize topics that require immediate operational attention.

---

#### 4. LLM-Generated Executive Summary  
**GET** `/analytics/executive_summary`  

Generates a concise, executive-ready summary using an LLM **only after metrics are computed**.  
The model receives structured analytics (trends, risks, sentiment) and converts them into a 2–4 sentence management insight.

**Outcome:** Clear, data-grounded AI summaries without hallucination or unnecessary LLM usage.

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

**Built with ❤️ by Yash Mahajan**
