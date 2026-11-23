# MongoDB Lab 6 — Index Design, Performance & Covered Queries

## What is included
Four independent Python scripts, four JSON configuration datasets, one PowerShell runner, one page final-report section and original activity documentation.

| Activity | Folder | Task |
|---|---|---|
| 6.1 | Activity_6.1_Index_Workload | Generate 50,000 product documents; explain five queries before/after five indexes |
| 6.1 Try | Activity_6.1_Try_IndexStats | Use `$indexStats` to measure query-driven accesses |
| 6.2 | Activity_6.2_Index_Strategies | Time two 10,000-document inserts with 0 vs 5 indexes, compare 5 vs 1 indexes |
| 6.2 Try | Activity_6.2_Try_Covered_Query | Explain covered query: IXSCAN, no FETCH, zero documents examined |

## Run on Windows (VS Code PowerShell)

Start MongoDB for the CA CTI project (mapped port **27029**), open this Lab 6 folder, then run:

```powershell
python -m pip install -r requirements.txt
powershell -ExecutionPolicy Bypass -File .\RUN-LAB6.ps1
```

If your local MongoDB is on default port 27017 instead, set the environment variable first:

```powershell
$env:LAB6_MONGO_URI='mongodb://localhost:27017'
```

The code uses database **mongodb_lab6**, with distinct collections **products_50k** and **products_index_benchmark**. The scripts only drop/reseed these two lab collections; your CTI and Lab 7 databases are not touched. No Docker volumes are deleted. The first run inserts 70,000 generated documents total and may take time depending on the system.

## Evidence and interpretation

Each activity writes a terminal transcript to `outputs/` and also saves JSON explain/usage evidence there. Capture **real terminal screenshots** after running: the original Google Classroom activity DOCX requires screenshots. Screenshots are deliberately not fabricated or pre-filled.

The five baseline queries include a **case-sensitive anchored name-prefix regex**, not `$text`, because MongoDB `$text` requires a text index and therefore cannot be explained before index creation. Prefix lookup remains an indexed name-search workload. If your instructor specifically requires `$text` search rather than name-prefix search, create a *separate* text index after capturing pre-index baseline and explain the difference.

For 6.2, the five-index vs one-index comparison uses the **same 20,000-document benchmark collection**. Wall-clock insertion times can vary with caching, container resources and host load. A positive slowdown indicates extra write overhead, but it is not guaranteed for a single short run. `ix_category_price` is the retained critical index. The covered query excludes `_id` to avoid FETCH and documents examined must be 0.

## Submission

Original activity submission: four scripts + four JSON files arranged in folders, plus DOCX containing the four scripts and **screenshots you capture from the real run**.

Final consolidated subject report: exactly **one Lab 6 experiment page** (aim, objective, procedure, result), no source code; front page is separate. Place all actual lab source code in the single consolidated GitHub repository together with the CA mini-project.
