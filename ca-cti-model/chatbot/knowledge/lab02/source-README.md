# Lab 2 | Cloud setup and CRUD
Reference: https://github.com/sujeetjagtap/NoSQL-Databases-using-MongoDB/tree/main/chapter-02
1. Open Docker Desktop, run START-WINDOWS.bat. Port 27022 avoids the existing local service on 27017.
2. Copy .env.example to .env, replace the placeholder with your Atlas Drivers URI, including the database user's password (URL-encode reserved characters). Allow your current IP in Atlas. Never submit .env.
3. Run RUN-LABS.bat. All four scripts export actual MongoDB Extended JSON in their own activity directories. No sample results are substituted.
4. In Compass connect to mongodb://127.0.0.1:27022/ and open lab2-mongodb. Inspect books_updated using filter {"year":{"$lt":2010}}. Clean Code should display 43.989 (43.99 rounded for display); other prices remain unchanged. The CRUD collection is separate and contains four books.
5. Capture actual terminal output for each activity and Compass verification. Save screenshots as activity-2.1/output.png, activity-2.1-try/output.png, activity-2.2/output.png, activity-2.2-try/output.png and activity-2.2-try/compass.png. Extra screenshots can be named output-2.png etc. Hide credentials.
6. Run MAKE-SUBMISSION.bat to generate the Word report and submission ZIP, excluding .env and the virtual environment. No Docker Hub upload.
7. STOP-WINDOWS.bat stops only Lab 2's container, retaining data.
