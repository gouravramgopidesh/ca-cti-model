# CA CTI model - website fixes

- 18 lab cards with searchable metadata and explicit source availability. Actual project READMEs included where accessible. Claims not backed by actual files are labelled pending.
- Auto routing differentiates ordinary chat and CTI/MongoDB/lab questions, while retaining General/CTI overrides.
- High-priority and active-threat queries retrieve ranked local MongoDB reports and never call unverified reports confirmed incidents.
- Two independent websites: original Lab7 site on port 3000, CA site on port 3019. Only CA site has chatbot.
- Original Docker volumes preserved as long as the Compose project names, mount paths, and volume identifiers are unchanged. NEVER use `docker compose down -v`.
- Native $vectorSearch needs Atlas Local/Atlas config; Community MongoDB fallback is not equivalent.
- Model has no built-in live web access. Current public-officeholder questions need external verification; do not claim that the AI knows real-time news.

## Safe local upgrade (PowerShell)
1. Back up BOTH project folders. Do not delete their database volumes.
2. Extract this archive and copy the CA project files into the existing `ca-cti-model` folder (do not overwrite `.env`).
3. From `ca-cti-model`, run `docker compose -p ca-cti-model up -d --build`, then `docker compose -p ca-cti-model exec -T chatbot python ingest.py`.
4. Verify `http://localhost:3019/#labs18` and `http://localhost:3019/#assistant`.
5. To restore the original Lab7-only site, use the separate lab7 website-only archive and rebuild with `docker compose -p lab7-mongodb up -d --build --remove-orphans` from the original Lab7 folder.
6. Verify `http://localhost:3000`; no Assistant nav should be present.

## Tests
- General: 'What is Python?' -> general answer, not unrelated CTI citations.
- Auto: 'Which threats are high priority in my database?' -> high/critical stored reports, labelled heuristic.
- Labs: 'Explain Lab 17' -> grounded on included lab project README; source references.
- Chat memory: ask follow-up in same session, then reload browser.

No code can guarantee perfect factual answers. Final runtime verification is required on the user's machine.
