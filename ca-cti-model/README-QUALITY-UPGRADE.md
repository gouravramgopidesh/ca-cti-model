# CA CTI chatbot: formatting and context quality update

This update is based on the working **ca-cti-model-retrieval-fixed** stack. It does not change Compose project names, MongoDB volume definitions, Ollama model settings, or the Lab 7 website.

## Changes
- Chat answers use safe DOM-built Markdown: headings, bold, lists, and inline code. No HTML is executed or injected.
- The chatbot supplies previous conversation turns to Ollama only for explicit short follow-up questions. New topics no longer inherit unrelated answers by default. Messages continue to persist in MongoDB.
- Lab-specific questions retrieve the lab's actual MongoDB source excerpts and ask Ollama for a concise evidence-grounded explanation instead of copying an entire README. Raw documented excerpts remain as a fallback if generation fails.

## Installation in Windows PowerShell
1. Preserve the existing `ca-cti-model` directory as a backup. Unzip this full project into its place. Do not delete Docker volumes.
2. From this directory run: `docker compose -p ca-cti-model up -d --build`.
3. Check: `docker compose -p ca-cti-model ps`.
4. Open `http://localhost:3019/#assistant` and click New conversation.

## Test cases
- General: `Who is the Prime Minister of India?`, then `Explain artificial intelligence.` (second answer must not repeat the PM).
- Real follow-up: `What is a MongoDB replica set?`, then `Explain that more simply.`
- Lab RAG: `Explain Lab 17 and how MongoDB vector search works.` (should explain with citations instead of pasting the README).
- Ransomware: `Give prevention, detection and recovery advice for ransomware on Windows.` (formatted bullets and headings).
- Data: `What are the five latest threats stored in MongoDB?` (database records, with appropriate caveats).

No chatbot can guarantee fully correct answers. This version was syntax-tested locally, not exercised against the user's running Windows Docker environment. It does **not** enable native MongoDB indexed vector search, automatically add missing lab source material, or provide access to live web searches.
