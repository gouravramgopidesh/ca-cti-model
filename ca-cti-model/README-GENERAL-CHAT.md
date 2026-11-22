# General + CTI chatbot upgrade

This project contains the existing Lab 7 CTI Digest website and MongoDB-backed RAG, with an additional **General chat** mode that answers everyday questions without retrieving unrelated CTI articles.

## Modes
- **General chat (default)**: Qwen2.5 3B via local Ollama; uses MongoDB session history; no web access or automatic device scanning.
- **CTI / Labs**: original MongoDB retrieval mode with source citations, threat-report search, and cybersecurity instructions.

## Windows install
1. **Back up** the existing `ca-cti-model` folder and extract this ZIP into a fresh folder named `ca-cti-model`. The Compose project name is still `lab7-mongodb`, so the existing MongoDB and Ollama Docker volumes are reused. Do not use `docker compose down -v`.
2. Run `START-AI-WINDOWS.bat` in the project folder. It will build the app, pull `qwen2.5:3b` and `all-minilm`, and ingest MongoDB knowledge.
3. Open http://localhost:3019/#assistant. Select **General chat** and ask: `What can you do?`, `Explain Python functions`, `Write a short email`, then try CTI mode for `Latest threats in my database`.
4. If the site loads an old UI, press Ctrl+Shift+R to refresh cached assets.

### If model pull failed
```
docker compose exec ollama ollama pull qwen2.5:3b
docker compose up -d --build
docker compose logs --tail=80 chatbot
```

### Resource tradeoff
`qwen2.5:3b` uses more RAM and disk than `qwen2.5:0.5b`. On low-memory machines change `CHAT_MODEL` in `.env` to `qwen2.5:1.5b` and pull that model first (`docker compose exec ollama ollama pull qwen2.5:1.5b`).

**Limitations:** A local SLM cannot guarantee correct answers to literally anything; it cannot browse live news or inspect a computer. General mode is not sourced; CTI mode provides retrieved citations. Full course coverage requires all course documents ingested. System and security hardening still need verification before production deployment.
