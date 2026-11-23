# lab10-mongodb — Transactions, Atomicity, Durability & Journaling

Independent MongoDB 8.0 / PyMongo lab. No Lab 7 website or Lab 8/9 dependency. Docker Compose creates a private 3-node replica set (`rs0`) and separate named data volumes. No host ports are published. This is an unauthenticated local teaching cluster, not a production deployment.

## Windows / VS Code

1. Extract the ZIP and open the `lab10-mongodb` folder. Start Docker Desktop. Other labs may be stopped to save resources.
2. Run ` .\START-WINDOWS.bat ` from PowerShell, press a key at the end, and check `docker compose ps`.
3. Run ` .\RUN-LABS.bat ` and capture each activity's actual terminal output. Press a key at each pause. The final message indicates success; errors stop the runner.
4. Open `evidence/10.2-throughput.svg` in a browser for the measured throughput plot. Keep the JSON and CSV results.
5. Stop using ` .\STOP-WINDOWS.bat ` (does not delete volumes).

## Lab 10.1 — Bank transfer transaction

`activity-10.1/bank-transfer.py` uses accounts (account_id, integer balance, version) and transfer_history. Seed balances A=1000 and B=500. A successful transfer of 200 should leave A=800 and B=700. An insufficient-funds transfer and a deliberately injected failure after debit must leave balances and history unchanged. The latter directly demonstrates rollback of an already executed write. The script checks the committed history on every replica. Transactions use snapshot reads and majority, journaled commits. These are test expectations, not pre-recorded results. Journaled majority acknowledgement demonstrates configured durability; the lab does not simulate a power-loss event.

## Lab 10.1 — Try it yourself

`activity-10.1-try-it-yourself/retry-transfer.py` creates an actual competing committed update after the transaction reads its snapshot. A stale-snapshot write should raise a transient transaction error. The helper retries the entire transaction with exponential delays of 0.1, 0.2, 0.4, 0.8 and 1.6 seconds (up to five retries). Unknown commit results are retried as commits only. It asserts a retry was observed and the final transfer occurred exactly once. Insufficient funds are business failures, not retried.

## Lab 10.2 — Inventory reservation with deadlock/write conflict handling

`activity-10.2/inventory-reservation.py` creates inventory and orders with product_id, stock, version, customer_id, items, status and total. Each reservation reads availability and performs a version-checked decrement and order insert in one transaction. A barrier forces eight independent sessions to read the same five-unit stock snapshot before attempting the write. The no-retry run records conflicts; the retry-enabled run checks exactly five successful orders, three out-of-stock rejections, zero remaining stock, no overselling and at least one retry. Business rejections stop immediately. PyMongo reports write conflicts via error codes/labels (not a dedicated WriteConflict exception class).

For throughput, each mode and each thread count (1, 4, 8, 16) starts with 80 units and performs 80 requests. The same majority+journal write concern is used for both the transaction and the non-transactional findOneAndUpdate + insert baseline. Count successes, elapsed time, successful reservations/second, conflict retries and failures. Actual performance trends depend on the machine. An injected order-creation failure shows why the non-transactional sequence can lose stock while the transactional sequence rolls back. Every run uses a separate run ID so old evidence data is not deleted.

## Evidence generated after actual execution

- `replica-status.json`
- `10.1-bank-transfer.json`
- `10.1-retry.json`
- `10.2-inventory.json`
- `10.2-throughput.csv`
- `10.2-throughput.svg`

## Docker Hub submission (after successful local tests)

Run ` .\PUBLISH-DOCKER.bat `, enter your Docker Hub username and authenticate with Docker. This builds and pushes `<username>/lab10-mongodb:1.0`. Then run ` .\RUN-PUBLISHED.bat ` and enter the same username. It pulls the exact tag and executes the activities using that image without rebuilding. Check all activities finish and ensure the repository is accessible to your instructor. Submit a PDF with the actual repository URL and tag, as required by the assignment. No PDF with an unverified URL is included.

### Reproduce using only the published image and Docker Desktop

In an empty folder, substitute the actual Docker Hub username in the following PowerShell commands:

```powershell
$image = 'YOUR_USERNAME/lab10-mongodb:1.0'
docker pull $image
$id = docker create $image
docker cp "${id}:/work/docker-compose.yml" .\docker-compose.yml
docker rm $id
$env:LAB10_IMAGE = $image
New-Item -ItemType Directory -Force evidence | Out-Null
docker compose up -d --wait mongo1 mongo2 mongo3
docker compose run --rm --no-deps --no-build -T runner python init.py
docker compose run --rm --no-deps --no-build -T runner python run_all.py
docker compose --profile tools stop
```

The published image contains all the Python source and Compose file. The official MongoDB image provides the three database services. Do not use `docker compose down -v` unless you explicitly want to delete this lab's database volumes.

## References

- Assignment screenshots: Exercise 10, Lab 10.1, Try it yourself, Lab 10.2 and Docker Hub submission.
- Instructor repository (not accessible during preparation): https://github.com/sujeetjagtap/NoSQL-Databases-using-MongoDB/tree/main/chapter-10
- MongoDB transaction API: https://www.mongodb.com/docs/manual/core/transactions-in-applications/
- PyMongo transaction guide: https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/transactions/
