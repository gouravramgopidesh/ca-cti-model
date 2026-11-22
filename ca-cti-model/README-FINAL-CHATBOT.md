# ca-cti-model

# Final Assessment — CTI Digest LLM/SLM + MongoDB

## Original Lab 7 preserved
This is the user-supplied Lab 7 project extended with an **embedded assistant in the same dashboard** (`http://localhost:3000/#assistant`). Existing Lab 7 MongoDB data, API routes, container volume and lab artifacts are preserved. Do not use `docker compose down -v`.

## Install / launch on Windows (Docker Desktop required)
1. Extract this entire project to a new folder, back up your earlier Lab 7 project, and stop its previous compose stack **without deleting volumes** (`docker compose down`, NOT `-v`). Avoid running two stacks on port 3000/27018. Reusing the original named volume across different compose project names is **not automatic**: export and restore your original database first if you need its live data. The included database dump initializes a fresh Lab 7 dataset.
2. Run `START-AI-WINDOWS.bat` in this project folder, or execute commands below. First Ollama downloads require internet. Model choice `qwen2.5:0.5b` is lightweight for student hardware.
3. Visit `http://localhost:3000/#assistant` and test a specific CTI question.

```powershell
docker compose up -d --build
docker compose exec ollama ollama pull qwen2.5:0.5b
docker compose exec ollama ollama pull all-minilm
docker compose exec chatbot python ingest.py
docker compose ps
```

To ingest **genuine** Labs 1–18 coursework, put Markdown/TXT/PDF into `chatbot/knowledge/lab01` ... `lab18`, then rerun `docker compose exec chatbot python ingest.py`. This build includes source data from Lab 7; other lab source material is **not in the two uploaded files**, so they are not claimed ingested. Ingestion is idempotent per chunk ID, but document truncation should be reviewed before reimport.

## Data flow
Browser `/#assistant` → Express `/api/chat` same-origin proxy → FastAPI `/chat` → MongoDB `lab7-mongodb` (`articles`, `indicators`, `annualReports`, `chat_knowledge` for embeddings, `chat_sessions` for durable multi-turn memory, `chat_metrics` for latency/health) → Ollama SLM. UI shows source links and a disclaimer.

## Vector search: honest deployment distinction
MongoDB standard Community Server 8.0 **does not provide the `$vectorSearch` aggregation stage**. This Docker Compose uses stored vectors in MongoDB plus **bounded, exact client-side cosine matching** for up to 2500 knowledge records. This delivers vector retrieval but not an indexed native vector-search pipeline. For Atlas/Atlas Local, configure a native `cti_vector_index` on `chat_knowledge.embedding` with matching dimensions, set `VECTOR_INDEX_ENABLED=true`, and use a MongoDB URI to that service. To comply strictly with the professor's native MongoDB vector-search-index requirement, use Atlas/Atlas Local and verify `$vectorSearch` there.

## API
- POST `/api/chat` on Lab 7, JSON `{ "message":"What phishing risks affect Windows?", "platform":"Windows", "session_id":"session123" }`
- GET `/api/chat/health` shows MongoDB, Ollama, knowledge count.
- GET `/api/chat/sessions/session123` restores conversation.
- FastAPI native POST `/chat/stream` provides SSE responses; currently the Lab 7 front end uses the standard non-streaming endpoint.

## Security and safety
No system scans, arbitrary shell execution, or automatic mitigation. External RSS is untrusted; output must be verified with original vendor sources. API enforces 1400-character questions, basic per-IP memory rate limits (12/min), no secrets committed, 8-message history, context size bounds. For real public production deployment add gateway TLS, persistent distributed rate limiting, authentication/session authorization, data retention policy and structured observability. This educational build binds ports only to loopback; do not expose publicly as-is.

## Validate before submission
Run `RUN-AI-CHECKS.bat`; ask a question, refresh browser, confirm chat session restoration; inspect Compass database `lab7-mongodb` collections `chat_knowledge`, `chat_sessions`, `chat_metrics`. Capture actual screenshots. Push the full project to a **PRIVATE** GitHub repo, invite professor, create a PDF with private repo URL and submit it. Do not publish login credentials or API keys.

## Known limits
The uploaded Lab 7 ZIP dates to Nov 16 and could differ from your latest local version. Runtime Docker verification is required on Windows. The advanced optional autonomous-scanning capability is intentionally omitted; no unauthorized changes to devices. Threat lifecycle classification should be evidence-based; the current prompt differentiates the lifecycle and avoids fabricating verification.

## Response relevance correction (v2)
Specific conversational intents (assistant identity, greetings, threat lifecycle, and latest local articles) are handled separately from generic RAG. Latest local reports use MongoDB sort on `publishedAt` and exclude training records. General retrieval requires topical keyword overlap to avoid citing unrelated material; questions with no relevant evidence are labeled as general guidance. Existing responses persist in MongoDB and old faulty responses can be cleared with **New conversation** (without deleting database records). Model qwen2.5:0.5b remains a limited SLM; verify factual answers and consider a stronger model if resources permit.
