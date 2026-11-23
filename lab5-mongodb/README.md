# MongoDB Lab 5 — Aggregation and $lookup

Complete code package for the four activities in Chapter 5, following the supplied classroom instructions.

## Project isolation

- MongoDB connection defaults to `mongodb://localhost:27029`, the published MongoDB port of the existing CA project.
- Only writes to the separate database `mongodb_lab5`.
- Uses unique keys and upsert-based seed data; does **not** drop other databases, containers or volumes.
- The input `orders.json` uses human-readable ISO order dates. The aggregation converts dates with `$toDate` before grouping by month.

## Activity folders

1. `Activity_5.1_Sales_Analytics/` — monthly revenue, top three customers, average order value by status. 24 orders.
2. `Activity_5.1_Try_Bucket/` — `$bucket`: small (<$50), medium ($50–$200, inclusive), large (>$200); sample orders use integer prices/totals.
3. `Activity_5.2_Lookup_Joins/` — referenced orders/products, `$lookup` join, and two never-ordered products.
4. `Activity_5.2_Try_Lookup_Pipeline/` — correlated `$lookup` pipeline with a filter on foreign product documents.

Each folder has its own Python script and JSON input. All four are independent of your CTI production collections.

## Run on Windows in VS Code

1. Extract this ZIP into `C:\mongodb-projects\lab5-mongodb` (or any separate folder).
2. Open that folder in VS Code. Make sure your CA Docker **MongoDB** container is running (localhost port 27029).
3. In PowerShell, install dependencies:

   `python -m pip install -r requirements.txt`

4. Run:

   `powershell -ExecutionPolicy Bypass -File .\RUN-LAB5.ps1`

5. Confirm four `PASS` messages and the green `All 4 Lab 5 activities passed` line.
6. Capture your own terminal screenshots after actual execution. The script also stores terminal text in `outputs/`.

If your MongoDB port differs, set `LAB5_MONGO_URI`, for example:

   `$env:LAB5_MONGO_URI = 'mongodb://localhost:27017'`

## Assignment documentation

- `docs/Lab5_Original_Activity_Documentation.docx` — four code listings with labelled, **unfilled** screenshot evidence areas (outputs must be taken from your machine; no fabricated screenshots).
- `docs/Lab5_One_Page_Chapter_Report.docx` — one experiment page, plus a separate cover page, with Aim, Objective, Procedure and Result. No programming code.
- `docs/Lab5_One_Page_Chapter_Report.pdf` — printable version.

## Requirements / scope notes

- The 5.1 sales totals include all statuses because the assignment doesn't specify excluding cancelled or pending orders. For production recognized revenue, filter to completed orders.
- 5.2 uses a true reference `product_id` and computes line totals from `products.base_price`, distinct from the 5.1 snapshots in `orders.unit_price`.
- This is classroom demonstration code, not a deployed API or production commerce backend.
- Do not claim execution was verified until you run this against your local MongoDB.

## For your final submission

Add this Lab 5 activity folder to your existing consolidated GitHub repo alongside the other lab source files and mini project. The final lab report should include exactly one Lab 5 experiment page (not four separate report pages).
