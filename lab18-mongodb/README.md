# Lab 18 - Comparative Capstone: CTI false-positive review

Independent Docker Compose project. No additional website; no modification to Labs 7–17. The assignment's "transactions" are modeled as threat-feed observations. MongoDB 8.0, Cassandra 4.1 and Neo4j 5.26 Community run on isolated lab volumes; Python runs all tasks. No database ports are published to Windows. The hardcoded Neo4j password is only an internal lab credential, not for production.

## Windows workflow

1. Extract `lab18-mongodb` into your `mongodb-lab` directory. Stop unneeded labs to free memory; Docker Desktop should have roughly 8 GB memory and 10 GB free storage (actual requirements vary). Internet access is needed to pull images and public feed snapshots.
2. Open the folder in VS Code and run `START-WINDOWS.bat`. All four containers should start. Cassandra may take longer than MongoDB.
3. Run `RUN-LABS.bat`. This fetches and freezes the dataset, resets **only Lab18's dedicated data**, loads 100,000 baseline observations in each database, verifies hashes, benchmarks and creates the comparative PDF. The run is substantial; loading and verification are sequential and printed progress is normal. Do not stop the group midway.
4. Run `PUBLISH-DOCKER.bat` after local tests pass. Uses existing Docker Hub credentials. If needed, `docker login` first (browser flow). Image: `gouravram77/lab18-mongodb:1.0`.
5. Run `RUN-PUBLISHED.bat`. Pulls and force-recreates the app from the published tag, with no local build. Reuses the frozen snapshot. The published PDF is `reports/Lab18-published-comparative-report.pdf`; the published digest is in `evidence/published-image.txt`.
6. Submit the published-run PDF with Docker Hub URL. Keep the Compose/source ZIP for demonstration (the runner image is not a self-contained three-database deployment). Stop all four services using the Docker Desktop group. Do not delete volumes.

## Lab 18.1: genuine data, not fake threats

- Primary sources: IPsum daily snapshots (GitHub commit history, when available), blocklist.de all/SSH/mail/Apache/IMAP, ShadowWhisperer Threats, romainmarcoux inbound aggregation and ThreatHive. The app downloads ONLY fixed public feed URLs, never follows or scans an indicator. No malware samples, no active probing.
- An observation is unique per **feed + UTC snapshot day + IP**. Same IP reported by multiple feeds/days intentionally remains multiple observations. A feed may aggregate other feeds; sources are not automatically independent. The baseline must contain 100,000 genuine observations and at least two publishers; an additional 1,000 genuine observations are reserved for timed inserts. No fabricated or duplicated padding. If insufficient, the program fails explicitly and writes `datasets/collection-failure.json`.
- Timestamps are publication (IPsum Git commit time) or download snapshot time, **not attack event times**. Blocklist.de documents a preceding 48-hour report window; an exact incident timestamp is not supplied. Historical GitHub snapshots are optional; if unavailable daily analytics may cover only the current snapshot day. Targets represent reported service categories (SSH, mail, HTTP, IMAP), not identified victims; `unknown` remains unknown. Spread means distinct indicators, network prefixes and publishers by reported target.
- A deterministic round-robin samples available source snapshots in original order. A source's raw byte hash and precise URL are stored in `manifest.json`. Raw upstream lists are not redistributed in the image; frozen normalized dataset `observations.jsonl.gz` is local. Follow the source terms and keep the data private to coursework; never use it as automatic enforcement without validation.
- On repeat runs, the app validates the SHA-256 and reuses the snapshot. To collect a fresh dataset, move `datasets/manifest.json` and `datasets/observations.jsonl.gz` together to a separate folder before rerunning. Do not edit the manifest to force success. Local and published results use the same frozen snapshot by default.

### Schema and benchmarks

- MongoDB: `lab18_capstone.full_threats` with one document per observation; unique id and `(from_source,timestamp,id)` history index. `threats` contains each source's bounded latest 50 rows; writes update both collections. A standalone node does not provide atomic cross-collection writes.
- Cassandra: `threats_by_source` partitioned by `(from_source,day)`, `threats_by_type` partitioned by `(threat_type,day)`, both clustered by descending timestamp and ascending id. One source/day or type/day query is partition-local. Multi-day history and global daily analytics must fan out; no `ALLOW FILTERING`. Writes denormalize into both tables.
- Neo4j: Source, Threat, Indicator, Network, Community nodes; REPORTED, OBSERVES, IN_NETWORK, SUSPICIOUS and IN_COMMUNITY relationships. Uniqueness constraints and range indexes. Shared exact indicator source overlap produces SUSPICIOUS edges between distinct publisher feeds.
- Three read benchmarks (history latest 50, target/spread for one type/day, daily counts across all days) plus real-time insert of 100 genuine held-out observations per run. 10 measured runs/database/operation, rotating DB order; read warmup; include driver/network/result materialization. Compare every read result to baseline; verify full-field hashes before and after insert benchmark across MongoDB, both Cassandra tables and Neo4j. Report final 101,000 count separately from initial 100,000. Throughput is observations per second, not DB statements/s. The bounded MongoDB recent display is separately timed.
- Graph activity: Cypher builds source overlap edges and obtains the top 30 multi-publisher prefixes (at most 100 observations each); weighted projection (same IP=3, shared prefix across publishers=1) uses seeded NetworkX Louvain. Dense groups with repeated indicator frequency above eligible-network median are flagged `needs_review`. Cross-reference the full sampled projection and all flagged members in MongoDB, verify complete fields and store memberships in Neo4j. This is a graph-derived algorithm, not Neo4j GDS; false positives are not automatically confirmed, and zero candidates is a valid outcome. Without labeled ground truth, no accuracy/precision/recall claim is made. Bounded projection and overlapping feeds are limitations.

## Lab 18.2: report

`reports/Lab18-local-comparative-report.pdf` and `reports/Lab18-published-comparative-report.pdf` are generated from measured runtime results. Includes executive summary, architecture, methodology, schema and query forms, latency/throughput table and charts, graph integrity, ergonomics, horizontal scaling, 1M/10M/100M hardware and storage estimates, backups/monitoring/skills, recommendation per access pattern, references and Docker Hub URL. Hardware numbers are illustrative assumptions, not benchmarks. Single-node/RF1/Community results are not equivalent to HA production workloads.

Evidence folders contain `provenance.json`, `environment.json`, `baseline_integrity.json`, `final_integrity.json`, `benchmark_raw.csv`, `benchmark.csv`, `communities.json`, `results.json`, and PNG/SVG charts. Regenerate report from saved evidence without rerunning databases: `docker compose exec -T app python report.py --mode published`.

## References

Instructor chapter: https://github.com/sujeetjagtap/NOSQL-Databases-using-MongoDB/tree/main/chapter-18 (unavailable during preparation; implementation follows complete supplied assignment text).

Source and database documentation links are embedded in the PDF generator. The assignment asks for recent threats; the implementation counts genuine recent reported IP-feed observations rather than 100,000 verified attacks. Confirm interpretation with instructor if they require uniquely timestamped incidents or unique indicators. No separate website. Integration with Lab 7 is a later step, not performed here.

## Validation status at delivery

Code syntax, dataset parser/unit fixtures and report rendering smoke checks can be done without Docker. Live feed acquisition, database connections, benchmark numbers, candidate counts, image build/push/pull and published report require your machine; none are claimed completed here.
