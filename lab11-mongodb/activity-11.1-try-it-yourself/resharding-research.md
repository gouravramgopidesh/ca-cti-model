# Lab 11.1 — Try it yourself: resharding (MongoDB 5.0+)

Resharding changes an existing sharded collection's shard key, redistributing its data. It is not the same as adding a suffix with refineCollectionShardKey.

## Procedure (MongoDB 8.0)
1. Review workload and candidate key; check cardinality, frequency and query targeting. Take a backup and confirm available disk, CPU and network headroom on every shard.
2. Ensure all members and feature compatibility version support the operation. Use a globally unique _id across shards; check unique index compatibility and use simple collation as required. Finish index builds and avoid competing DDL.
3. Connect to mongos; disable the balancer for the documented procedure. Execute `db.adminCommand({reshardCollection: "lab11-mongodb.hotspot_data", key: {user_id: "hashed"}})` only on a disposable test collection containing user_id. Monitor with $currentOp; verify resulting shard key, counts, indexes and routing; re-enable balancer.
4. The coordinator clones data to recipients and applies concurrent changes. A short critical section blocks writes at cutover. Schedule for low traffic; do not assume zero disruption.

## Limitations
- Minimum duration is five minutes in MongoDB 8.0. Resource demands can be significant, and only one reshard/move/unshard operation may run at once.
- Duplicate _id values across shards can cause failure. Do not build indexes during resharding. Queryable Encryption collections are not supported; Atlas Search indexes may need rebuilding.
- The new key must meet shard-key constraints. Retryable writes spanning the operation have a limited history window; application retries and validation are important.
- This activity asks for research, not a timed live reshard. The standard runner does not execute the command or alter the measured collections.

References: https://www.mongodb.com/docs/v8.0/core/sharding-reshard-a-collection/ and https://www.mongodb.com/docs/v8.0/reference/command/reshardcollection/
