# Exercise 1 — NoSQL foundations (no Docker)

Requires Python 3, a running MongoDB Community Server (or Atlas), and PyMongo. Compass is optional and is not itself a MongoDB server.

## Windows / VS Code
1. Open this extracted Exercise-1 folder in VS Code.
2. If MongoDB Community Server is installed as a Windows service, check that it is running in services.msc. Default connection: mongodb://localhost:27017.
3. In the VS Code PowerShell terminal, run `python -m pip install -r requirements.txt`.
4. Run ` .\RUN-LABS.bat `, or execute each command below separately. If using Atlas or another server, set `$env:MONGO_URI` to your connection URI in the terminal before running. Do not include credentials in screenshots or the submission.

- `python activity-1.1/classify_databases.py`
- `python activity-1.1-try/research_database.py`
- `python activity-1.2/map_application.py`
- `python activity-1.2-try/map_cti.py`

The batch pauses after each activity so you can capture actual output with Win+Shift+S. Scroll up for any additional screenshots. Each script reads its matching JSON, writes to its dedicated collection in the lab1-mongodb database, verifies equality, and exports the actual records back to JSON. Re-running replaces coursework data in those four dedicated collections only. Do not use those collection names for other data.

## Submission
Fill in name and USN in Exercise-1.docx and insert actual screenshots for all four activities. ZIP the four activity directories and completed DOCX. README, requirements and batch are optional execution helpers, not required submission files. No Docker or Docker Hub is needed. The initial JSON files are prepared coursework data, not evidence of a successful run.

Reference: instructor assignment and chapter 01 README supplied by the user; https://github.com/sujeetjagtap/NoSQL-Databases-using-MongoDB/tree/main/chapter-01 . ArangoDB research reference: https://docs.arango.ai/arangodb/stable/concepts/data-models/ .
