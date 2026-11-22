# Exercise 1 — NoSQL foundations

Course: 23CSE528. Four independent activity directories, each with one Python script and its matching JSON. JSON is prepopulated coursework data and is rewritten from verified MongoDB records on execution. No other database products are installed: MongoDB stores the classification and design decisions as required.

## Run on Windows
1. Extract into your mongodb-lab folder and open lab1-mongodb in VS Code.
2. Run ` .\START-WINDOWS.bat ` then ` .\RUN-LABS.bat `.
3. For screenshots, run each activity separately, using the commands below. Capture the actual terminal output, including its PASS line. Scroll or use multiple screenshots as needed. Insert the screenshots in the corresponding spaces of Exercise-1.docx (or send them for assembly). Do not submit the placeholder report as finished evidence.

- `docker compose exec -T app python activity-1.1/classify_databases.py`
- `docker compose exec -T app python activity-1.1-try/research_database.py`
- `docker compose exec -T app python activity-1.2/map_application.py`
- `docker compose exec -T app python activity-1.2-try/map_cti.py`

## Submission
ZIP with four activity directories and the completed DOCX containing all four scripts and their real screenshots. Docker files are included for reproducibility; Docker Hub publication is not required for Exercise 1. The submission deadline was 27 August 2026, 23:59; the assignment specifies a late penalty.

Reference: instructor-provided chapter 01 README and assignment text (GitHub page could not be retrieved independently). ArangoDB research: https://docs.arango.ai/arangodb/stable/concepts/data-models/.
