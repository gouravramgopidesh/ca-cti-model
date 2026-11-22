# CA CTI Model — AI-Powered Cyber Threat Intelligence Assistant

**Final Assessment:** Building and Deploying an LLM/SLM-Backed Chat Application on MongoDB  
**Course:** 23CSE528 — NoSQL Database using MongoDB  
**Repository:** https://github.com/gouravramgopidesh/ca-cti-model

## 1. Project overview

CA CTI Model is a Dockerized cyber threat intelligence (CTI) application integrating an Express-powered web dashboard, a Python FastAPI chatbot, MongoDB, and a locally hosted Ollama language model. It supports ordinary conversational questions, questions about MongoDB Labs 1–18, and evidence-backed questions about locally stored threat-intelligence articles. The application is designed for educational demonstration rather than autonomous security operations.

The chatbot provides platform-aware security guidance and helps explain the distinction between **anticipated, active, evolving, and resolved threats**. Threat reports must still be validated against original advisories: an ingested news article does not automatically prove that an attack is active.

## 2. Main features

- **CTI dashboard:** Browse, search, filter, and review stored security articles and their sources.
- **AI assistant:** General-purpose chat using the local `qwen2.5:3b` model through Ollama; no hosted LLM API key required.
- **MongoDB-backed RAG:** Ingest source text and retrieve relevant chunks for CTI and course questions.
- **Conversation history:** Store user and assistant messages in MongoDB using session identifiers and timestamps.
- **Labs 1–18 overview:** A dedicated website section with summaries and available source material.
- **Platform-aware advice:** Discuss Windows, Linux, macOS, Android, iOS, and other platforms when supported by available information.
- **Containerized stack:** Independent website, chatbot backend, MongoDB, and Ollama services, with health checks and persistent volumes.

> **Scope note:** The website can show an overview of all 18 labs, but its detailed RAG coverage depends on which original lab documents have been supplied and ingested. The repository does not necessarily contain every separate Lab 1–18 project.

## 3. Architecture

```text
Browser — http://localhost:3019
      |
      v
Express web app (app container; port 3000 internally)
      |                  \
      | CTI API           \ same-origin chatbot API
      v                    v
MongoDB (mongo) <----> FastAPI (chatbot) ----> Ollama (ollama)
  |  CTI data              |                    |
  |  knowledge chunks      |                    +-- qwen2.5:3b
  |  chat sessions         +-- embedding-based retrieval
  +-- metrics                                 +-- all-minilm
```

Docker Desktop contains a separate Compose project called `ca-cti-model` with four services:

| Service | Purpose | Host access |
| --- | --- | --- |
| `app` | CTI website and integrated assistant interface | `http://localhost:3019` |
| `chatbot` | FastAPI RAG and conversation backend | Internal port `8000` |
| `mongo` | CTI collections, knowledge chunks and chat history | `127.0.0.1:27029` |
| `ollama` | Local language model and embedding model | Internal port `11434` |

**The original Lab 7 deployment remains separate:** `lab7-mongodb` serves its original CTI website at `http://localhost:3000`, while `ca-cti-model` serves the CTI website **with** the chatbot and Labs section at `http://localhost:3019`.

## 4. Requirements

- Windows 10/11 with Docker Desktop and Docker Compose enabled.
- Sufficient free RAM and disk space for MongoDB, the Node/Python images, and Ollama model weights.
- Internet access for the **first** download of Docker images, local models, and optional live CTI feed synchronization.
- A modern browser for the CTI interface.

The LLM runs **inside the Ollama Docker container**; installing Ollama separately on Windows is not required.

## 5. Getting started — Windows

1. Open Docker Desktop.
2. Open the `ca-cti-model` project folder in VS Code or PowerShell. Make sure the directory contains `docker-compose.yml`.
3. Run the following commands:

```powershell
cd "C:\mongodb-projects\ca-cti-model"
docker compose -p ca-cti-model up -d --build
docker compose -p ca-cti-model exec -T ollama ollama pull qwen2.5:3b
docker compose -p ca-cti-model exec -T ollama ollama pull all-minilm
docker compose -p ca-cti-model exec -T chatbot python ingest.py
docker compose -p ca-cti-model ps
```

Alternatively, double-click **`START-AI-WINDOWS.bat`**, which performs startup, model downloads, and knowledge ingestion.

4. Open the website and explore:

   - **Dashboard:** http://localhost:3019
   - **AI assistant:** http://localhost:3019/#assistant
   - **Labs 1–18:** http://localhost:3019/#labs18

5. In MongoDB Compass, connect to `mongodb://127.0.0.1:27029` and inspect database `lab7-mongodb`.

The first start may initialize the CA project's own MongoDB volume from the bundled Lab 7 database archive. It does **not** automatically synchronize later edits made to the separate Lab 7 deployment.

### Verify the running system

```powershell
docker compose -p ca-cti-model ps
docker compose -p ca-cti-model exec -T chatbot python -c "from urllib.request import urlopen; print(urlopen('http://127.0.0.1:8000/health',timeout=10).read().decode())"
```

Or run **`VERIFY-AND-INGEST-WINDOWS.bat`**, which rebuilds the stack if needed, pulls the models, ingests knowledge, checks readiness and executes basic chatbot tests.

## 6. MongoDB data and RAG workflow

1. **Ingestion:** `chatbot/ingest.py` reads supplied knowledge files and selected local CTI records, splits content into chunks, computes embeddings and stores them in MongoDB.
2. **Retrieval:** For a CTI or Lab question, the backend searches stored knowledge for relevant evidence.
3. **Generation:** Relevant context is passed to the Ollama language model to produce an answer.
4. **Conversation storage:** User and assistant exchanges are written to `chat_sessions` for session-based follow-up and review.

The MongoDB database includes collections such as `articles`, `sources`, `indicators`, `annualReports`, `chat_knowledge`, `chat_sessions`, and `chat_metrics` (depending on startup and ingestion state).

**Vector-search distinction:** In the supplied local MongoDB Community Docker configuration, embeddings are persisted in MongoDB, but retrieval may use application-side similarity calculations. **Do not describe this setup as native indexed MongoDB `$vectorSearch` unless you configure and verify a supported deployment such as MongoDB Atlas / Atlas Local.**

## 7. Labs 1–18 and assessment integration

The **Labs 1–18** website section summarizes the coursework and links to information available within the CA project. Main topics include foundational NoSQL concepts; MongoDB connectivity, CRUD, schema design, queries, aggregation and indexing; replica sets, failover and sharding; database security and operational monitoring; application-oriented MongoDB use; vector search and retrieval-augmented generation; and the final comparative capstone.

The final assessment particularly draws on:

| Prior exercise | Concept used in CA CTI Model |
| --- | --- |
| 2 | MongoDB setup and client connectivity |
| 4–6 | Queries, aggregation and indexing principles |
| 12 | Environment-variable configuration and security practices |
| 13 | Docker Compose deployment and health checks |
| 14 | Monitoring and operational readiness |
| 17 | Embeddings, vector retrieval and RAG |

Detailed explanations require the corresponding source documents to be present in `chatbot/knowledge/` and re-ingested. The website's lab summaries are not equivalent to including all original lab project directories.

## 8. Demonstration questions

Use **New conversation** to test independent topics; choose the appropriate chat mode if the automatic mode picks the wrong context.

| Test | Example question | What to check |
| --- | --- | --- |
| General chat | `What is artificial intelligence?` | Relevant explanation, not unrelated previous answers |
| Follow-up | `What is a MongoDB replica set?` then `Explain that more simply.` | Uses the preceding topic |
| Local CTI | `What are the five latest articles stored in MongoDB?` | Uses local records and differentiates reports from confirmed active threats |
| Lab material | `Explain Lab 17 and MongoDB vector search.` | Explains course content and identifies retrieved evidence when available |
| Platform advice | `How can I protect Windows from ransomware?` | Prevention, detection and recovery guidance |
| Threat lifecycle | `Explain anticipated, active, evolving and resolved threats.` | Correctly distinguishes four threat states |
| Memory | Ask a question, refresh/reopen the session, and inspect MongoDB `chat_sessions` | Checks message persistence; explicit fact memorization is a separate feature |

**Known limitation:** A small local language model can produce inaccurate, repetitive or unsupported answers. RAG improves access to project sources but does not guarantee correctness or live web knowledge. Always verify critical answers against the underlying records and publisher advisories.

## 9. Project structure

```text
ca-cti-model/
├── backend/                  Express routes, feeds, CTI ingestion and analytics
├── chatbot/
│   ├── main.py               FastAPI chatbot implementation
│   ├── ingest.py             Knowledge ingestion
│   ├── knowledge/             Available Lab and CTI source texts
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                 CTI website, assistant UI and Labs 1–18 page
├── labs/                     Lab 7 scripts and database checks
├── evidence/                 Report and experiment evidence
├── database-dump/            Bundled Lab 7 restore archive (review before sharing)
├── Dockerfile                Express app image
├── docker-compose.yml        Four-service Docker application
├── .env.example              Example host-side configuration (no credentials)
├── START-AI-WINDOWS.bat      Start services, pull models and ingest documents
├── VERIFY-AND-INGEST-WINDOWS.bat
├── RUN-AI-CHECKS.bat         Chatbot checks
└── README.md                 Project documentation
```

## 10. Security and limitations

- Use `.env` or a proper secret manager for credentials. **Never commit `.env`, API keys, tokens or passwords.**
- This is an **educational local deployment**; it is not hardened for unrestricted public hosting.
- HTTP service ports are bound to the loopback interface in the provided Compose file. Use HTTPS, authentication, access control, robust rate limiting, audit logging, and a secrets manager for production exposure.
- Do not treat heuristic severity labels or model-generated classifications as confirmed threat intelligence.
- The app does **not** autonomously scan devices, exploit vulnerabilities or apply system fixes.
- Review `database-dump/`, `evidence/`, and old backup files before publishing the repository publicly.

## 11. Stopping safely

```powershell
# Stop just the CA project containers (data is retained)
docker compose -p ca-cti-model stop

# Or remove CA containers/networks while retaining named volumes
docker compose -p ca-cti-model down
```

**Never use `docker compose down -v` unless you intentionally want to delete this project's MongoDB and Ollama volumes.** Do not delete the separate original `lab7-mongodb` project to stop the CA application.

## 12. Submission

**Project repository:** https://github.com/gouravramgopidesh/ca-cti-model

The assignment requests a **private GitHub repository**, a faculty collaborator invitation, and a **PDF containing the repository URL**. Check with the instructor before using a public repository. Include a working source checkout, Docker instructions, and actual screenshots/evidence of the tested features. Avoid publishing private data or credentials.

---

**Course project disclaimer:** This system is intended for learning and demonstration. Generated text and ingested third-party feeds require independent verification before being used for operational security decisions.
