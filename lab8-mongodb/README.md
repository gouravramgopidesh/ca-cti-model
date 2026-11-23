# lab8-mongodb
Independent local MongoDB replica-set exercise. No Lab 7 files, database, website or ports are used. Docker Desktop with Linux containers and Compose v2 is required. All scripts run inside Docker; no host Python installation is necessary.

## Run on Windows
1. Extract the ZIP, open `lab8-mongodb` in VS Code, and start Docker Desktop.
2. Run `.\START-WINDOWS.bat` in PowerShell. It starts three data-bearing members, initializes rs0 with mongosh, and starts an unconfigured fourth process for the arbiter exercise. The arbiter is not a member yet.
3. Run `.\RUN-LABS.bat`. Each Python activity pauses after completion; capture the terminal output using Win+Shift+S and insert the genuine screenshot in the corresponding section of `lab8-mongodb-report.docx`. Evidence JSON is saved in `evidence/`.
4. Run `.\STOP-WINDOWS.bat` when finished. This keeps all named volumes. Lab 7 is unaffected.

## Individual commands (after START)
```
docker compose run --rm --no-deps runner activity-8.1/replica-set-init.py
docker compose run --rm --no-deps runner activity-8.1-try-it-yourself/add-arbiter.py
docker compose run --rm --no-deps runner activity-8.2/failover-monitor.py
docker compose run --rm --no-deps runner activity-8.2-try-it-yourself/priority-election.py
```
Run in order. The first activity resets membership to three data members on repeat runs, preserving data. Do not run reconfiguration experiments concurrently. To inspect the shell interactively:
```
docker compose exec mongo1 mongosh 'mongodb://mongo1,mongo2,mongo3/?replicaSet=rs0'
```
Then use `rs.status()`, `rs.conf()`. The accompanying JS scripts demonstrate equivalent shell commands; the Python runner executes the activities automatically, so do not run the JS reconfiguration scripts simultaneously. To manually step down use `rs.stepDown(30,10)` in the replica-set shell and reconnect if necessary.

## Design notes
- Docker DNS names are used, not localhost: each container has its own loopback interface. Each data member has its own named volume. No MongoDB port is published to the host. This is an unauthenticated isolated teaching environment, not a production deployment.
- An arbiter votes but stores no application data and cannot become primary. Three data voters + one arbiter = four votes, quorum three; a two-data-node + arbiter setup has three votes, quorum two, but reduced data redundancy. Three data members without an arbiter are generally preferable here.
- Majority journaled writes and majority reads use collection-level PyMongo concerns. The instructor's reference read_concern keyword on find_one is replaced by ReadConcern on the collection.
- Priority affects election preference, not a guarantee. Record actual first elected primary and any later takeover, including mismatch.
- Reports require actual screenshots; no invented output is included. JSON evidence files are generated at runtime and overwritten per activity on rerun; copy them elsewhere if preserving earlier runs.

## References
Assignment screenshots and supplied reference scripts; https://github.com/sujeetjagtap/NoSQL-Databases-using-MongoDB/tree/main/chapter-08 (not accessible during preparation).
MongoDB docs: https://www.mongodb.com/docs/manual/tutorial/add-replica-set-arbiter/ ; https://www.mongodb.com/docs/manual/reference/command/replsetreconfig/ ; https://www.mongodb.com/docs/languages/python/pymongo-driver/current/connect/connection-targets/
