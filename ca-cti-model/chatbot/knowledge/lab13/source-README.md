# lab13-mongodb
Independent educational deployment. No previous lab files, ports or database volumes are required. MongoDB 8.0, Python 3.12, Percona exporter. All MongoDB ports are private to the Compose network; exporter binds only to localhost:9216. This is production-style configuration for coursework, not a hardened production deployment (no TLS, multi-host redundancy, external secret manager or backup policy).

## Windows / Docker Desktop
1. Extract the folder, open in VS Code, start Docker Desktop (Linux containers).
2. `./START-WINDOWS.bat` generates local credentials and key, builds runner, starts and initializes three members, creates a monitoring user, starts exporter.
3. `docker compose ps` and `./RUN-LABS.bat` verify majority-written record on every member, reject anonymous access, step down primary, log actual successful read target using PyMongo command monitoring, verify reconnection and scrape the exporter. `http://localhost:9216/metrics` is optional viewing.
4. `./PUBLISH-DOCKER.bat` and `./RUN-PUBLISHED.bat` publish and rerun with tag 1.0. Make repository public for grading. The published runner contains all scripts and manifests; Compose file and mongo-start.sh are needed on host. Existing volumes reused unless explicitly reset; no reset needed.
5. `./STOP-WINDOWS.bat` stops Compose before Kubernetes to free resources. Keep .env and volumes; do not publish .env or keys.

## Kubernetes (13.2)
Enable Kubernetes in Docker Desktop settings; verify `kubectl --context docker-desktop get nodes` shows Ready and `kubectl --context docker-desktop get storageclass` shows a default storage class. If Docker Desktop uses another context, inspect and adapt the explicitly pinned context rather than running against a remote cluster. Ensure Docker Hub image is public (Kubernetes pulls it). Run `./RUN-KUBERNETES.bat`, entering your Docker Hub username. It creates only namespace lab13-mongodb, generates one shared Secret (retained for reruns), applies headless Service and StatefulSet, initializes rs0 using mongosh, runs published Python image in two verification Jobs, deletes only mongo-2, verifies replacement pod UID and unchanged PVC UID, checks document on all three replicas, and saves actual logs. `./STOP-KUBERNETES.bat` scales StatefulSet to zero, retaining PVCs and Secret. Re-run restores replicas. Kubernetes Jobs are retained for inspection.

## Evidence and submission
`dir .\evidence` after both runs. Capture screenshots of successful tests, Docker Hub tag, kubectl pods/PVCs before and after. Submit PDF containing actual Docker Hub URL as instructed. PDF deferred per your workflow. Compare deployments in activity-13.2/COMPARISON.md. No fabricated benchmark results.

## References
Assignment screenshots (Exercise 13). Instructor reference repository: https://github.com/sujeetjagtap/NoSQL-Databases-using-MongoDB/tree/main/chapter-13 (not accessible during preparation). MongoDB keyfile guide: https://www.mongodb.com/docs/v8.0/tutorial/deploy-replica-set-with-keyfile-access-control/ ; exporter: https://github.com/percona/mongodb_exporter ; Kubernetes StatefulSet: https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/ . Atlas Terraform is a referenced example in the assignment, not an explicit activity; this project does not provision cloud resources.
