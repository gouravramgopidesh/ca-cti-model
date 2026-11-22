# CA CTI Model — targeted chat quality patch

This patch applies to the **CA** Docker project only. It fixes the two problems demonstrated in your screenshots:
1. Exact arithmetic goes through a deterministic, restricted Python calculator instead of the LLM (which guessed the result).
2. New general-topic questions no longer automatically include unrelated previous conversation turns, reducing answer contamination. Follow-up questions still include recent history.

## Install safely

1. Back up `ca-cti-model/chatbot/main.py` on your Windows computer.
2. Copy the patch's `chatbot/main.py` over the corresponding file inside your existing `ca-cti-model` folder. Do **not** copy it into the `lab7-mongodb` folder.
3. From `ca-cti-model` in PowerShell run:

   `docker compose -p ca-cti-model up -d --build chatbot`

4. Refresh `http://localhost:3019/#assistant`, click **New conversation**, and try:
   - `what is 666767676+78776868` → `745544544`
   - `what are the largest rivers in India` → a relevant geography response (model-generated, not guaranteed accurate)
   - `who is our PM` → the model must state uncertainty when appropriate.

No Docker volumes, MongoDB data, or Ollama model files need to be deleted. The original Lab 7 website remains unchanged.

## Scope and limitations

This is a focused patch, not a claim of a completely error-free LLM. It does not provide live internet browsing, fully implement native MongoDB vector search, or populate missing lab source files. General AI factual correctness remains limited by model quality and available evidence. Only source-level syntax and deterministic arithmetic tests were performed here; Windows/Docker runtime is not tested by this patch.
