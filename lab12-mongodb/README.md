# lab12-mongodb — Database security and CIA triad

Independent classroom project. Docker Desktop (Linux containers) and Windows PowerShell required. No host database ports, no dependency on Lab 7 or other labs.

## Run
1. Extract, open this directory in VS Code, run `./START-WINDOWS.bat` (PowerShell: `.\START-WINDOWS.bat`).
2. `docker compose ps`; both mongo and mongo-tls should be healthy.
3. `.\RUN-LABS.bat`; capture each activity's terminal output. JSON evidence is written to evidence/.
4. `.\PUBLISH-DOCKER.bat` and `.\RUN-PUBLISHED.bat` with your Docker Hub username. Submit the repository URL in a PDF, after verifying visibility. Keep this Compose project alongside the published runner for demonstration; a runner image alone cannot provision both database services.
5. `.\STOP-WINDOWS.bat` stops services without deleting data.

## Activities
- 12.1: authenticated MongoDB, collection-scoped report reader and writer, anonymous and wrong-password rejection, allowed and denied operations. Ordinary aggregation uses MongoDB's `find` privilege, not a separate `aggregate` action. Admin creates users and roles. Expected permission error 13 and authentication error 18 are successful negative tests.
- 12.1 extension: public employee view excludes salary; application users cannot read underlying collection; HR can. Data is synthetic. View redaction is access control, not field encryption.
- 12.2: OpenSSL creates a local CA, server and client certificates; server SAN includes Docker hostname and localhost. Separate authenticated MongoDB service requires TLS and a trusted client certificate; PyMongo uses SCRAM credentials in addition to TLS. Plaintext and missing-client-cert attempts must fail while valid encrypted reads succeed. Evidence includes protocol, cipher and certificate metadata. Private keys are not printed or published.

## Security and scope
Generated passwords in `.env` are local only; do not upload that file. Certificates and private keys live in separate Docker volumes; CA private key is not mounted by either database or runner. Server key only in server volume. Do not remove volumes or `.env` to restart. This is an isolated classroom deployment, not a production hardened system; TLS server runs as root inside its container for bootstrap simplicity. Authentication and TLS are tested on separate instances to preserve the demonstration of both configurations. No encryption-at-rest or enterprise audit feature is claimed. Confidentiality: RBAC, view, TLS. Integrity: restricted mutations. Availability: not benchmarked here (covered by earlier replica-set labs).

## References
- https://www.mongodb.com/docs/v8.0/reference/privilege-actions/
- https://www.mongodb.com/docs/v8.0/reference/method/db.createrole/
- https://www.mongodb.com/docs/v8.0/tutorial/configure-ssl/
- Instructor Exercise 12 screenshots; chapter-12 repository could not be retrieved.

## Evidence
`12.1-rbac.json`, `12.1-redaction.json`, `12.2-tls.json`. Results are generated only on actual execution. Static checks and OpenSSL chain generation tested during packaging; Docker runtime must be verified locally.
