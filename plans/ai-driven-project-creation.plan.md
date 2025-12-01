# AI-Driven Continuous Monitoring – Implementation Plan

## Table of Contents
- [Vision](#vision)
- [Core Workflow](#core-workflow)
- [Architecture](#architecture)
  - [1. Data Model (Hybrid Schema in Cloud SQL)](#1-data-model-hybrid-schema-in-cloud-sql)
  - [2. AI Ingestion Agent (Backend)](#2-ai-ingestion-agent-backend)
  - [3. Report Templates (Frontend)](#3-report-templates-frontend)
  - [4. Chat-to-Configure UI](#4-chat-to-configure-ui)
- [Implementation Steps](#implementation-steps)
  - [Phase 1: Backend Foundation](#phase-1-backend-foundation)
  - [Phase 2: AI Ingestion Logic](#phase-2-ai-ingestion-logic)
  - [Phase 3: Frontend & Chat UI](#phase-3-frontend--chat-ui)
  - [Phase 4: Project Report Templates](#phase-4-project-report-templates)
- [Risks & Mitigations](#risks--mitigations)
- [Current Status](#current-status)
- [Next Steps](#next-steps)

## Vision
Transform Jaltol into an intelligent data analyst. Instead of forcing users to match a rigid schema, we use AI to understand their diverse CSVs (10-100 columns) and generate interactive reports via a conversational interface.

## Core Workflow
1.  **Upload**: User uploads raw CSVs (Wells, Time Series, etc.).
2.  **AI Analysis**: LLM analyzes headers/sample rows to identify "Core Fields" (Lat/Lon, Date, Value) and "Context Fields".
3.  **Conversation**: AI confirms mappings with user ("Is 'Depth_M' your water level?").
4.  **Configuration**: AI suggests suitable Report Templates based on data shape.
5.  **Visualization**: Frontend renders interactive reports based on the AI-generated config.

## Architecture

### 1. Data Model (Hybrid Schema in Cloud SQL)
We need a schema that enforces *some* structure (for maps/charts) but allows infinite flexibility.

*   `CMProject`: Metadata (owner, name, description, visibility, slug).
*   `RawDataset`: Stores the original CSV file, AI-generated mapping JSON, and ingestion status.
*   `UnifiedObject` (implemented):
    *   Core fields: `external_id`, `latitude`, `longitude`, `name`.
    *   `extra_data`: JSONB for all site-specific attributes.
*   `UnifiedTimeSeries` (implemented):
    *   Core fields: `timestamp`, `value`, `metric`.
    *   `extra_data`: JSONB for per-reading metadata (sensor_id, quality_flag, etc.).
*   `MetricCatalog`: Normalizes metric metadata for all projects.

### 2. AI Ingestion Agent (Backend)
*   **Role**: The "Translator".
*   **Input**: CSV Headers + First 5 rows.
*   **Task**:
    *   Identify `Latitude`, `Longitude`, `Date`, `Value` columns using fuzzy matching.
    *   Categorize other columns (Categorical, Numerical, Text).
    *   Generate a `ColumnMapping` object.
*   **Tech**: Gemini Pro (via Vertex AI or Studio API).

### 3. Report Templates (Frontend)
Pre-built React components that accept a `config` object.

*   **Template A: Site Snapshot (Map)**
    *   Config: `{ lat_col, lon_col, color_by_col, filter_cols[] }`
*   **Template B: Time-Traveler (Heatmap)**
    *   Config: `{ lat_col, lon_col, date_col, value_col }`
*   **Template C: Impact Analyzer (Bar/Line)**
    *   Config: `{ date_col, value_col, intervention_date }`
*   **Template D: Correlation Detective (Scatter)**
    *   Config: `{ x_axis_col, y_axis_col, group_by_col }`

### 4. Chat-to-Configure UI
*   A chat interface where the user interacts with the "Jaltol Analyst".
*   **User**: "Show me a map of wells."
*   **AI**: "Sure. I'll use 'Lat_N' and 'Long_E' for coordinates. Do you want to color the points by 'Status' or 'Depth'?"
*   **User**: "Status."
*   **AI**: *Generates Config for Template A and renders it.*

## Implementation Steps

### Phase 1: Backend Foundation
**Status:** Completed (deployed to local Django server, migrations applied).

- [x] Created `continuous_monitoring` Django app and registered URLs under `/api/cm/`.
- [x] Defined hybrid models (`CMProject`, `RawDataset`, `UnifiedObject`, `UnifiedTimeSeries`, `MetricCatalog`) with JSONB flexibility.
- [x] Created authenticated project CRUD viewsets plus `upload_dataset` action that persists files to `cm_uploads/...` and marks dataset status.

**Manual Tests**
1. ✅ `python manage.py makemigrations && python manage.py migrate` (verifies schema).
2. ⛔ `POST /api/cm/projects/` with auth token → expect `201`.
3. ⛔ `POST /api/cm/projects/{id}/upload_dataset/` with CSV multipart body → expect `201` with dataset metadata.

### Phase 2: AI Ingestion Logic
**Status:** Completed (needs continuous validation with live Vertex AI credentials).

- [x] Implemented `AIAnalysisService` (Gemini Pro prompt using first 10 CSV rows) that stores mapping and transitions dataset status to `ANALYZED`.
- [x] Added `POST /api/cm/datasets/{id}/analyze/` route that invokes the service and returns JSON mapping.
- [x] Added `POST /api/cm/datasets/{id}/confirm/` route plus `ETLService` that ingests snapshot or time-series data into unified tables.

**Manual Tests**
1. ⛔ Upload a dataset, then call `POST /api/cm/datasets/{id}/analyze/` → expect JSON mapping persisted on `RawDataset`.
2. ⛔ Send `POST /api/cm/datasets/{id}/confirm/` with (optionally edited) mapping → expect `UnifiedObject`/`UnifiedTimeSeries` rows created and dataset status `INGESTED`.
3. ⛔ Run `python manage.py shell` to verify row counts and inspect `dataset.error_message` remains empty.

### Phase 3: Frontend & Chat UI
**Status:** In Progress (UI skeleton exists, needs API wiring + manual verification).

- [ ] Build `ChatInterface` component with authenticated session context (pending final UX polish).
- [ ] Implemented baseline "Upload & Analyze" flow in chat; needs local API target + optimistic UI updates.
- [ ] Display AI mapping suggestions within confirmation drawer (UI stub exists; wire to `/api/cm/datasets/{id}/analyze/` response).

**Manual Tests (Planned)**
1. From `ChatInterface`, upload CSV → ensure frontend calls `POST /api/cm/projects/{id}/upload_dataset/` against local dev API.
2. Observe AI mapping message and confirm selection triggers `/confirm/` endpoint; verify UI surfaces ingestion success.
3. Refresh page → dataset list persists (ensures state sync with backend).

### Phase 4: Project Report Templates (in components/project-templates)
**Status:** Not Started (awaiting confirmed configs from chat workflow).

- [ ] Build `MapTemplate` (Leaflet/Mapbox) fed by `UnifiedObject` API.
- [ ] Build `ChartTemplate` (Recharts/Chart.js) for time-series display.
- [ ] Connect Chat AI to template config generation + runtime rendering.

**Manual Tests (Planned)**
1. Select Template A ("Site Snapshot") → expect map pins colored as configured.
2. Switch to Template C ("Impact Analyzer") → verify ingestion results plotted for chosen intervention date.
3. Run Lighthouse-style smoke check to ensure components lazy-load and do not block chat UI.

## Risks & Mitigations
*   **AI Hallucination**: AI might map 'Well_ID' to 'Latitude'.
    *   *Mitigation*: User *must* confirm the mapping before data ingestion.
*   **Data Volume**: 100 columns x 10k rows = JSONB bloat.
    *   *Mitigation*: Store raw CSVs in GCS; only ingest "active" columns into Postgres if needed, or use efficient JSONB indexing.
*   **Cost**: LLM tokens.
    *   *Mitigation*: Only send headers + 5 rows, not the whole file.

## Current Status
*   **Plan**: Pivoted to AI-Driven approach with hybrid schema + AI ingestion.
*   **Completed**: Backend foundation and ingestion APIs are live locally; chat UI groundwork exists.
*   **Blocked**: Frontend uses production `VITE_API_URL`, so local file uploads never reach dev API.
*   **Manual Validation**: Backend endpoints tested via curl/Postman; frontend end-to-end flow pending.

## Next Steps
1. Update `JaltolUI/.env.local` so `VITE_API_URL=http://127.0.0.1:8000/api` during local development; restart Vite dev server.
2. Re-run Phase 3 manual tests to confirm upload/analyze/confirm flow against local API.
3. Instrument chat UI with explicit success/error to surface ingestion failures quickly.
4. Begin Phase 4 template builds once ingestion configs render successfully in UI.
