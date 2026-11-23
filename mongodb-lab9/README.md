# mongodb-lab9
Independent Chapter 9 lab. No dependency on the Lab 7 website or Lab 8 containers. Three voting data-bearing MongoDB 8.0 nodes, no arbiter, no published host ports. Uses the Lab 8 replica-set pattern and a status observer adapted to network partitions.

## Windows
Open this folder in VS Code with Docker Desktop running. Run ` .\START-WINDOWS.bat`, then ` .\RUN-LABS.bat`. Press a key at each pause. The 9,000 measured individual writes may take time, especially with journaling. ` .\STOP-WINDOWS.bat` stops containers without deleting volumes. Do not use down -v. Each benchmark uses unique IDs; evidence JSON/CSV files for 9.1 are replaced on rerun; 9.2 logs append UTC events.

## Lab 9.1
1,000 sequential inserts for each of w:1, w:majority, w:all, then repeat with j:true and j:false. In MongoDB w:all is not a predefined mode; numeric w:3 is equivalent on this three-data-node set. Default journaling is left unspecified for the first experiment. j:false does not disable server journaling; it changes acknowledgment requirements. Total seconds and mean milliseconds are measured using perf_counter; warm-up excluded. Compare CSV results; no assumed speedup. A majority write waits for two votes, w:3 for all three. Higher acknowledgment generally costs latency but depends on the system. See https://www.mongodb.com/docs/v8.0/reference/write-concern/.

## Lab 9.2
The host PowerShell script isolates only lab9 containers via Docker network disconnect. A Python observer polls each member's hello and replica status and records UTC timestamps, including unreachable states. First isolate one secondary, test w:1 and majority, hold for at least 30 seconds, reconnect and verify the majority marker on the isolated member. Then isolate both secondaries and test majority against former primary; expect a write concern timeout or not-primary error depending on election timing. Observe primary step-down, reconnect both, verify a healthy set and elected primary. Writes may be unavailable without quorum; direct secondary reads can still work. A timeout does not prove a write was rolled back. The observer records observed time, not exact internal election instant. Reconnection in finally protects against normal script errors; if interrupted forcibly, use the recovery commands below. No Docker socket is mounted into containers.

## Evidence
`evidence/9.1-write-concern.csv`, `9.1-journaling.csv`, matching JSON, `9.2-partition.jsonl`, `9.2-observer.jsonl`, `replica-status.json`. Report actual measured results and unexpected errors. Observer sampling is approximately one second plus network delays. Check the two successful writes in phase one, failed majority acknowledgment in phase two, step-down, recovery, and catch-up. The runner prints outcomes, not fabricated data.

## Recovery after forced interruption
In PowerShell from this folder, for each of mongo1/mongo2/mongo3 whose network is disconnected: `docker network connect --alias mongo1 mongodb-lab9_default (docker compose ps -q mongo1)` (replace mongo1 twice as needed). Then `docker compose run --rm --no-deps -T runner python init.py`. Do not touch Lab 7/8 networks.

## Docker Hub submission
Create a public repository `mongodb-lab9` in your Docker Hub account. Run ` .\PUBLISH-DOCKER.bat` and enter your username; authenticate through Docker CLI. The image contains all Python tasks and the PowerShell orchestration/Compose files, not evidence or credentials. Keep this project folder for Compose orchestration. To demonstrate the published image, run ` .\RUN-PUBLISHED.bat` and enter the same username (it pulls the published image and uses it for every task). To retrieve Compose files from the published image alone: `docker create --name lab9-extract USER/mongodb-lab9:1.0` then `docker cp lab9-extract:/work/. ./mongodb-lab9` then `docker rm lab9-extract`. From extracted folder run RUN-PUBLISHED.bat. Submit a PDF containing the actual repository URL, tag, and measured evidence after push succeeds. Do not submit a placeholder URL.

## References
Assignment screenshots (Chapter 9); instructor repository https://github.com/sujeetjagtap/NoSQL-Databases-using-MongoDB/tree/main/chapter-09 (not accessible during preparation); MongoDB 8.0 write concern docs above. No live Docker test was performed in the generation environment.
