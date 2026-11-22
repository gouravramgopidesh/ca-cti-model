# Lab 14 — Managing Database Services in Production

Independent Compose project; no host ports exposed, no other labs changed. MongoDB 8.0 three-node replica set, Python monitor, webhook receiver and hourly backup scheduler. No Windows background installer or security-policy changes. Local teaching deployment uses no database authentication; do not expose to public networks. Reserve several GB of free disk and RAM.

## Windows workflow
1. Extract the project into mongodb-lab. Open Docker Desktop.
2. Double-click START-WINDOWS.bat (or run it from VS Code PowerShell). Wait for success.
3. Run RUN-LABS.bat. Monitoring verification waits 30 seconds and the benchmark generates 111,000 documents across three isolated databases; duration varies. Check final PASSED and evidence.
4. Run PUBLISH-DOCKER.bat, then RUN-PUBLISHED.bat to verify the actual pulled image. For grading use the Compose file plus published image, not a local rebuild. Existing Compose project is reused; evidence is replaced by the newest successful run.
5. Start/stop the lab group from Docker Desktop. The scheduler and monitor stop together with MongoDB. Do not delete volumes. The scheduler does not run while the lab is stopped.

## 14.1
`activity-14.1/monitor.py` reads serverStatus, connections, opcounters, WiredTiger and replSetGetStatus. Samples logged to logs/metrics.log every 30 seconds during normal operation. Cache hit estimate = 1 - delta pages read into cache / delta pages requested from cache; this uses actual WiredTiger counters, not a nonexistent bytes-read-from-cache counter. First sample or zero requests = N/A; counters reset on server change. Lag = primary optimeDate minus secondary optimeDate. Warning thresholds strictly below 80% and above 10 seconds. `test_alerts.py` records two real samples 30 seconds apart and exercises both threshold breaches with explicitly simulated metrics; real alerts use the same code. Local HTTP receiver persists actual delivered payloads. To use Slack/Discord set WEBHOOK_URL in a local .env and recreate monitor; keep secrets out of images and submissions. External delivery is optional and not tested by the local receiver test.

## 14.2
`backup_verify.py` accepts `--uri` and `--output-dir`. Scheduler performs a full replica-set mongodump --oplog on startup and every hour after completion, storing timestamped directories with completion manifests; successful backup triggers seven-day retention based on UTC directory timestamp. It never deletes unrelated folders or incomplete backups. Benchmark dumps isolated databases containing 1k/10k/100k deterministic ~1 KB documents, corrupts verified/value fields, restores only the intended namespace with --drop, checks every original field and count, checks index recreation and hashes. Temporary benchmark databases are dropped after verification; dumps remain. RPO target 3600 seconds assuming successful uninterrupted hourly backups (actual interval can exceed an hour by job duration; stopped/failed jobs invalidate target). RTO estimate = restore duration + measured fresh application client startup/health read; not a full production outage measurement. Recovery in benchmark is to the quiescent backup snapshot; hourly full dump includes oplog, which supports consistent snapshot recovery with full mongorestore --oplogReplay into a separate replica set. Arbitrary-time recovery requires continuous oplog archiving and is not claimed here. No actual arbitrary-time PITR or full oplog restore test included. Manual backup uses the same scheduler job; retention test creates synthetic old/new directories, and hourly schedule is checked without waiting one hour. For actual hourly evidence leave lab running and inspect logs/backup-scheduler.jsonl.

## Evidence / grading
- logs/metrics.log, verification-metrics.log, webhooks.jsonl, backup-scheduler.jsonl
- evidence/14.1-monitoring.json, 14.2-benchmark.json and CSV, 14.2-verification.json
- backups/ hourly, manual and benchmarks; do not upload backup data to Docker Hub.
- Actual benchmark times are generated on your machine. No fabricated numbers.
- PDF submission should include actual Docker Hub URL and measured evidence; prepare after runtime verification.

Instructor: https://github.com/sujeetjagtap/NoSQL-Databases-using-MongoDB/tree/main/chapter-14 (could not retrieve during preparation; supplied assignment screenshots used).
MongoDB docs: https://www.mongodb.com/docs/database-tools/mongodump/ and https://www.mongodb.com/docs/database-tools/mongorestore/.
