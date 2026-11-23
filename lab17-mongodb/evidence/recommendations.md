# Measured index recommendations

Collection: `lab17_rag.benchmark_949f74809684`. 5,000 vectors, 384 dimensions, 100 queries.

- MongoDB HNSW: fastest 2.401 ms at 99.20% recall (numCandidates=50); highest recall 100.00% (numCandidates=100).
- FAISS HNSW: fastest 0.019 ms at 98.20% recall (M=8;efConstruction=32;efSearch=32); highest recall 100.00% (M=8;efConstruction=64;efSearch=64).
- FAISS IVF: fastest 0.028 ms at 99.55% recall (nlist=200;nprobe=10); highest recall 100.00% (nlist=50;nprobe=50).

HNSW is a candidate for high-recall RAG; tune search breadth and memory. IVF is useful when an external index is acceptable and probing can be tuned. Full probing costs more; flat exact search is another option for small collections. Select configurations using measured recall targets, not assumed rankings. Native MongoDB timings include network and BSON retrieval; FAISS timings are in-process, so they are not equivalent end-to-end timings. This small synthetic corpus does not establish million-vector performance or memory savings.