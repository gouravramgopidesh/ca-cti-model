# lab7-mongodb | Lab 7 submission guide

## Start and demonstrate

1. Extract this ZIP (do not run files from inside the archive).
2. Open Docker Desktop and run START-WINDOWS.bat. The first run needs internet for the container images and npm dependencies. The bundled MongoDB archive is restored automatically into a fresh volume. If the old project is still running, stop it first to free ports 3000 and 27018.
3. Open http://localhost:3000. Search a threat title, apply filters, change an article's analyst verdict, and refresh to verify persistence. Open the Sources, IOC and Reports tabs. Synthetic sample indicators are intentionally labeled training data.
4. Open the Lab panel for live BSON and cache metrics. In Compass connect to mongodb://localhost:27018 and select lab7-mongodb.
5. Run RUN-LABS.bat. It creates the Lab 7.1 comparison collections and regenerates only the synthetic workingSet test collection for Lab 7.2. The two cache samples are normally about 10 seconds apart; the first is a baseline, the second gives a delta-based estimate. Live report discovery runs concurrently. Internet failures are recorded rather than treated as successful discovery.
6. Review the new lab71_*.json and lab72_*.jsonl files in evidence/. These are actual measurements from your environment, not predicted values. If desired, run `docker compose exec app npm run working-set` for more samples; Ctrl+C stops it.
7. To stop, run STOP-WINDOWS.bat. Database volumes remain intact.

## Requirement mapping

| Assignment | Implementation / evidence |
|---|---|
| CTI platform, frontend and backend | frontend/, backend/server.js; RSS ingestion in backend/intelligence.js and feeds.js |
| MongoDB dump | database-dump/lab7.archive.gz, restored by labs/01-restore.sh on fresh Docker volume |
| Identify embedded and referenced relationships; explain alternatives | README.md and Lab 7.1 extension; original Word report |
| Average BSON size and 16 MiB verification | GET /api/lab/schema, labs/schema-check.js, Lab dashboard, historical evidence/lab7-schema.json |
| Redesign source / assessment reference | backend/lab71-compare.js creates four isolated comparison collections, with matching query verification and median query times |
| Faster queries and harder updates | LAB71-EXTENSION.md explains joins, indexing, fan-out updates and duplicated snapshots |
| 100,000 approximately 2 KB documents | backend/working-set.js generates synthetic payloads, optionally linked to real report metadata in annualReports |
| WiredTiger cache size, use and cache fit | backend/working-set.js, GET /api/lab/cache; server-wide occupancy and estimated collection fit are distinguished |
| Random reads and changing hit ratio | 1,000 random indexed reads each interval; JSONL cache measurements |
| Monitor every ten seconds and discover new reports | backend/working-set.js and backend/intelligence.js; canonical URL upserts, periodic sync and error recording |
| Indexing | backend/server.js, labs/indexes.js and experiment indexes |
| Search and threat classification | Dashboard and API, with persisted analyst verdict |

## Data sources and interpretation

- CTI Digest: https://ctidigest.com/ — inspiration and public publisher RSS source list. Live classification is analyst-reviewed; keyword-based severity is only a triage aid.
- Annual Security Reports: https://github.com/jacobdjwilson/awesome-annual-security-reports/ — report metadata, not full report PDFs. The performance dataset is synthetic, not 100,000 distinct published reports.
- Instructor reference: https://github.com/sujeetjagtap/NoSQL-Databases-using-MongoDB/tree/main/chapter-07 — could not be retrieved during final packaging, so the supplied assignment screenshots govern the mapping. The provided standalone indexing and schema scripts are project-specific, not copies of the instructor scripts.

The original Word report and original evidence files are retained as historical evidence from the supplied project. The additional benchmark and modified working-set script have not been run against a live MongoDB in the packaging environment. No new performance numbers are asserted. A 100% estimated cache fit does not establish 100% actual collection residency, and the page hit ratio is a teaching approximation, not an exact query-level hit ratio. Publisher reputation and whether an article reports a confirmed threat are different concepts; the analyst verdict addresses the latter.
