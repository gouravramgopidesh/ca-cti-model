# Exercise 3 — MongoDB data modeling
Normal local Python project; no Docker, Atlas, Lab 7 dependency or chatbot.
Connect Compass to mongodb://127.0.0.1:27017/. Database: lab3-mongodb.
Run RUN-LABS.bat; it installs dependencies and pauses after each activity.
Scripts reset only their own exercise collections in lab3-mongodb on rerun.
Run in order: 3.1, 3.1 try, 3.2, 3.2 try. JSON exports are generated from live reads.
Capture terminal screenshots (multiple if needed) into screenshots/ named
3.1-01.png, 3.1-try-01.png, 3.2-01.png, 3.2-try-01.png. Additional images
may use -02, -03 etc. Capture Compass evidence as compass-01.png if desired.
Run MAKE-SUBMISSION.bat to rebuild Exercise-3.docx and create Exercise-3-Submission.zip.
Expected counts: courses 3; courses_prerequisites 3; posts 5; comments 10;
posts_embedded 5; posts_10000_referenced 1; comments_10000 10000.
The 3.2 JSON exports migrated posts with comments; 3.2 try exports all referenced comments.
Course reference supplied: https://github.com/sujeetjagtap/NoSQL-Databases-using-MongoDB/tree/main/chapter-03
The link could not be retrieved during preparation; implementation follows the supplied assignment text.
