# ca-cti-model

This is the Lab 7 CTI Digest website plus its final chatbot integration, packaged under the requested name **ca-cti-model**.

Run `START-AI-WINDOWS.bat` from this folder. The integrated website remains at http://localhost:3000/#assistant.

**Data compatibility:** `docker-compose.yml` deliberately retains `name: lab7-mongodb` and database `lab7-mongodb` so that renaming the filesystem folder does not silently change Docker Compose volume names or database identifiers. Do not run the original Lab 7 Compose stack and this package at the same time; they represent the same stack. Do not use `docker compose down -v` unless you intentionally want to delete its data volumes.

**Submission:** The final LLM assessment specifies a PRIVATE GitHub repository and faculty collaborator access. An existing public `ca-cti-model` repository would not meet that privacy requirement unless made private and the instructor invited.
