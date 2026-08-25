# p42-KB

Knowledge Base project documentation.

## Current qualification guide

Version 1.2 is the current supporting guide for qualifying document understanding, retrieval and—only when justified—archetype induction and a bounded synthetic evaluation corpus on one NVIDIA DGX Spark. Version 1.2 keeps the full technical depth but uses progressive disclosure: a concise real-first operator route in the main chapters and linked implementation detail in appendices.

- `docs/KB_Project_P42_KB_Document_Archetype_and_Synthetic_Evaluation_Corpus_Qualification_Guide_v1.2.md` — editable source;
- `docs/KB_Project_P42_KB_Document_Archetype_and_Synthetic_Evaluation_Corpus_Qualification_Guide_v1.2.html` — formatted offline reading edition with deep links and reader routes;
- `docs/KB_Project_P42_KB_Document_Archetype_and_Synthetic_Evaluation_Corpus_Qualification_Guide_v1.2.docx` — styled Word edition with a live contents field and linked appendices.

Versions 1.0 and 1.1, together with the v1.0 review, are retained as historical evidence. The review file records the original findings and their later disposition.

## Validate the guide contracts

Install the pinned validation dependencies, validate the rendered HTML, and run the validator tests:

```bash
python3 -m venv .venv-guide-validation
.venv-guide-validation/bin/python -m pip install -r requirements-guide-validation.lock
.venv-guide-validation/bin/python tools/validate_guide_contracts.py \
  docs/KB_Project_P42_KB_Document_Archetype_and_Synthetic_Evaluation_Corpus_Qualification_Guide_v1.2.html
.venv-guide-validation/bin/python -m unittest discover -s tests -v
```

The validator checks the guide's tagged JSON/YAML examples against the exact versioned contracts embedded in the document. Operational commands still require target-DGX runtime qualification; syntax and document-contract validation are not substitutes for executing the negative fixtures on the frozen image.
