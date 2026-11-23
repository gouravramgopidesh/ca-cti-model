# Lab 16 — Wide-Column and Graph Databases

Independent classroom project. Docker Desktop with Linux containers; recommend at least 6 GB available to Docker, more if other labs are running. No website or host database ports. Demo-only credentials and single-node databases, not production security or availability.

Run START-WINDOWS.bat, then RUN-LABS.bat. The first startup may take several minutes (Cassandra and Neo4j readiness). Stop/start the Compose group in Docker Desktop; keep volumes. PUBLISH-DOCKER.bat uses existing Docker credentials (`docker login` separately if necessary). RUN-PUBLISHED.bat pulls and recreates the app without building. The published image contains all Python tasks; Compose and external database images are also needed for demonstration. Evidence is saved to evidence/ on the host. Reruns replace only the dedicated lab datasets and evidence files.

## 16.1 University enrollment
60 students, 12 courses, 180 enrollments. Each student has three course IDs. MongoDB embeds course IDs and rosters; Cassandra maintains two query-driven tables; Neo4j models students/courses with ENROLLED_IN. All 132 query cases compare exact results against the generated dataset. See run_labs.py for executable queries and schema setup.

| Query | MongoDB | Cassandra | Neo4j |
|---|---|---|---|
| Courses for student | students.find_one({_id: student}).course_ids | SELECT course_id FROM student_courses WHERE student_id=? | MATCH (s:LabStudent {id:$id})-[:ENROLLED_IN]->(c) RETURN c.id |
| Students in course | courses.find_one({_id: course}).student_ids | SELECT student_id FROM course_students WHERE course_id=? | MATCH (s)-[:ENROLLED_IN]->(c:LabCourse {id:$id}) RETURN s.id |
| Shared courses | fetch course IDs then indexed $in on students, exclude self | fetch course IDs then query each roster, union and exclude self | MATCH (a:LabStudent {id:$id})-[:ENROLLED_IN]->(c)<-[:ENROLLED_IN]-(b) WHERE a<>b RETURN DISTINCT b.id |

MongoDB offers compact document reads but duplicated rosters require coordinated updates and bounded arrays. Cassandra gives predictable partition-local reads; shared-course queries fan out and require application-side deduplication. Neo4j expresses relationships directly and can extend to more hops; traversal cost grows with degree and depth. The sample is small and single-node; measurements are not production throughput claims. Each operation is warmed once, then measured 20 times using wall-clock time, including client/network overhead. JSON and CSV contain actual means, medians and ranges.

## 16.2 Hybrid fraud service
MongoDB transactions have txn_id, user_id, amount, merchant, timestamp and risk_score. Cassandra user_profiles partitions by user_id and clusters by descending event_time (txn_id tie-breaker). Neo4j has FraudUser nodes and TRANSFERRED_TO edges. The demo ring U1→U2→U3→U1 is explicitly verified; paths are bounded to 1–3 hops and 50 results. A path is a candidate connection, not proof of fraud. FraudQueryService merges three independently tagged results. Pools: Mongo maxPoolSize=10, Cassandra persistent session/executor_threads=4, Neo4j max_connection_pool_size=10. Each circuit opens after three consecutive failures, skips calls for 30 seconds, and retries on the next request. Sequential classroom service, not thread-safe. Mock tests simulate outages and cooldown with a fake clock; integration tests use all three real databases. No live outage injection is claimed. Evidence includes ordered profile and graph paths, query equivalence and latency results.

Instructor source: https://github.com/sujeetjagtap/NoSQL-Databases-using-MongoDB/tree/main/chapter-16 (not retrievable during preparation; assignment screenshots used). The clipped portion of 16.1 sample solution was not available. Docker Hub target: https://hub.docker.com/r/gouravram77/lab16-mongodb . PDF submission should use actual run results after published verification.
