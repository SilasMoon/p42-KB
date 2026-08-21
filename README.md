# p42-KB

Knowledge Base project documentation.

## Current qualification guide

Version 1.1 is the current supporting guide for qualifying document understanding, retrieval, archetype induction and a bounded synthetic evaluation corpus on one NVIDIA DGX Spark:

- `docs/KB_Project_P42_KB_Document_Archetype_and_Synthetic_Evaluation_Corpus_Qualification_Guide_v1.1.md` — editable source;
- `docs/KB_Project_P42_KB_Document_Archetype_and_Synthetic_Evaluation_Corpus_Qualification_Guide_v1.1.html` — formatted offline reading edition;
- `docs/KB_Project_P42_KB_Document_Archetype_and_Synthetic_Evaluation_Corpus_Qualification_Guide_v1.1.docx` — Word edition.

The v1.0 HTML and its review are retained as historical evidence. The review file records the original findings and their v1.1 disposition.

## Validate the guide contracts

Install the pinned validation dependencies, validate the rendered HTML, and run the validator tests:

```bash
python3 -m venv .venv-guide-validation
.venv-guide-validation/bin/python -m pip install -r requirements-guide-validation.lock
.venv-guide-validation/bin/python tools/validate_guide_contracts.py \
  docs/KB_Project_P42_KB_Document_Archetype_and_Synthetic_Evaluation_Corpus_Qualification_Guide_v1.1.html
.venv-guide-validation/bin/python -m unittest discover -s tests -v
```

The validator checks the guide's tagged JSON/YAML examples against the exact versioned contracts embedded in the document. Operational commands still require target-DGX runtime qualification; syntax and document-contract validation are not substitutes for executing the negative fixtures on the frozen image.
