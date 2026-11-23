# MongoDB Lab 4 — Product Query API, Regex, Upsert and Bulk Operations

This package follows the four activities shown in the instructor's Chapter 4 assignment. The Python code is kept separate from the final one-page lab report.

## Files

- `Activity_4.1_Product_Query_API/`: validated products schema, 12 seed products, CRUD, comparison/logical/array queries, pagination.
- `Activity_4.1_Try_Regex_Search/`: case-insensitive `$regex` name lookup, with `regex_queries.json`.
- `Activity_4.2_Upsert_Bulk/`: price upsert and exactly five `UpdateOne` requests, with `bulk_operations.json`.
- `Activity_4.2_Try_Idempotent_Import/`: repeated import with no duplicate SKUs, with `import_products.json`.
- `lab4_common.py`: shared MongoDB setup and schema validation.
- `docs/`: activity documentation, one-page chapter report and PDF.
- `outputs/`: terminal transcripts created when scripts run on your machine.

Each activity directory has one Python script and its respective JSON file, as requested.

## Windows setup (PowerShell)

Keep the CA Docker stack running, so its MongoDB service is accessible on **localhost:27029**. Lab 4 uses database **`mongodb_lab4`**, leaving your existing CA CTI database and Lab 7 volumes unchanged.

```powershell
cd "C:\mongodb-projects\lab4-mongodb"
python -m pip install -r requirements.txt
powershell -ExecutionPolicy Bypass -File .\RUN-LAB4.ps1
```

If your standalone MongoDB runs on 27017 instead:

```powershell
$env:LAB4_MONGO_URI = "mongodb://localhost:27017"
powershell -ExecutionPolicy Bypass -File .\RUN-LAB4.ps1
```

### Run individually

```powershell
python Activity_4.1_Product_Query_API/lab4_1_product_queries.py
python Activity_4.1_Try_Regex_Search/lab4_1_try_regex.py
python Activity_4.2_Upsert_Bulk/lab4_2_upsert_bulk.py
python Activity_4.2_Try_Idempotent_Import/lab4_2_try_import.py
```

The scripts create the `products` collection with a JSON schema validator and a unique SKU index. They do **not** delete databases or volumes. The bulk stock increments in Activity 4.2 are deliberately repeatable **actions**, not idempotent; the import in Activity 4.2 Try It Yourself **is idempotent**.

## Verification and report evidence

1. Run all four scripts on your own MongoDB. Each script prints `PASS` only after its own assertions pass.
2. Save the generated `outputs/*.txt` transcripts. Capture actual terminal screenshots of each activity (Windows: `Win + Shift + S`) and insert them in `docs/Lab4_Original_Activity_Documentation.docx` for the **original activity submission**. Screenshots have not been fabricated or pre-inserted.
3. For the **final printed lab report**, use `docs/Lab4_One_Page_Chapter_Report.pdf` or the matching DOCX. That page contains Aim, Objective, Work Done / Procedure and Result, without source code.
4. Add the four activity folders and their scripts/JSON files to the consolidated GitHub repository alongside Labs 1–18 and the mini project.

## Important

The source files and document formats have been generated and Python syntax/JSON checked. Actual MongoDB execution still needs to occur on your Windows machine. Do not report verified database output until you've seen the `PASS` messages.
