# Standalone Docker project: ca-cti-model

This is a **separate Docker Compose project**, not part of the existing `lab7-mongodb` Docker Desktop group.

## What runs

Docker Desktop group `ca-cti-model` contains four distinct containers:
- `app-1`: CTI website plus integrated chatbot UI, hosted at **http://localhost:3019/#assistant**
- `chatbot-1`: Python FastAPI AI chatbot backend
- `mongo-1`: dedicated MongoDB database, host port 27029
- `ollama-1`: dedicated Ollama language model service

The prior `lab7-mongodb` group remains intact and its named data volumes are not touched. This stack initializes an **independent MongoDB volume** from the included database dump, not a live clone of subsequent edits in the old stack. This is an independent copy of the Lab 7 website, not the old website's port 3000. The chatbot is a separate container inside this dedicated group.

## Start

Open Docker Desktop. From PowerShell in this folder, run `./START-AI-WINDOWS.bat` or `docker compose up -d --build`. The launcher also pulls the 3B model and embedding model and runs ingestion. Avoid double-running the launcher.

Open http://localhost:3019/#assistant. To verify `docker compose ps` and `./RUN-AI-CHECKS.bat`.

## Stop safely

`docker compose stop` stops this group only. `docker compose down` removes these containers but preserves volumes. **Never use `docker compose down -v` unless you explicitly intend to delete this project's MongoDB data and model downloads.**

## Port conflicts

Default ports: website 3019, MongoDB 27029. If another app uses these, change `PORT` and `MONGODB_PORT` via an `.env` file in this folder. Keep secrets out of Git.

## Limits

This starter retains the educational project limitations: answer accuracy is not guaranteed; advanced RAG, labs 1–18 coverage, production security and native indexed `$vectorSearch` still need verification or further work. The hostname used inside Docker Compose is still `mongo` and the database name remains `lab7-mongodb` for compatibility.
