# lab7-mongodb — MongoDB Labs 7.1 and 7.2

lab7-mongodb is a MongoDB learning project with an Express API and browser dashboard. It demonstrates threat-intelligence feed ingestion, search and analyst classification, document modeling with `$bsonSize`, and WiredTiger working-set monitoring.

## Quick start — Windows final submission

Extract the ZIP, open Docker Desktop, and double-click `START-WINDOWS.bat`. The final package uses a separately named Compose project and initializes a **new** MongoDB volume from the included dump (including the working set). Existing volumes are never overwritten. Open `http://localhost:3000`. If those host ports are already occupied, stop the previous project or configure different ports in `.env` before running. The Windows launcher opens port 3000 by default.

Double-click `RUN-LABS.bat` to run Lab 7.1 and the two-sample Lab 7.2 exercise. New evidence is written directly into the host `evidence/` folder. For continuous monitoring run `docker compose exec app npm run working-set`. This regenerates only the workingSet test collection. Stop with Ctrl+C.

`STOP-WINDOWS.bat` stops this project without deleting its database. See `SUBMISSION-CHECKLIST.md` and `LAB71-EXTENSION.md` for the final requirements mapping and experiment.

## Data provenance and limitations

- Live article records are imported from public RSS feed URLs listed in the client source of [CTI Digest](https://ctidigest.com/). The project reads those publisher feeds directly; CTI Digest does not expose a documented API used here. Articles are stored with their original publisher URL, an ingestion source, and `isTrainingData: false`.
- Article severity/category use simple keyword heuristics and confidence is a fixed placeholder (55), not publisher-provided or verified threat verdicts. An analyst must review each item before acting on it.
- Bundled example articles and indicators are synthetic and visibly labeled `SAMPLE`. They are not actionable IOCs or claims about real campaigns. CTI Digest's RSS articles generally do not provide a normalized IOC dataset.
- Annual report metadata is discovered from the public [Awesome Annual Security Reports](https://github.com/jacobdjwilson/awesome-annual-security-reports/) repository file tree.
- Feed availability, RSS formats, and upstream content can change. A failed source is reported; existing database data is retained.

## Run locally

Requirements: Node.js 18+ and MongoDB 6+ running locally, or an accessible MongoDB URI.

```powershell
npm install
Copy-Item .env.example .env
npm run seed
npm start
```

Open <http://localhost:3000>. Do not open `frontend/index.html` directly: the frontend and API use root-relative URLs that require the Express server.

`npm run seed` **recreates the demo collections** (`articles`, `sources`, `indicators`, and `annualReports`) and then attempts a live sync. Back up any data you need first. To add newly available RSS articles and annual reports without reseeding, run `npm run sync-cti`, or use **Sync intelligence** in the dashboard. The app also attempts a sync after it starts. Set `MONGODB_URI`, `DB_NAME`, and `PORT` in `.env` as needed. Live sync requires outbound HTTPS access from the machine running Node.

## Run with Docker and connect with MongoDB Compass

Requirements: Docker Desktop with Docker Compose enabled.

From the project directory:

```powershell
docker compose up --build -d
docker compose ps
```

Open <http://localhost:3000>. The first launch builds the Node app image, starts MongoDB, waits for MongoDB's health check, and restores the bundled archive into a new volume before the app creates indexes and syncs live data. The restore does not repeat on later starts. MongoDB data persists in the named `mongo_data` volume across container restarts.

In MongoDB Compass, create a new connection using:

```text
mongodb://localhost:27018
```

Open the `lab7-mongodb` database and its `articles`, `sources`, `indicators`, and `annualReports` collections. Port `27018` is intentionally used on the host to avoid colliding with a MongoDB installation already listening on `27017`; inside Compose, the app connects to `mongo:27017`. To use another host port, set `MONGODB_PORT` in `.env` before starting.

Useful Docker commands:

```powershell
docker compose logs -f app
docker compose logs -f mongo
docker compose exec app npm run sync-cti
docker compose exec app node backend/working-set.js --once
docker compose exec app npm run working-set
docker compose down
```

The one-shot working-set mode inserts the dataset and emits two samples approximately 10 seconds apart, waits for its initial report-discovery request to finish, then exits; use it for a quick lab run. The regular working-set command runs continuously; stop it with Ctrl+C. `docker compose down` stops containers but keeps database contents. **Do not use `docker compose down -v` unless you intentionally want to permanently delete the MongoDB volume and all its data.** The sample Compose database has no authentication and publishes a host port, so use it only on a trusted local machine; do not expose it to a network or use it for production.

## Lab 7.1 — Analyze the schema

### Collections and relationship choices

| Relationship / fields | Design | Why |
| --- | --- | --- |
| `articles.sourceId` → `sources.name` | Reference to the canonical source catalog | Many articles can come from one publisher; canonical URL/type/reliability metadata is managed in one place. |
| `articles.source` | Embedded publisher snapshot | The feed needs publisher name and URL with the article. This avoids a lookup to render article provenance, at the cost of duplicate, potentially stale publisher metadata. |
| `articles.sourceAssessment` | Embedded analyst verdict | The bounded `verdict` and review time are read with the article, so feed triage does not need an assessment lookup. This verdict assesses the reported activity, not whether the publisher itself is malicious. |
| `indicators` → article/source provenance | Reference through source name; extend to article ObjectIds in production | Indicators can recur across many reports and need independent search/update. A bounded `indicatorSnapshots: [{value, kind, confidence}]` embedded in each article makes article detail reads faster, but complicates cross-article IOC search and consistency. |
| `annualReports` → publisher | Publisher name/URL snapshot | The external index supplies report and publisher data together. A separate publisher collection would reduce repetition but require lookups. |
| `articles.tags`, severity, category, classification | Embedded scalars and bounded arrays | These values are small and normally read with the article. |

The analyst control on each feed card cycles the embedded `sourceAssessment.verdict` and the compatible `classification` field through `confirmed-threat`, `benign`, and `needs-review`. This is an assessment of the report's threat activity; it does **not** declare the publisher to be a threat actor or judge publisher trustworthiness. The canonical publisher relationship remains referenced while a small publisher snapshot is embedded on each article.

### Measure document sizes

The live Lab panel aggregates `$bsonSize` for `articles`, `sources`, `indicators`, and `annualReports`, showing average/minimum/maximum size and comparing the largest measured document with 16 MiB (16,777,216 bytes). Run the same check in `mongosh`:

```javascript
db.articles.aggregate([
  { $project: { bytes: { $bsonSize: "$$ROOT" } } },
  { $group: {
      _id: null,
      count: { $sum: 1 },
      averageBytes: { $avg: "$bytes" },
      maxBytes: { $max: "$bytes" },
      minBytes: { $min: "$bytes" }
  } }
])
```

Repeat for each collection to verify no measured document approaches MongoDB's 16 MiB BSON document limit. The dashboard uses live database measurements rather than hard-coded size results.

## Lab 7.2 — Working set and WiredTiger

Run:

```powershell
npm run working-set
```

The script saves JSONL evidence automatically and recreates only the `workingSet` collection, inserts 100,000 documents with an approximately 1,900-character synthetic payload plus a reference to annual-report metadata when available, measures its actual BSON bytes, creates a `seq` index, and performs 1,000 random indexed reads per sample. It prints a sample about every 10 seconds and syncs CTI RSS articles plus annual reports every 10 minutes by default (`REPORT_SYNC_INTERVAL_MS` can change the sync interval).

The output includes:

- `bytes currently in the cache` and `maximum bytes configured` from `db.serverStatus().wiredTiger.cache`.
- The BSON size of the test collection and an **estimated cache-fit percentage** based on configured WiredTiger capacity versus collection BSON size.
- Deltas for pages read into cache and pages requested from cache, plus a **teaching approximation** of hit percentage: `1 - (delta pages read into cache / delta pages requested from cache)`.

WiredTiger counters and cache occupancy are server-wide, not collection-specific. The fit percentage is a capacity estimate, not a direct measurement of what fraction of this collection is resident in memory. Indexes, other collections, allocator overhead, compression, and other databases also affect actual cache usage. A user with `serverStatus` privilege is required. Stop the script with Ctrl+C.

## Search, classification, and API

- `GET /api/articles?q=&severity=&category=` — search and filter the feed.
- `PATCH /api/articles/:id/classification` — save the analyst threat verdict, including its embedded `sourceAssessment`.
- `GET /api/sources`, `GET /api/indicators?q=` — source catalog and IOC table.
- `GET /api/lab/schema`, `GET /api/lab/cache` — BSON size and WiredTiger metrics.
- `POST /api/intelligence/sync` — import unseen CTI RSS articles and annual security reports.
- `GET /api/reports`, `POST /api/reports/discover` — annual report library and standalone report discovery.
- `GET /api/health` — database connection status.

## Project layout

```text
frontend/                  Dashboard HTML, CSS, and JavaScript
backend/server.js          Express API and dashboard server
backend/data.js            Clearly labeled synthetic training records
backend/feeds.js            RSS endpoints listed by CTI Digest
backend/intelligence.js    RSS/report importing and MongoDB upserts
backend/seed.js             Demo data and index setup
backend/sync.js             Non-destructive live-data sync command
backend/working-set.js      Lab 7.2 generator, cache monitor, and periodic report sync
Dockerfile                 Node web app image
docker-compose.yml         MongoDB and app services with persistent storage
.dockerignore              Excludes local secrets and dependencies from image builds
lab7-mongodb-report.docx  Word-format lab report with measured results and run instructions
```

The submission ZIP includes the original Word report alongside the source project. Its collection counts and cache measurements are a snapshot from report preparation; refresh them after changing or re-syncing the dataset.
