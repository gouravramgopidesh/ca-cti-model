# Lab 2 — no Docker
Reference: https://github.com/sujeetjagtap/NoSQL-Databases-using-MongoDB/tree/main/chapter-02

This version compares native MongoDB Community Server with Atlas, not Docker. This is a deviation from Activity 2.1 Try it yourself; obtain instructor approval if required.

1. Ensure the existing Windows MongoDB service is running at 127.0.0.1:27017 (same as Lab 1). No Docker is used. Only the dedicated lab2-mongodb database is modified.
2. In Atlas ensure the database user exists and current IP is allowed. Run CONFIGURE-ATLAS.bat and enter the database username/password (not website credentials). It URL-encodes credentials, tests ping and saves .env only on success. Never submit .env.
3. Run RUN-LABS.bat. Each activity exports output.json with real database results.
4. In Compass connect to mongodb://127.0.0.1:27017/ and open lab2-mongodb. Inspect books_updated using filter {"year":{"$lt":2010}}. Clean Code changes from 39.99 to 43.989 (43.99 rounded). Other prices stay unchanged.
5. Save real screenshots in each activity folder as output.png; save Compass verification as activity-2.2-try/compass.png. Additional screenshots may be output-2.png etc. Hide credentials.
6. Run MAKE-SUBMISSION.bat to create Lab2-Report.docx and Lab2-Submission.zip. No Docker Hub upload. Do not submit the setup ZIP as final work.
