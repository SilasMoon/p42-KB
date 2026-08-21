from __future__ import annotations

import html
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))
import validate_guide_contracts as validator  # noqa: E402


HASH_PATTERN = "^[a-fA-F0-9]{64}$"


def observation_schema() -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["observations", "warnings"],
        "properties": {
            "observations": {"type": "array"},
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
    }


def claim_schema() -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["answerability", "claims"],
        "properties": {
            "answerability": {
                "enum": [
                    "fully_answerable",
                    "partly_answerable",
                    "not_answerable",
                    "conflicting_authority",
                    "ambiguous",
                ]
            },
            "claims": {"type": "array"},
        },
    }


def public_research_schema() -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "recommendation",
            "claims",
            "artefact_refs",
            "test_refs",
            "unresolved_risks",
        ],
        "properties": {
            "recommendation": {"type": "string"},
            "claims": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["claim", "kind", "source_urls", "limitation"],
                    "properties": {
                        "claim": {"type": "string"},
                        "kind": {"enum": ["published_fact"]},
                        "source_urls": {
                            "type": "array",
                            "items": {"type": "string", "format": "uri"},
                        },
                        "limitation": {"type": ["string", "null"]},
                    },
                },
            },
            "artefact_refs": {"type": "array"},
            "test_refs": {"type": "array"},
            "unresolved_risks": {"type": "array"},
        },
    }


def worker_schema(schema_id: str = validator.WORKER_SCHEMA_ID) -> dict:
    definitions = {
        "observation": observation_schema(),
        "reviewer": {"type": "object"},
        "ast_fill": {"type": "object"},
        "claim_response": claim_schema(),
        "protected_case_map": {"type": "object"},
        "code_build": {"type": "object"},
        "public_research": public_research_schema(),
        "frozen_report": {"type": "object"},
    }
    all_of = [
        {
            "if": {
                "properties": {"status": {"const": "complete"}},
                "required": ["status"],
            },
            "then": {
                "properties": {
                    "escalation": {"type": "null"},
                    "payload": {"type": "object"},
                }
            },
        },
        {
            "if": {
                "properties": {"status": {"const": "needs_escalation"}},
                "required": ["status"],
            },
            "then": {
                "properties": {
                    "escalation": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "enum": [
                                    "ROUTINE_VISUAL_UNRESOLVED",
                                    "HARD_REASONING_UNRESOLVED",
                                    "EVIDENCE_CONFLICT",
                                    "SCHEMA_INADEQUATE",
                                ]
                            }
                        },
                    },
                    "payload": {"type": "null"},
                }
            },
        },
        {
            "if": {
                "properties": {"status": {"const": "data_boundary_blocked"}},
                "required": ["status"],
            },
            "then": {
                "properties": {
                    "escalation": {
                        "type": "object",
                        "properties": {
                            "code": {"const": "DATA_BOUNDARY_MISMATCH"}
                        },
                    },
                    "payload": {"type": "null"},
                }
            },
        },
        {
            "if": {
                "properties": {"status": {"const": "tool_failure"}},
                "required": ["status"],
            },
            "then": {
                "properties": {
                    "escalation": {
                        "type": "object",
                        "properties": {"code": {"const": "TOOL_UNAVAILABLE"}},
                    },
                    "payload": {"type": "null"},
                }
            },
        },
    ]
    for payload_id, def_name in validator.PAYLOAD_SCHEMA_TO_DEF.items():
        all_of.append(
            {
                "if": {
                    "allOf": [
                        {
                            "properties": {"status": {"const": "complete"}},
                            "required": ["status"],
                        },
                        {
                            "properties": {
                                "task_payload_schema_id": {"const": payload_id}
                            },
                            "required": ["task_payload_schema_id"],
                        },
                    ]
                },
                "then": {
                    "properties": {"payload": {"$ref": f"#/$defs/{def_name}"}}
                },
            }
        )
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": schema_id,
        "type": "object",
        "additionalProperties": False,
        "required": [
            "job_id",
            "attempt_id",
            "status",
            "escalation",
            "task_payload_schema_id",
            "payload",
            "model_revision",
            "inference_profile_id",
            "prompt_sha256",
        ],
        "properties": {
            "job_id": {"type": "string"},
            "attempt_id": {"type": "string"},
            "status": {
                "enum": [
                    "complete",
                    "needs_escalation",
                    "data_boundary_blocked",
                    "tool_failure",
                ]
            },
            "escalation": {
                "oneOf": [
                    {"type": "null"},
                    {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["code", "field_ids", "evidence_ids"],
                        "properties": {
                            "code": {
                                "enum": [
                                    "ROUTINE_VISUAL_UNRESOLVED",
                                    "HARD_REASONING_UNRESOLVED",
                                    "DATA_BOUNDARY_MISMATCH",
                                    "EVIDENCE_CONFLICT",
                                    "SCHEMA_INADEQUATE",
                                    "TOOL_UNAVAILABLE",
                                ]
                            },
                            "field_ids": {"type": "array"},
                            "evidence_ids": {"type": "array"},
                        },
                    },
                ]
            },
            "task_payload_schema_id": {
                "enum": list(validator.PAYLOAD_SCHEMA_TO_DEF)
            },
            "payload": {"type": ["object", "null"]},
            "model_revision": {"type": "string"},
            "inference_profile_id": {"type": "string"},
            "prompt_sha256": {"type": "string", "pattern": HASH_PATTERN},
        },
        "allOf": all_of,
        "$defs": definitions,
    }


def job_schema(schema_id: str = validator.JOB_SCHEMA_ID) -> dict:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": schema_id,
        "type": "object",
        "additionalProperties": False,
        "required": [
            "job_id",
            "execution_zone",
            "allowed_inputs",
            "source_manifest_sha256",
            "forbidden_action_registry_sha256",
        ],
        "properties": {
            "job_id": {"type": "string"},
            "execution_zone": {"type": "string"},
            "allowed_inputs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["sha256"],
                    "properties": {
                        "sha256": {"type": "string", "pattern": HASH_PATTERN}
                    },
                },
            },
            "source_manifest_sha256": {"type": "string", "pattern": HASH_PATTERN},
            "forbidden_action_registry_sha256": {
                "type": "string",
                "pattern": HASH_PATTERN,
            },
        },
    }


def valid_job(job_id: str = "JOB-001") -> dict:
    return {
        "job_id": job_id,
        "execution_zone": "TRUSTED_PHASE_B",
        "allowed_inputs": [{"sha256": "[HASH]"}],
        "source_manifest_sha256": "[HASH]",
        "forbidden_action_registry_sha256": "[HASH]",
    }


def valid_claim() -> dict:
    return {"answerability": "ambiguous", "claims": []}


def valid_observation() -> dict:
    return {"observations": [], "warnings": []}


def valid_worker(job_id: str = "WORK-001") -> dict:
    return {
        "job_id": job_id,
        "attempt_id": "ATTEMPT-001",
        "status": "complete",
        "escalation": None,
        "task_payload_schema_id": "observation/1.0",
        "payload": valid_observation(),
        "model_revision": "REVISION-001",
        "inference_profile_id": "PROFILE-001",
        "prompt_sha256": "[HASH]",
    }


def public_research_worker(source_url: str) -> dict:
    value = valid_worker("WORK-RESEARCH")
    value["task_payload_schema_id"] = "public-research/1.0"
    value["payload"] = {
        "recommendation": "test",
        "claims": [
            {
                "claim": "published",
                "kind": "published_fact",
                "source_urls": [source_url],
                "limitation": None,
            }
        ],
        "artefact_refs": [],
        "test_refs": [],
        "unresolved_risks": [],
    }
    return value


def encode(value: object, language: str) -> str:
    if isinstance(value, str):
        return value
    if language == "json":
        return json.dumps(value, indent=2)
    return yaml.safe_dump(value, sort_keys=False)


def code_block(
    language: str,
    value: object,
    annotation: str | None = None,
) -> str:
    annotation_attr = (
        f' data-p42-contract="{html.escape(annotation, quote=True)}"'
        if annotation
        else ""
    )
    text = html.escape(encode(value, language))
    # Pandoc puts fenced-code attributes on this enclosing sourceCode div.
    return (
        f'<div class="sourceCode"{annotation_attr}>'
        f'<pre class="sourceCode {language}"><code class="sourceCode {language}">'
        f"{text}</code></pre></div>"
    )


def section(section_id: str, *blocks: str) -> str:
    return f'<section id="{section_id}">' + "".join(blocks) + "</section>"


def build_guide(
    *,
    yaml_job: object | None = None,
    json_job: object | None = None,
    worker_schema_value: dict | None = None,
    job_schema_value: dict | None = None,
    extra_html: str = "",
    extra_worker_examples: tuple[dict, ...] = (),
) -> str:
    yaml_job = valid_job("JOB-YAML") if yaml_job is None else yaml_job
    json_job = valid_job("JOB-JSON") if json_job is None else json_job
    worker_schema_value = (
        worker_schema() if worker_schema_value is None else worker_schema_value
    )
    job_schema_value = (
        job_schema() if job_schema_value is None else job_schema_value
    )

    sections = [
        section(
            "ai-task-envelope",
            code_block("yaml", yaml_job, validator.KIND_JOB),
        ),
        section(
            "step-a5-qualify-the-answer-model",
            code_block("json", valid_claim(), "claim-evidence-response/1.1"),
        ),
        section(
            "step-b4-observe-each-document-before-aggregating",
            code_block("json", valid_observation(), "observation/1.0"),
        ),
        section("b.1-experiment-manifest", code_block("yaml", {"run_id": "R1"})),
        section("b.2-canonical-evidence-object", code_block("json", {"id": "E1"})),
        section(
            "b.3-claimevidence-response",
            code_block("json", valid_claim(), "claim-evidence-response/1.1"),
        ),
        section("b.4-archetype-policy-object", code_block("json", {"id": "A1"})),
        section("b.5-fictional-truth-occurrence", code_block("json", {"id": "T1"})),
        section("b.6-factorised-synthetic-case", code_block("yaml", {"id": "S1"})),
        section(
            "b.7-common-worker-response-schema",
            code_block("json", worker_schema_value, validator.WORKER_SCHEMA_ID),
        ),
        section(
            "b.8-job-envelope-schema",
            code_block("json", job_schema_value, validator.JOB_SCHEMA_ID),
        ),
        section(
            "b.9-access-resource-and-rule-profiles",
            code_block("yaml", {"profile": "access"}),
            code_block("yaml", {"profile": "resource"}),
            code_block("yaml", {"profile": "rules"}),
        ),
        section(
            "f.3-standard-job-envelope",
            code_block("json", json_job, validator.KIND_JOB),
        ),
        section(
            "f.12-response-contracts",
            code_block("json", valid_worker("WORK-1"), validator.KIND_WORKER),
            code_block("json", valid_worker("WORK-2"), validator.KIND_WORKER),
            *(
                code_block("json", value, validator.KIND_WORKER)
                for value in extra_worker_examples
            ),
        ),
    ]
    return "<!doctype html><html><body>" + "".join(sections) + extra_html + "</body></html>"


class GuideValidatorTests(unittest.TestCase):
    def run_guide(self, source: str) -> tuple[int, str]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "guide.html"
            path.write_text(source, encoding="utf-8")
            output = io.StringIO()
            result = validator.validate_guide(path, stream=output)
            return result, output.getvalue()

    def test_valid_annotated_guide_passes(self) -> None:
        result, output = self.run_guide(build_guide())
        self.assertEqual(result, validator.EXIT_OK, output)
        self.assertIn("all contracts consistent", output)

    def test_missing_discriminator_key_cannot_fall_out_of_validation(self) -> None:
        job = valid_job()
        del job["allowed_inputs"]
        result, output = self.run_guide(build_guide(json_job=job))
        self.assertEqual(result, validator.EXIT_DRIFT)
        self.assertIn("'allowed_inputs' is a required property", output)

    def test_duplicate_json_key_is_rejected(self) -> None:
        raw = json.dumps(valid_job()).replace("{", '{"job_id":"DUP",', 1)
        result, output = self.run_guide(build_guide(json_job=raw))
        self.assertEqual(result, validator.EXIT_DRIFT)
        self.assertIn("duplicate JSON key 'job_id'", output)

    def test_duplicate_yaml_key_is_rejected(self) -> None:
        raw = "job_id: FIRST\n" + yaml.safe_dump(valid_job(), sort_keys=False)
        result, output = self.run_guide(build_guide(yaml_job=raw))
        self.assertEqual(result, validator.EXIT_DRIFT)
        self.assertIn("duplicate YAML key 'job_id'", output)

    def test_placeholder_must_be_exact_and_at_an_allowed_path(self) -> None:
        job = valid_job()
        job["source_manifest_sha256"] = "malformed-[HASH]-value"
        result, output = self.run_guide(build_guide(json_job=job))
        self.assertEqual(result, validator.EXIT_DRIFT)
        self.assertIn("does not match", output)

    def test_duplicate_exact_schema_id_is_rejected(self) -> None:
        duplicate = section(
            "b.7-common-worker-response-schema",
            code_block("json", worker_schema(), validator.WORKER_SCHEMA_ID),
        )
        result, output = self.run_guide(build_guide(extra_html=duplicate))
        self.assertEqual(result, validator.EXIT_DRIFT)
        self.assertIn("found 2", output)

    def test_lookalike_schema_id_is_rejected(self) -> None:
        lookalike = worker_schema("https://unapproved.invalid/worker-response/1.1")
        result, output = self.run_guide(build_guide(worker_schema_value=lookalike))
        self.assertEqual(result, validator.EXIT_DRIFT)
        self.assertIn("lookalike schema ID", output)
        self.assertIn("found 0", output)

    def test_unclassified_machine_readable_block_is_rejected(self) -> None:
        extra = section("new-unreviewed-section", code_block("json", {"x": 1}))
        result, output = self.run_guide(build_guide(extra_html=extra))
        self.assertEqual(result, validator.EXIT_DRIFT)
        self.assertIn("unclassified section", output)

    def test_explicit_annotation_allows_new_reviewed_block(self) -> None:
        extra = section(
            "new-reviewed-section",
            code_block("json", valid_observation(), "observation/1.0"),
        )
        result, output = self.run_guide(build_guide(extra_html=extra))
        self.assertEqual(result, validator.EXIT_OK, output)

    def test_bash_brace_group_is_not_misclassified_as_json(self) -> None:
        extra = section(
            "shell-example",
            '<pre class="sourceCode bash"><code class="sourceCode bash">'
            "{ echo hello; }</code></pre>",
        )
        result, output = self.run_guide(build_guide(extra_html=extra))
        self.assertEqual(result, validator.EXIT_OK, output)

    def test_uri_format_is_enforced(self) -> None:
        bad_worker = public_research_worker("not a URI")
        result, output = self.run_guide(
            build_guide(extra_worker_examples=(bad_worker,))
        )
        self.assertEqual(result, validator.EXIT_DRIFT)
        self.assertIn("is not a 'uri'", output)

    def test_complete_worker_requires_task_payload(self) -> None:
        bad_worker = valid_worker("WORK-NULL-COMPLETE")
        bad_worker["payload"] = None
        result, output = self.run_guide(
            build_guide(extra_worker_examples=(bad_worker,))
        )
        self.assertEqual(result, validator.EXIT_DRIFT)
        self.assertIn("None is not of type 'object'", output)

    def test_needs_escalation_rejects_partial_payload(self) -> None:
        bad_worker = valid_worker("WORK-PARTIAL-ESCALATION")
        bad_worker["status"] = "needs_escalation"
        bad_worker["escalation"] = {
            "code": "EVIDENCE_CONFLICT",
            "field_ids": [],
            "evidence_ids": [],
        }
        result, output = self.run_guide(
            build_guide(extra_worker_examples=(bad_worker,))
        )
        self.assertEqual(result, validator.EXIT_DRIFT)
        self.assertIn("is not of type 'null'", output)

    def test_failure_status_requires_matching_closed_code(self) -> None:
        bad_worker = valid_worker("WORK-WRONG-ROUTE")
        bad_worker["status"] = "data_boundary_blocked"
        bad_worker["payload"] = None
        bad_worker["escalation"] = {
            "code": "TOOL_UNAVAILABLE",
            "field_ids": [],
            "evidence_ids": [],
        }
        result, output = self.run_guide(
            build_guide(extra_worker_examples=(bad_worker,))
        )
        self.assertEqual(result, validator.EXIT_DRIFT)
        self.assertIn("DATA_BOUNDARY_MISMATCH", output)

    def test_every_answerability_state_is_accepted(self) -> None:
        for state in (
            "fully_answerable",
            "partly_answerable",
            "not_answerable",
            "ambiguous",
            "conflicting_authority",
        ):
            with self.subTest(state=state):
                claim = valid_claim()
                claim["answerability"] = state
                result, output = self.run_guide(
                    build_guide(json_job=valid_job(), yaml_job=valid_job())
                    .replace(
                        html.escape(json.dumps(valid_claim(), indent=2)),
                        html.escape(json.dumps(claim, indent=2)),
                    )
                )
                self.assertEqual(result, validator.EXIT_OK, output)

    def test_missing_input_has_controlled_tool_error(self) -> None:
        missing = REPO_ROOT / "does-not-exist.html"
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            result = validator.main([str(missing)])
        self.assertEqual(result, validator.EXIT_TOOL_ERROR)
        self.assertIn("FATAL: cannot stat", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
