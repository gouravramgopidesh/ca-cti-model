# Lab 7.1 — Referencing versus embedding experiment

The existing application already implements a hybrid publisher reference and embedded snapshot, plus an embedded analyst verdict. This separate experiment makes the before/after comparison explicit without modifying the application collections.

## Run

From the existing project root, with the same `.env` and running MongoDB instance:

```powershell
node backend/lab71-compare.js
```

For Docker, after rebuilding the app image to include the new script:

```powershell
docker compose up --build -d
docker compose exec app node backend/lab71-compare.js
```

The script reads existing articles and creates four uniquely named `lab71_*` collections in the same database. It never reseeds or deletes production collections. Open these collections in Compass to inspect the designs. Each run creates additional collections; delete only the experiment collections you no longer need. The JSON evidence is saved under `evidence/` (automatically persisted to the host through the Docker evidence bind mount).

## Before and after

Referenced article: `{title, sourceId, assessmentId}`. The canonical source stores publisher details, and the assessment stores the analyst's verdict for that article. References avoid repeating publisher metadata and permit independent assessment management. Two `$lookup` stages resolve the source and verdict.

Embedded article: `{title, source: {name, url, type, reliability}, sourceAssessment: {verdict, reviewedAt}}`. The article contains the data needed to show its origin and assess whether the reported activity is an actual threat. The verdict is per article; a publisher is not labeled malicious merely because it reports a threat. Synthetic training records remain marked and are not actual threat evidence.

## Query and update trade-offs

- Article detail and verdict filtering can avoid joins with embedding. An index on `sourceAssessment.verdict` supports direct filtering. The referenced design also has an indexed assessment verdict and reference fields; alternative join orders may perform differently.
- Publisher metadata changes are a single canonical update in the referenced design. Embedded publisher updates require updating all affected snapshots, or intentionally retaining historical metadata.
- Per-article verdict changes are single-document updates in either design, but embedding makes reading the article and its verdict together straightforward. A separate assessment history may be preferable for unbounded audit trails.
- Embedding repeats publisher metadata and increases article size. Compare the total BSON bytes of all referenced experiment collections against the embedded collection, not just the article sizes. BSON bytes exclude indexes and storage compression.

## Evidence

The script checks equivalent query outputs, measures 20 alternating timed runs after warm-up for each verdict and one article-detail query, and reports median end-to-end milliseconds. It also uses `$bsonSize` to report count, mean, maximum, total and maximum as percentage of the 16 MiB limit for each experiment collection. Do not claim embedding won unless your actual measurements support it. Empty result sets should be identified in your discussion. The benchmark is a controlled snapshot, not a universal performance guarantee.

The original dashboard is preserved; Lab 7.2 now also saves fresh JSONL evidence directly to the host. For the original production schema size results use the existing Lab panel; the experiment measures the additional collections separately.
