#!/usr/bin/env python3
"""Validate machine-readable contracts embedded in the P42-KB guide HTML.

Usage:
    python3 tools/validate_guide_contracts.py path/to/guide.html

Exit codes:
    0  Every classified example and required schema is consistent.
    1  Contract drift, malformed machine-readable content, or missing coverage.
    2  Invocation, dependency, input-file, or validator-internal failure.

The guide predates explicit per-block annotations, so this validator contains a
small, reviewable section coverage manifest. New JSON/YAML blocks must either be
added to that manifest or carry ``data-p42-contract`` on their Pandoc
``sourceCode`` wrapper, ``pre``, or ``code`` element. Supported annotation
values are documented in
``ANNOTATION_TO_KIND`` below.

Only an *exact* ``[HASH]`` or ``[SHA256]`` token is accepted as a documentation
placeholder, and only in a known SHA-256 field. Other placeholder-looking text
is validated literally.

Install the exact dependencies from ``requirements-guide-validation.lock``.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable, TextIO
from urllib.parse import urlsplit

try:
    import yaml
    from jsonschema import Draft202012Validator, FormatChecker
    from jsonschema.exceptions import SchemaError
except ImportError as exc:  # pragma: no cover - exercised by deployment
    print(
        "FATAL: missing guide-validator dependency "
        f"{getattr(exc, 'name', None) or str(exc)!r}; "
        "install requirements-guide-validation.lock",
        file=sys.stderr,
    )
    raise SystemExit(2) from None


EXIT_OK = 0
EXIT_DRIFT = 1
EXIT_TOOL_ERROR = 2

MAX_HTML_BYTES = 20_000_000
MAX_BLOCK_CHARS = 2_000_000

WORKER_SCHEMA_ID = "https://p42.example/schema/worker-response/1.1"
JOB_SCHEMA_ID = "https://p42.example/schema/job-envelope/1.1"

KIND_WORKER_SCHEMA = "schema:worker-response/1.1"
KIND_JOB_SCHEMA = "schema:job-envelope/1.1"
KIND_WORKER = "worker-response/1.1"
KIND_JOB = "job-envelope/1.1"
KIND_SYNTAX_ONLY = "syntax-only"
PAYLOAD_PREFIX = "payload:"

PAYLOAD_SCHEMA_TO_DEF = {
    "observation/1.0": "observation",
    "reviewer/1.0": "reviewer",
    "ast-prose-fill/1.0": "ast_fill",
    "claim-evidence-response/1.1": "claim_response",
    "protected-case-map/1.1": "protected_case_map",
    "code-build/1.0": "code_build",
    "public-research/1.0": "public_research",
    "frozen-report/1.0": "frozen_report",
}
REQUIRED_WORKER_DEFS = frozenset(PAYLOAD_SCHEMA_TO_DEF.values())

ANNOTATION_TO_KIND = {
    WORKER_SCHEMA_ID: KIND_WORKER_SCHEMA,
    JOB_SCHEMA_ID: KIND_JOB_SCHEMA,
    KIND_WORKER_SCHEMA: KIND_WORKER_SCHEMA,
    KIND_JOB_SCHEMA: KIND_JOB_SCHEMA,
    KIND_WORKER: KIND_WORKER,
    KIND_JOB: KIND_JOB,
    KIND_SYNTAX_ONLY: KIND_SYNTAX_ONLY,
    **{
        schema_id: f"{PAYLOAD_PREFIX}{def_name}"
        for schema_id, def_name in PAYLOAD_SCHEMA_TO_DEF.items()
    },
}


@dataclass(frozen=True)
class CoverageRule:
    kind: str
    minimum: int = 1


# This is deliberately explicit. A renamed section or a new machine-readable
# block must be reviewed instead of silently falling out of validation.
SECTION_RULES: dict[tuple[str, str], CoverageRule] = {
    ("ai-task-envelope", "yaml"): CoverageRule(KIND_JOB),
    ("step-a5-qualify-the-answer-model", "json"): CoverageRule(
        f"{PAYLOAD_PREFIX}claim_response"
    ),
    ("step-b4-observe-each-document-before-aggregating", "json"): CoverageRule(
        f"{PAYLOAD_PREFIX}observation"
    ),
    ("b.1-experiment-manifest", "yaml"): CoverageRule(KIND_SYNTAX_ONLY),
    ("b.2-canonical-evidence-object", "json"): CoverageRule(KIND_SYNTAX_ONLY),
    ("b.3-claimevidence-response", "json"): CoverageRule(
        f"{PAYLOAD_PREFIX}claim_response"
    ),
    ("b.4-archetype-policy-object", "json"): CoverageRule(KIND_SYNTAX_ONLY),
    ("b.5-fictional-truth-occurrence", "json"): CoverageRule(KIND_SYNTAX_ONLY),
    ("b.6-factorised-synthetic-case", "yaml"): CoverageRule(KIND_SYNTAX_ONLY),
    ("b.7-common-worker-response-schema", "json"): CoverageRule(
        KIND_WORKER_SCHEMA
    ),
    ("b.8-job-envelope-schema", "json"): CoverageRule(KIND_JOB_SCHEMA),
    ("b.9-access-resource-and-rule-profiles", "yaml"): CoverageRule(
        KIND_SYNTAX_ONLY, minimum=3
    ),
    ("f.3-standard-job-envelope", "json"): CoverageRule(KIND_JOB),
    ("f.12-response-contracts", "json"): CoverageRule(KIND_WORKER, minimum=2),
}

# Once the guide uses explicit annotations, these semantic minima replace the
# legacy section-ID minima. This keeps coverage stable if headings are renamed.
ANNOTATED_KIND_MINIMUMS: dict[str, int] = {
    KIND_WORKER_SCHEMA: 1,
    KIND_JOB_SCHEMA: 1,
    # One canonical worked job and one canonical claim example are sufficient.
    # The v1.2 guide deliberately removes duplicate full objects from the main
    # reading path; the schema and prompt appendices remain their sole homes.
    KIND_JOB: 1,
    KIND_WORKER: 2,
    f"{PAYLOAD_PREFIX}claim_response": 1,
    f"{PAYLOAD_PREFIX}observation": 1,
}


class GuideInputError(Exception):
    """The requested input cannot be safely or deterministically processed."""


class DuplicateKeyError(ValueError):
    """A JSON or YAML mapping contains a duplicate key."""


@dataclass
class CodeBlock:
    index: int
    text: str
    section_id: str | None
    classes: set[str] = field(default_factory=set)
    annotations: set[str] = field(default_factory=set)

    def language(self) -> str | None:
        languages: set[str] = set()
        for class_name in self.classes:
            candidate = class_name.lower()
            if candidate.startswith("language-"):
                candidate = candidate.removeprefix("language-")
            if candidate == "yml":
                candidate = "yaml"
            if candidate in {"json", "yaml"}:
                languages.add(candidate)
        if len(languages) > 1:
            raise GuideInputError(
                f"pre#{self.index} has conflicting code languages: "
                f"{', '.join(sorted(languages))}"
            )
        return next(iter(languages), None)

    def annotation(self) -> str | None:
        if len(self.annotations) > 1:
            raise GuideInputError(
                f"pre#{self.index} has conflicting data-p42-contract annotations: "
                f"{', '.join(sorted(self.annotations))}"
            )
        return next(iter(self.annotations), None)


class GuideHTMLParser(HTMLParser):
    """Extract rendered code blocks without executing or fetching content."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[CodeBlock] = []
        self._section_stack: list[str | None] = []
        self._div_annotation_stack: list[str | None] = []
        self._current: CodeBlock | None = None

    @staticmethod
    def _attrs(attrs: list[tuple[str, str | None]]) -> dict[str, str]:
        return {key: value or "" for key, value in attrs}

    @staticmethod
    def _classes(attrs: dict[str, str]) -> set[str]:
        return {part for part in attrs.get("class", "").split() if part}

    def _nearest_section(self) -> str | None:
        return next((item for item in reversed(self._section_stack) if item), None)

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        values = self._attrs(attrs)
        if tag == "section":
            self._section_stack.append(values.get("id") or None)
            return
        if tag == "div":
            self._div_annotation_stack.append(
                values.get("data-p42-contract") or None
            )
            return
        if tag == "pre":
            if self._current is not None:
                raise GuideInputError("nested <pre> elements are not supported")
            annotations = set()
            inherited = next(
                (
                    item
                    for item in reversed(self._div_annotation_stack)
                    if item is not None
                ),
                None,
            )
            if inherited:
                annotations.add(inherited)
            if values.get("data-p42-contract"):
                annotations.add(values["data-p42-contract"])
            self._current = CodeBlock(
                index=len(self.blocks),
                text="",
                section_id=self._nearest_section(),
                classes=self._classes(values),
                annotations=annotations,
            )
            return
        if tag == "code" and self._current is not None:
            self._current.classes.update(self._classes(values))
            if values.get("data-p42-contract"):
                self._current.annotations.add(values["data-p42-contract"])

    def handle_endtag(self, tag: str) -> None:
        if tag == "pre":
            if self._current is None:
                raise GuideInputError("encountered </pre> without <pre>")
            self.blocks.append(self._current)
            self._current = None
            return
        if tag == "section":
            if not self._section_stack:
                raise GuideInputError("encountered </section> without <section>")
            self._section_stack.pop()
            return
        if tag == "div":
            if not self._div_annotation_stack:
                raise GuideInputError("encountered </div> without <div>")
            self._div_annotation_stack.pop()

    def handle_data(self, data: str) -> None:
        if self._current is not None:
            self._current.text += data
            if len(self._current.text) > MAX_BLOCK_CHARS:
                raise GuideInputError(
                    f"pre#{self._current.index} exceeds {MAX_BLOCK_CHARS} characters"
                )

    def finish(self) -> list[CodeBlock]:
        self.close()
        if self._current is not None:
            raise GuideInputError("document ends inside an unclosed <pre> element")
        return self.blocks


class UniqueKeySafeLoader(yaml.SafeLoader):
    """Safe YAML loader which rejects duplicate mapping keys."""


def _construct_unique_mapping(
    loader: UniqueKeySafeLoader, node: yaml.nodes.MappingNode, deep: bool = False
) -> dict[Any, Any]:
    loader.flatten_mapping(node)
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=True)
        try:
            duplicate = key in mapping
        except TypeError as exc:
            raise DuplicateKeyError(
                f"unhashable YAML mapping key at line {key_node.start_mark.line + 1}"
            ) from exc
        if duplicate:
            raise DuplicateKeyError(
                f"duplicate YAML key {key!r} at line {key_node.start_mark.line + 1}"
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeySafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_unique_mapping
)


def _reject_json_duplicates(pairs: Iterable[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant {value!r}")


URI_FORMAT_CHECKER = FormatChecker()
_URI_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*$")
_BAD_URI_CHAR = re.compile(r"[\x00-\x20<>\"{}|\\^`]")
_BAD_PERCENT_ESCAPE = re.compile(r"%(?![0-9A-Fa-f]{2})")


@URI_FORMAT_CHECKER.checks("uri")
def _is_absolute_uri(value: object) -> bool:
    """Conservative RFC-3986-style absolute URI check for guide contracts."""

    if not isinstance(value, str):
        return True  # JSON Schema's type keyword owns type validation.
    if not value or _BAD_URI_CHAR.search(value) or _BAD_PERCENT_ESCAPE.search(value):
        return False
    try:
        parsed = urlsplit(value)
        # Accessing hostname also detects malformed bracketed IPv6 literals.
        hostname = parsed.hostname
    except ValueError:
        return False
    if not parsed.scheme or not _URI_SCHEME.fullmatch(parsed.scheme):
        return False
    if parsed.scheme.lower() in {"http", "https"} and not hostname:
        return False
    return True


@dataclass
class Reporter:
    stream: TextIO
    passes: int = 0
    failures: int = 0

    def passed(self, message: str) -> None:
        self.passes += 1
        print(f"[PASS] {message}", file=self.stream)

    def failed(self, message: str) -> None:
        self.failures += 1
        print(f"[FAIL] {message}", file=self.stream)


@dataclass
class ParsedBlock:
    block: CodeBlock
    language: str
    kind: str | None
    value: Any | None
    parsed: bool


def read_code_blocks(path: Path) -> list[CodeBlock]:
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise GuideInputError(f"cannot stat {path}: {exc}") from exc
    if not path.is_file():
        raise GuideInputError(f"not a regular file: {path}")
    if size > MAX_HTML_BYTES:
        raise GuideInputError(
            f"{path} is {size} bytes; maximum is {MAX_HTML_BYTES} bytes"
        )
    try:
        source = path.read_text(encoding="utf-8", errors="strict")
    except (OSError, UnicodeError) as exc:
        raise GuideInputError(f"cannot read {path} as strict UTF-8: {exc}") from exc
    parser = GuideHTMLParser()
    try:
        parser.feed(source)
        return parser.finish()
    except GuideInputError:
        raise
    except Exception as exc:  # HTMLParser errors should become controlled exit 2.
        raise GuideInputError(f"cannot parse guide HTML: {exc}") from exc


def parse_machine_block(block: CodeBlock, language: str) -> Any:
    text = block.text.strip()
    if not text:
        raise ValueError("empty machine-readable code block")
    if language == "json":
        return json.loads(
            text,
            object_pairs_hook=_reject_json_duplicates,
            parse_constant=_reject_json_constant,
        )
    if language == "yaml":
        value = yaml.load(text, Loader=UniqueKeySafeLoader)
        if value is None:
            raise ValueError("empty YAML document")
        return value
    raise AssertionError(f"unsupported machine-readable language: {language}")


def classify_block(
    block: CodeBlock, language: str, reporter: Reporter
) -> str | None:
    annotation = block.annotation()
    section_rule = SECTION_RULES.get((block.section_id or "", language))
    annotated_kind: str | None = None
    if annotation is not None:
        annotated_kind = ANNOTATION_TO_KIND.get(annotation)
        if annotated_kind is None:
            reporter.failed(
                f"pre#{block.index} has unknown data-p42-contract={annotation!r}"
            )
            return None
    if annotation is not None and section_rule and annotated_kind != section_rule.kind:
        reporter.failed(
            f"pre#{block.index} annotation selects {annotated_kind!r}, but section "
            f"{block.section_id!r} requires {section_rule.kind!r}"
        )
        return None
    kind = annotated_kind or (section_rule.kind if section_rule else None)
    if kind is None:
        reporter.failed(
            f"pre#{block.index} is {language} in unclassified section "
            f"{block.section_id!r}; add data-p42-contract or update SECTION_RULES"
        )
    return kind


def collect_machine_blocks(
    blocks: list[CodeBlock], reporter: Reporter
) -> list[ParsedBlock]:
    parsed_blocks: list[ParsedBlock] = []
    section_counts: Counter[tuple[str, str]] = Counter()
    kind_counts: Counter[str] = Counter()
    saw_annotation = False

    for block in blocks:
        language = block.language()
        annotation = block.annotation()
        saw_annotation |= annotation is not None
        if annotation is not None and language is None:
            reporter.failed(
                f"pre#{block.index} has data-p42-contract but no json/yaml language"
            )
            continue
        if language is None:
            stripped = block.text.lstrip()
            if not block.classes.intersection({"bash", "sh", "shell"}) and (
                stripped.startswith("{")
                or stripped.startswith("[")
                or stripped.startswith("job_id:")
            ):
                reporter.failed(
                    f"pre#{block.index} looks machine-readable but lacks an explicit "
                    "json/yaml code language"
                )
            continue

        key = (block.section_id or "", language)
        if key in SECTION_RULES:
            section_counts[key] += 1
        kind = classify_block(block, language, reporter)
        if kind is not None:
            kind_counts[kind] += 1
        try:
            value = parse_machine_block(block, language)
        except (json.JSONDecodeError, yaml.YAMLError, ValueError, DuplicateKeyError) as exc:
            reporter.failed(
                f"pre#{block.index} ({block.section_id or 'no-section'}, {language}) "
                f"does not parse safely: {exc}"
            )
            parsed_blocks.append(
                ParsedBlock(block, language, kind, value=None, parsed=False)
            )
            continue
        reporter.passed(
            f"pre#{block.index} ({block.section_id or 'no-section'}) has strict "
            f"{language.upper()} syntax"
        )
        parsed_blocks.append(ParsedBlock(block, language, kind, value, parsed=True))

    if saw_annotation:
        for kind, minimum in ANNOTATED_KIND_MINIMUMS.items():
            actual = kind_counts[kind]
            if actual < minimum:
                reporter.failed(
                    f"annotated coverage for {kind!r} is {actual}; "
                    f"minimum is {minimum}"
                )
    else:
        for key, rule in SECTION_RULES.items():
            actual = section_counts[key]
            if actual < rule.minimum:
                reporter.failed(
                    f"coverage for section {key[0]!r} ({key[1]}) is {actual}; "
                    f"minimum is {rule.minimum}"
                )

    return parsed_blocks


def find_exact_schema(
    parsed_blocks: list[ParsedBlock],
    exact_id: str,
    expected_kind: str,
    reporter: Reporter,
) -> dict[str, Any] | None:
    suffix = "/".join(exact_id.rsplit("/", 2)[-2:])
    exact: list[ParsedBlock] = []
    for item in parsed_blocks:
        if not item.parsed or not isinstance(item.value, dict):
            continue
        schema_id = item.value.get("$id")
        if schema_id == exact_id:
            exact.append(item)
            if item.kind != expected_kind:
                reporter.failed(
                    f"pre#{item.block.index} contains {exact_id!r} but is classified "
                    f"as {item.kind!r}, not {expected_kind!r}"
                )
        elif isinstance(schema_id, str) and schema_id.endswith(suffix):
            reporter.failed(
                f"pre#{item.block.index} has lookalike schema ID {schema_id!r}; "
                f"expected exact ID {exact_id!r}"
            )
    if len(exact) != 1:
        reporter.failed(
            f"expected exactly one schema with $id {exact_id!r}; found {len(exact)}"
        )
        return None
    return exact[0].value


def check_schema(
    label: str, schema: dict[str, Any], reporter: Reporter
) -> bool:
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        reporter.failed(f"{label} is not a valid Draft 2020-12 schema: {exc.message}")
        return False
    except Exception as exc:
        reporter.failed(f"{label} cannot be checked: {exc}")
        return False
    reporter.passed(f"{label} is a valid Draft 2020-12 schema")
    return True


_SHA_PLACEHOLDER_PATHS: dict[str, tuple[tuple[object, ...], ...]] = {
    KIND_JOB: (
        ("source_manifest_sha256",),
        ("prompt_sha256",),
        ("schema_sha256",),
        ("tool_registry_sha256",),
        ("validator_rule_registry_sha256",),
        ("forbidden_action_registry_sha256",),
        ("allowed_inputs", "*", "sha256"),
    ),
    KIND_WORKER: (
        ("prompt_sha256",),
        ("payload", "candidate_sha256"),
        ("payload", "issue_registry_sha256"),
    ),
}
_EXACT_SHA_PLACEHOLDERS = frozenset({"[HASH]", "[SHA256]"})


def _path_matches(pattern: tuple[object, ...], path: tuple[object, ...]) -> bool:
    return len(pattern) == len(path) and all(
        expected == "*" or expected == actual
        for expected, actual in zip(pattern, path)
    )


def normalize_documentation_placeholders(instance: Any, kind: str) -> Any:
    """Replace only exact SHA placeholders at explicitly permitted paths."""

    allowed_paths = _SHA_PLACEHOLDER_PATHS.get(kind, ())
    result = copy.deepcopy(instance)

    def visit(value: Any, path: tuple[object, ...]) -> Any:
        if (
            isinstance(value, str)
            and value in _EXACT_SHA_PLACEHOLDERS
            and any(_path_matches(pattern, path) for pattern in allowed_paths)
        ):
            return "0" * 64
        if isinstance(value, dict):
            return {key: visit(child, path + (key,)) for key, child in value.items()}
        if isinstance(value, list):
            return [visit(child, path + (index,)) for index, child in enumerate(value)]
        return value

    return visit(result, ())


def payload_schema(worker_schema: dict[str, Any], def_name: str) -> dict[str, Any]:
    definition = copy.deepcopy(worker_schema["$defs"][def_name])
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        **definition,
        "$defs": copy.deepcopy(worker_schema["$defs"]),
    }


def _json_pointer(parts: Iterable[object]) -> str:
    values = [str(part).replace("~", "~0").replace("/", "~1") for part in parts]
    return "/" + "/".join(values) if values else "/"


def validate_instance(
    label: str,
    instance: Any,
    schema: dict[str, Any],
    placeholder_kind: str,
    reporter: Reporter,
) -> bool:
    normalized = normalize_documentation_placeholders(instance, placeholder_kind)
    try:
        validator = Draft202012Validator(
            schema, format_checker=URI_FORMAT_CHECKER
        )
        errors = sorted(
            validator.iter_errors(normalized),
            key=lambda error: (
                tuple(str(part) for part in error.absolute_path),
                tuple(str(part) for part in error.absolute_schema_path),
                error.message,
            ),
        )
    except Exception as exc:
        reporter.failed(f"{label} could not be validated: {exc}")
        return False
    if not errors:
        reporter.passed(f"{label} satisfies {placeholder_kind}")
        return True
    reporter.failed(f"{label} has {len(errors)} contract error(s)")
    for error in errors:
        print(
            f"    - {_json_pointer(error.absolute_path)}: {error.message}",
            file=reporter.stream,
        )
    return False


def validate_guide(path: Path, stream: TextIO = sys.stdout) -> int:
    reporter = Reporter(stream)
    blocks = read_code_blocks(path)
    parsed_blocks = collect_machine_blocks(blocks, reporter)

    worker_schema = find_exact_schema(
        parsed_blocks, WORKER_SCHEMA_ID, KIND_WORKER_SCHEMA, reporter
    )
    job_schema = find_exact_schema(
        parsed_blocks, JOB_SCHEMA_ID, KIND_JOB_SCHEMA, reporter
    )

    schemas_ready = worker_schema is not None and job_schema is not None
    if worker_schema is not None:
        schemas_ready &= check_schema("worker-response schema", worker_schema, reporter)
        defs = worker_schema.get("$defs")
        if not isinstance(defs, dict):
            reporter.failed("worker-response schema has no object-valued $defs")
            schemas_ready = False
        else:
            missing_defs = sorted(REQUIRED_WORKER_DEFS - defs.keys())
            if missing_defs:
                reporter.failed(
                    "worker-response schema is missing required payload definitions: "
                    + ", ".join(missing_defs)
                )
                schemas_ready = False
    if job_schema is not None:
        schemas_ready &= check_schema("job-envelope schema", job_schema, reporter)

    if schemas_ready and worker_schema is not None and job_schema is not None:
        for item in parsed_blocks:
            if not item.parsed or item.kind in {
                None,
                KIND_SYNTAX_ONLY,
                KIND_WORKER_SCHEMA,
                KIND_JOB_SCHEMA,
            }:
                continue
            label = (
                f"pre#{item.block.index} ({item.block.section_id or 'no-section'})"
            )
            if item.kind == KIND_JOB:
                validate_instance(label, item.value, job_schema, KIND_JOB, reporter)
            elif item.kind == KIND_WORKER:
                validate_instance(
                    label, item.value, worker_schema, KIND_WORKER, reporter
                )
            elif item.kind.startswith(PAYLOAD_PREFIX):
                def_name = item.kind.removeprefix(PAYLOAD_PREFIX)
                try:
                    selected_schema = payload_schema(worker_schema, def_name)
                except KeyError:
                    reporter.failed(
                        f"{label} selects missing worker $def {def_name!r}"
                    )
                    continue
                validate_instance(
                    label, item.value, selected_schema, item.kind, reporter
                )
            else:  # Defensive: annotations and section rules must be exhaustive.
                reporter.failed(f"{label} has unsupported classification {item.kind!r}")

    print(file=stream)
    if reporter.failures:
        print(
            f"RESULT: CONTRACT DRIFT DETECTED "
            f"({reporter.failures} failure(s), {reporter.passes} pass(es))",
            file=stream,
        )
        return EXIT_DRIFT
    print(
        f"RESULT: all contracts consistent ({reporter.passes} checks passed)",
        file=stream,
    )
    return EXIT_OK


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("guide_html", type=Path, help="rendered guide HTML to validate")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="show a traceback for unexpected validator-internal errors",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    try:
        return validate_guide(args.guide_html)
    except GuideInputError as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return EXIT_TOOL_ERROR
    except KeyboardInterrupt:
        print("FATAL: validation interrupted", file=sys.stderr)
        return 130
    except Exception as exc:  # noqa: BLE001 - controlled CI boundary
        if args.debug:
            raise
        print(
            f"FATAL: validator-internal error: {type(exc).__name__}: {exc}; "
            "rerun with --debug",
            file=sys.stderr,
        )
        return EXIT_TOOL_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
