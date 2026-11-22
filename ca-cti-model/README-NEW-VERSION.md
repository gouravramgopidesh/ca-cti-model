# ca-cti-model — New Complete Version

This package is a **full CA project**, not a partial patch. It combines the existing CA threat-intelligence website and Labs 1–18 section with the latest chatbot general-chat and deterministic arithmetic adjustments.

## Run on Windows

1. Keep your original `lab7-mongodb` project separate. Do not delete Docker volumes.
2. Rename your existing `ca-cti-model` folder to `ca-cti-model-backup`, then extract this ZIP into `mongodb-lab` so the `docker-compose.yml` is in `ca-cti-model`.
3. Preserve any private `.env` from the previous CA folder if you customized it; do not upload it to GitHub.
4. From the new folder: `docker compose -p ca-cti-model up -d --build`.
5. Check: `docker compose -p ca-cti-model ps`. Open `http://localhost:3019/#labs18` or `http://localhost:3019/#assistant`.
6. On first startup, if the local model and knowledge are missing, execute `START-AI-WINDOWS.bat` (this downloads models and ingests data).

## Important

Do NOT run `docker compose down -v`, remove existing volumes, or delete `lab7-mongodb`. This project retains its own Compose group, and retains previously created Docker volumes so long as the Compose project name remains `ca-cti-model`.

Features that still require live verification: answer quality across all types of questions, native MongoDB `$vectorSearch`, complete original lab sources for labs 4–6, and professor's full deployment/security checklist. The model can make factual mistakes; no model can promise zero errors.
