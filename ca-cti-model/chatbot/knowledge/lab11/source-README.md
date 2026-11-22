# lab11-mongodb
Independent Lab 11: shard key evaluation and hotspot detection. No previous lab files, ports or databases are required. MongoDB 8.0, Python and Docker Compose. Local-only unauthenticated development cluster: one config replica set member, two single-member shard replica sets and one mongos router. Not production/high availability. All data volumes are separate. No host ports are published.

## Run on Windows
1. Open Docker Desktop and the extracted project in VS Code.
2. Run `START-WINDOWS.bat` (initializes config and shard sets before launching mongos).
3. Run `RUN-LABS.bat` and press a key at each pause. Activity 11.1 seeds 10,000 synthetic orders, computes actual cardinalities and frequency, and exports a decision matrix; read the resharding research activity. Activity 11.2 inserts 10,000 documents per collection and records per-shard statistics and execution plans. The runner drops only its own orders/hotspot_data/even_data collections on rerun. It temporarily disables and restores the balancer. Do not run multiple copies concurrently.
4. Inspect evidence/ and keep screenshots. Use `STOP-WINDOWS.bat` to stop without deleting volumes.

## Methodology
The timestamp key receives an explicitly split and placed range (first 500 on shardA, newest 9500 on shardB) before insertion. This controlled experiment isolates the monotonic write hotspot; it does not claim the automatic balancer would produce those counts. Hashed user_id uses pre-distributed chunks and random ObjectIds. Both collections contain the same document fields and values. Identical date filters are compared, plus hashed key range and equality. Counts and plans are asserted; no timing or distribution results are invented. The decision matrix evaluates qualitative targeting and distribution, not a live benchmark of four separate shard layouts. Hashed customer_id is recommended for equality-heavy workloads, but a single hot customer still maps to one shard.

## Docker Hub submission
After local tests, run `PUBLISH-DOCKER.bat`, then `RUN-PUBLISHED.bat` with the same username. The runner image includes all scripts, Docker Compose and launchers. The three database members and router still use official mongo:8.0 images. Keep the local project folder for Compose orchestration. To recover that configuration from the image on another Windows PC, run `docker create --name lab11-files USER/lab11-mongodb:1.0`, then `docker cp lab11-files:/work ./lab11-demo`, then `docker rm lab11-files`. Open lab11-demo and use RUN-PUBLISHED.bat. Check repository visibility and submit PDF containing actual Docker Hub URL and tag 1.0. No PDF generated until publication.

## References
Instructor screenshots, Chapter 11 (repository unavailable during creation).
- https://www.mongodb.com/docs/v8.0/tutorial/deploy-shard-cluster/
- https://www.mongodb.com/docs/v8.0/sharding/
- https://www.mongodb.com/docs/manual/core/hashed-sharding/
- https://www.mongodb.com/docs/manual/reference/operator/aggregation/collstats/
- https://www.mongodb.com/docs/v8.0/core/sharding-reshard-a-collection/
