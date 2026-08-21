# Review — P42-KB Document Archetype and Synthetic Evaluation Corpus Qualification Guide v1.0

| | |
|---|---|
| **Documents reviewed** | `KB_Project_P42_KB_Document_Archetype_and_Synthetic_Evaluation_Corpus_Qualification_Guide_v1.0.html` (primary), cross-checked against `Project_Definition_and_High_Level_Requirements_v1.0.docx`, `PoC_Implementation_Plan_v0.9.docx`, `Candidate_Technical_Concepts_and_Design_Considerations_v1.0.docx` |
| **Review date** | 21 August 2026 |
| **Reviewer** | Claude (AI-assisted review) |
| **Method** | Full close reading of all four documents, plus programmatic verification: JSON-Schema validation of every machine-readable example against the guide's own Appendix B contracts, internal-link integrity check, arithmetic verification of statistical and effort claims, shell-script and container-command inspection, cross-document consistency sweep |
| **Verdict** | **The approach is fundamentally sound and unusually rigorous — approve with corrections.** Three sequencing/topology issues (F1–F3) should be resolved before Gate −1, the machine-readable contract inconsistencies (F4) before controller implementation, and the fail-open operational pipelines (F6) before any asset freeze or trusted import. Nothing found invalidates the strategy itself. |

> **Amendment note.** This remains a review of guide v1.0. It was amended after an independent cross-check to correct overstatements in F5, separate confirmed defects from an optional profile improvement in F6, correct two inaccurate editorial observations in F8, and add previously missed fail-open checksum/archive-pipeline defects.

> **Disposition in guide v1.1.** The published v1.1 Markdown, HTML and DOCX address the guide-level corrections in F1–F7 and the applicable F8 items: the one-Spark transition is sequenced explicitly; controller gates are tiered; Gate 3 authorises at most one bounded extension; examples and schemas use versioned `/1.1` contracts; answerability includes ambiguity; action/rule registries and an evidence-ID grammar are defined; audit-bound expectations are explicit; and the freeze, archive, smoke-test and Qdrant examples fail closed. The repository validator now checks tagged examples against the exact embedded contracts and has mutation tests for its former silent-pass modes. Standalone production `contracts/`, `prompts/` and `policies/` packages, a real controller implementation, and target-DGX negative/runtime qualification remain implementation work rather than claims made by the guide.

---

## 1. Overall assessment of the approach

The guide's core strategy holds up well against both the governing project documents and the current state of the art it cites. Its load-bearing choices are the right ones. Treating synthetic documents as a test rig rather than a product, and gating the whole synthetic work package behind a necessity test with an explicit deferral outcome, correctly protects the real-first PoC commitment in the PoC Plan (§2.4 tiers, §4.4). Generating fictional truth first (truth graph → document AST → deterministic renderer) and deriving oracles from the truth model rather than from LLM prose is the strongest known defence against the circular self-grading trap, and the guide goes further than the Concepts document by demanding a *separately implemented* final truth/scorer control (§11.10) — a genuine improvement. The R0–R4 evidence-level taxonomy for multi-model review (§6.6) is a real contribution: it names precisely why "two agreeing AIs" is screening rather than validation, and it is applied consistently throughout the document. The three-way separation of model-visible evidence, hidden fictional truth and normative expert truth (§11.10), the empirical-prevalence versus normative-policy versus scenario-policy distinction (§11.6), and the three leakage threat classes (§11.11) are all methodologically correct and clearly assigned to owners.

The statistical treatment is honest and, where checkable, exact. The rule-of-three claims were verified: for a one-sided 95% bound with zero observed misses, n = 59 gives ln(0.05)/ln(0.95) → a bound near 5%, and n = 299 gives a bound near 1% — both figures in §6.7 are correct to the unit. The SME-effort arithmetic (§13.4) is internally consistent with its own per-item assumptions. The memory envelope (§6.11) explicitly disarms its own additive-reading trap (32+16+40+40 = 128 GB). Benchmark population numbers (30–50 real / 50–100 synthetic / 3–5 historical) match the PoC Plan §6.2 and Concepts §13.1 exactly, and the guide correctly declares the PoC Plan authoritative. The T17 running example is coherent across all four documents and across every appendix object that reuses it (truth occurrence, AST, defect variant, scenario, counterfactual factors).

Document quality is also high in mechanical terms: all 1,278 internal anchors resolve, there are no duplicate IDs, and the page has no external script/style/font dependencies — the 96 external URLs are citation links only, so the file renders fully offline, consistent with the project's own air-gap ethos. The embedded script is a benign reading aid (theme, TOC search, glossary filter).

The residual risk to the objective is therefore not that the method is wrong, but that the machinery consumes the ten-week timebox, and that a handful of internal contradictions would propagate into the controller if implemented as written. Those are the findings below.

---

## 2. Findings register

| ID | Severity | Location | Finding |
|---|---|---|---|
| F1 | **Major** | Guide §9–§10, §13.1 vs PoC Plan §7, §8.1 | One physical DGX Spark cannot be in connected Phase A and trusted Phase B at the same time, yet the schedule requires both during weeks 1–7 |
| F2 | **Major** | Guide §6.8, §9.1, §11, G.2 | The tested controller is a hard gate for *all* Phase B headline evidence, putting the core PoC's protected-real results on the controller's critical path |
| F3 | **Major** | Guide §13.1 (Gate 3 row) vs §11.1 | Circular sequencing: the necessity test is scheduled before Phase B authorisation but requires Phase B material to run |
| F4 | **Major** | Guide §6.8, §9.6 vs Appendix B; §3.9; Concepts §8.1 | Machine-readable contract inconsistencies, machine-verified: both flagship inline examples fail the guide's own schemas; enum/vocabulary/ID-grammar drift |
| F6 | **Major** | Appendix A.2, A.3, A.5–A.9, §6.10/§6.14 | Traversal/archive failures can be masked and produce apparently valid incomplete manifests or archives; additional locale, Docker-network, xargs and smoke-assertion defects also require correction. Interactive co-residency is an optional measured optimisation, not a correctness defect |
| F5 | Moderate | Guide §6.7, §8.3, §12.5, §13 | At the illustrative 60-bundle/20%-audit envelope, a low residual-risk bound is unavailable without near-full audit; make the likely descriptive-feasibility outcome explicit at activation |
| F7 | Moderate | Guide §13.1 weeks 7–9 vs PoC Plan §4.4, Gate 3 | The Airbus family study and the specialist FA vertical silently compete for the same weeks 7–9 window and team |
| F8 | Minor | Repo-wide, several documents | Missing contract/prompt scaffolding in the repo, an empty §2.3 in the PoC Plan, filename/title mismatch, undefined acronym, unrecorded deviation from the Concepts model-comparison envelope, missing HLR traceability, undefined data-class propagation rules, and small editorial items |

---

## 3. Major findings in detail

### F1 — Environment topology: one Spark cannot be in two zones (Major)

The security model is strict and correct: the transition exit criterion states that "Airbus data and Airbus-derived prompts have never touched the Phase A or cloud system state" (§10.5), and every AIRBUS_CONTROLLED/AIRBUS_DERIVED job requires trusted Phase B (§6.2, B.8 policy tests). But the schedule in §13.1 has the same machine doing connected Phase A work (parser/retrieval bake-off, public rehearsal, weeks 3–5) at the same time as protected core-PoC work ("parsing, hybrid retrieval, cited Answer" on the real corpus, weeks 3–5; "bounded Connect, authority and references", weeks 5–7). The PoC Plan §8.1 names the single DGX Spark as the default PoC platform, and PoC 0/PoC 1 (weeks 1–5) ingest and answer over the authorised real corpus. Under the guide's own rules, none of that protected work may run on the Spark until after the airlock — which §13.1 implicitly places around Gate 3 (week 7). The plan as written double-books the machine, and the guide only addresses the real-case *map* ("use its existing approved protected environment", §8.4), not the compute for protected ingestion, retrieval and cited answering.

**Proposed correction.** Redefine Phase A on the Spark as *acquisition and smoke-testing only*, and re-scope "Phase A" from "everything public" to "everything requiring network egress" — which is the cleaner security definition anyway. Concretely: weeks 1–2, download and over-provision every model, container, wheelhouse, public fixture and benchmark asset (A0 plus the acquisition parts of A2–A8), run the smoke gates, freeze the transition bundle; airlock at the end of week 2; from week 3 the Spark is in trusted Phase B for the rest of the PoC. All bake-offs and rehearsals (A2–A6, A7) then run *offline* on public fixtures inside Phase B — nothing in the classification table forbids processing PUBLIC_CLEARED material locally, so no methodological content changes. Cloud AI research (which never needed the Spark) continues throughout on an ordinary connected workstation. Weeks 1–2 protected baseline (exact + SQLite FTS5/BM25 is deliberately CPU-only per A1) runs on the existing approved Airbus environment until the Spark crosses. Budget one contingency re-airlock cycle for forgotten assets, and add an explicit environment-timeline figure to §13.1. The alternative resolutions — a second GPU environment, or accepting that PoC 1 slips to week 4+ — should be recorded and rejected/accepted explicitly at Gate −1.

### F2 — The controller gates all Phase B evidence, including the core PoC (Major)

§6.8 states the AI-first route "is not operational until a tested controller can" satisfy seven capabilities, §9.1 adds that until then "AI work is exploratory and cannot support a headline result", and G.2 confirms the controller is specified but not shipped. Because the Phase B micro-batch procedure (§11, F.13 Pipeline 2) covers the *core* retrieval/answer evaluation as well as the synthetic study, the committed PoC's protected-real headline evidence becomes hostage to a non-trivial software build. The controller as specified (classification registry, schema validation with unknown-field rejection, policy-selected execution profiles, atomic resume, watchdogs, deterministic sampling, quarantine routing, prompt-injection fixtures, crash/restart tests) is realistically weeks of engineering even AI-assisted, on a plan staffed at roughly two FTE.

**Proposed correction.** Split the controller mandate into two tiers and say which evidence each tier gates. Tier 1, *security-mandatory and non-negotiable*: execution zones, no-egress enforcement, access profiles/mounts, classification registry, hashing of inputs/outputs, run manifests. These are airlock preconditions for any protected processing, but they are mostly infrastructure configuration plus a thin wrapper, not the full state machine. Tier 2, *workflow machinery*: typed job envelopes, schema-validated worker loops, retry/repair/quarantine state, sentinel-sampling export. Require Tier 2 only for the AI-first batch production of the synthetic/archetype study (observation, generation, review routing), which is where its value lies. Let the core retrieval/answer benchmark run under the simpler reproducibility discipline the PoC Plan §14 and the guide's own B.1 experiment manifest already define (versioned scripts, frozen configs, hashes). This preserves every security property while taking the committed PoC off the controller's critical path.

### F3 — Necessity-test circularity at Gate 3 (Major)

§13.1's Gate 3 row reads "run necessity test and authorise or defer Phase B", but the necessity test defined in §11.1 (Step B0) compares a neutral arm against "archetypes induced from the approved source families" — which requires Phase B access and a working slice of the B1–B8 machinery to produce the Airbus-informed arm. As written, the test that decides whether to authorise Phase B can only be run inside Phase B.

**Proposed correction.** Reword Gate 3 to: "authorise a *bounded Phase B pilot* whose first step (B0) is the necessity test on a small pilot family; continuation of proprietary archetype work beyond B0 requires the recorded margin." §11.1 already carries the continuation logic ("Continue proprietary archetype work only if…"), so only the schedule row needs fixing. Worth adding one honest limitation note to §11.1: the SME who approves the "neutral" arm inevitably carries Airbus document structure in their head, so the neutral arm is biased upward. That bias is conservative — it makes the expensive Airbus-informed path *harder* to justify, which is the safe direction — but it should be recorded in the pre-registration as a known asymmetry.

### F4 — Machine-readable contract inconsistencies (Major, machine-verified)

The guide rightly insists that "a schema name in a prompt is not enforcement" (F.12) and that malformed responses are operational failures (§9.6). It should therefore hold its own examples to that standard; today it does not. Every finding below was confirmed by validating the extracted JSON/YAML against the guide's own Appendix B schemas with a Draft 2020-12 validator (full output in Annex A).

The §6.8 flagship job-envelope example fails the B.8 `job-envelope/1.0` schema on nine substantive counts: four missing required fields (`task_type`, `config_id`, `approved_provider_surface_feature`, `provider_retention_profile_id`), two unknown root fields rejected by `additionalProperties: false` (`required_output`, `evidence_required`), an unknown `allowed_inputs` field (`evidence_pack_sha256`) alongside two missing required ones (`sha256`, `lineage_id`), and a missing required `limits.max_tool_calls`. The F.3 example, by contrast, is fully compliant — §6.8 is simply a stale earlier draft of the same object, and it is the one an implementer meets first.

The §9.6 answer-envelope example fails the B.7 `claim-evidence-response/1.0` contract on six counts: `"answerability": "ANSWERABLE"` is not in the enum (`fully_answerable | partly_answerable | not_answerable | conflicting_authority`), the claim lacks the required `claim_id`, `state`, `contradicting_evidence_ids` and `calculation`, and the root carries a `confidence` field the schema rejects. The B.3 example validates cleanly — again, one stale sibling of a correct object.

Three vocabulary drifts would surface as controller bugs. First, §6.8 references escalation rule `MISSING_CRITICAL_EVIDENCE`, which is defined nowhere; B.9's registry defines `CRITICAL_CONTENT_UNREADABLE` for that role. Second, forbidden-action names differ between the two envelope examples for the same concepts (`external_network` vs `network`; `write_source_corpus` vs `write_source_record`) with no registry to arbitrate. Third, the evidence-ID grammar differs between examples: `ICD-009-C:p14:table3:r17` in §9.6 versus `ICD-009:C:p14:table3:r17` (revision as its own colon segment) in B.2/B.3 — B.2 should define the grammar once and everything else should conform.

Finally, an internal contradiction with both the guide itself and the governing Concepts document: §3.9 says the system must distinguish "the question is ambiguous", and the Concepts document's reference model (§8.1) has a five-state answerability vocabulary including `AMBIGUOUS`, yet the guide's enum has no ambiguous state. Either add the state, or record an explicit mapping decision (e.g., ambiguous → `not_answerable` plus a mandatory limitation naming the ambiguity) in both documents.

**Proposed correction.** Fix §6.8 and §9.6 to be schema-valid (or generate them *from* the schemas); create the action/rule registries B.9 implies; define the evidence-ID grammar in B.2; resolve the answerability vocabulary against Concepts §8.1 in both documents. Then keep it fixed mechanically: extract the Appendix B schemas and Appendix F prompts into version-controlled files (see F8) and add a CI check that re-extracts every example from the HTML and validates it — the validation script used for this review is delivered alongside (`tools/validate_guide_contracts.py`) and currently reports exactly the failures above.

### F6 — Operational pipelines can fail open (Major, highest correction priority)

The most consequential missed defect is not cosmetic: several shell pipelines can report success after an earlier stage failed. The guide presents the commands as examples of a controlled pattern, so an implementer is likely to compose them into a script. No shown wrapper establishes `pipefail`, and `set -e` alone would not make a pipeline fail when its final command succeeds.

1. **Checksum completeness can be lost silently.** A.2 uses `find | sort | xargs sha256sum`. If traversal or sorting fails after producing partial output, the final `xargs` process can still exit zero; the partial temporary manifest is moved into place, and `sha256sum --check` verifies only the files that were listed. It does not prove that every model file was listed. The same failure mode is more serious at the airlock: §10.2/A.8 use `find | grep` to reject special files and `find | sort` to construct `FILELIST.NUL`; A.9 repeats those traversals. A traversal error can therefore be mistaken for “nothing unsafe found”, or the producer and verifier can compare incomplete views. This defeats the file-set completeness property the airlock is intended to establish.
2. **The container archive pipeline has the same masking problem.** A.3 uses `docker save | zstd`. A failing `docker save` can be masked by a successful compressor, leaving an empty or truncated compressed stream that is then checksummed. A checksum proves repeatability of those bad bytes, not that they contain a loadable image.
3. **The smoke tests can appear to pass when the request failed.** A.5 pipes each `curl` response to `tee`; without `pipefail`, the observed status is normally `tee`'s. The calls also have no deterministic timeout, and the prose “Pass” conditions are not implemented as assertions: neither JSON parsing nor the expected model/text/visual result is checked by the command. A log file can therefore exist after a failed, hung or semantically wrong smoke test.
4. **The airlock's sort order is locale-dependent.** §10.2/A.8 and A.9 byte-compare NUL-delimited file lists, so a locale difference between connected and reimaged builds can falsely quarantine a clean bundle. Use `LC_ALL=C` consistently at creation and verification.
5. **The Qdrant network command is not portable to the current frozen candidate without correction.** A.6 combines a container attached only to a bridge created with `--internal` and a loopback-published port. Current Docker/Moby versions can accept that request yet omit the port mapping. Select and test one explicit pattern: a non-internal bridge plus loopback publishing and host-enforced no-egress, or a fully internal network with the retrieval client attached to it and no published port.
6. **Empty input has surprising `xargs` behaviour.** `xargs -0 sha256sum` without `-r` invokes `sha256sum` once on empty input and emits a bogus stdin-hash line. Empty model/transition file sets should instead be an explicit hard failure.

The original review also called the absence of a fifth “Interactive QA” co-residency profile a defect. That was too strong. §6.10 already permits co-residency when measurements prove it stable, and §6.14 can persist an evidence pack between retrieval and answer profiles. An optional named co-resident profile would improve operational clarity and latency if it passes the measured-stability rule, but it is not required for correctness.

**Proposed correction.** Before executing these commands, replace pipelines with explicitly checked stages and temporary files; treat any traversal diagnostic or non-zero status as quarantine; reject empty inventories; use a fixed locale; test compressed archives (`zstd -t`) and prove they load offline; give `curl` bounded connect/total timeouts and validate responses with deterministic `jq -e` assertions. `set -Eeuo pipefail` is useful defence in depth but does not replace stage-specific checks, particularly around early-exit `find | grep -q` patterns. Keep the current instruction to re-verify vLLM flags against the frozen image.

---

## 4. Moderate findings

### F5 — A low residual-risk bound requires near-full audit at the illustrative PoC scale

The sampling design is statistically correct, but the original finding overstated what follows from the illustrative production envelope. §8.3 labels 60 accepted bundles an **example, not a default**, and §6.7 makes 20% an initial sampling floor, not a cap. If all 60 bundles provisionally pass and 12 are randomly audited with zero misses, the exact one-sided 95% upper bound is about 22.1%; the rule-of-three approximation is 25%. If only the 80% provisional-pass target is met, 20% sampling is roughly 10 bundles, giving an exact bound near 25.9% (approximately 30% by `3/n`). Reaching the illustrative 5% bound still needs about 59 independent zero-miss audits—possible with 60 bundles, but effectively near-full review. A 1% bound needs about 299 and is outside that example envelope.

It is therefore inaccurate to say the PoC *cannot* obtain a 5% bound or *must* be descriptive: it can choose a much higher audit fraction. The practical point remains valid. Under the initial 20% floor and constrained human budget, a low residual-risk claim is unavailable. The guide already says in §12.5 and G.2 to report descriptive feasibility when evidence is insufficient, so this is an expectation-placement improvement rather than a missing statistical safeguard. State at activation whether the budget supports the pre-registered bound, near-full audit, or a descriptive conclusion. The same expectation-setting applies to archetype claims: if resources cover only one controlled family, §11.10 already limits the headline claim to that family.

### F7 — Weeks 7–9 double-booking

The PoC Plan's Gate 3 selects *at most one* specialist FA vertical for weeks 7–9, with deferral as the default. The guide's §13.1 places the "small Airbus family study" in the same window, on the same team, gated by the same Gate 3. Both activities are aspirational-tier under the PoC Plan §2.4 shedding order. Neither document says what happens if Gate 3 nominally green-lights both. Add one sentence to §13.1 (and ideally to the PoC Plan Gate 3 row): in the committed ten-week envelope, at most one of {specialist vertical, Airbus-informed family study} begins, and the choice is made at Gate 3 against the same data-readiness and capacity criteria.

---

## 5. Minor findings (F8)

The repository now contains the documentation and the validation utility, but it still lacks standalone, versioned contract artefacts. The guide requires hashed prompt and schema files ("Store the final text as a versioned file and hash it", F.2; "Install complete schema files in the controller", F.12/B.7), yet the schemas and prompt texts exist only inside the guide. Scaffolding `contracts/` (Appendix B schemas), `prompts/` (Appendix F texts) and `policies/` after the F4 fixes would turn those contracts into a usable source of truth and make the `prompt_sha256`/`schema_sha256` fields computable. This is implementation readiness work, not evidence that the guide's strategy is unsound.

The PoC Plan §2.3 "In scope" is an empty heading immediately followed by §2.4 (verified in the document XML); delete it or fold §2.4's content under it. The HTML filename ("…Document Archetype and Synthetic Evaluation Corpus Qualification Guide…") and the document title ("A Practical Guide to Document Understanding and Synthetic Evaluation for P42-KB") differ; harmonising them would help configuration management. The original review incorrectly said the guide lacked status/version/date metadata: the HTML hero already records version 1.0, research date and status. It also overstated the naming gap: D.1 already defines P42-KB as the wider project, although one explicit alias to the Word documents' name "KB Project" would remove residual ambiguity.

The Concepts document uses "SDP" (§23.2 chain table), which no glossary in any document defines. Its §29.3 planning envelope calls for comparing a ~30B-class against a ~70B-class generator "only if residency and latency permit"; the guide does not carry that arm forward. The omission is defensible under the single-Spark latency envelope, but the measured decision or explicit ADR should be recorded rather than left implicit. A short traceability table mapping guide chapters to KB-HLR-033…036, -059…062, -065, OBJ-09 and PoC deliverables D3/D9/D10 would also help; §8.2 asks each activation record to name its HLR, and the guide should expose the governing mapping.

One F8 item is more than editorial and should be resolved alongside F4. B.8 says an output class "cannot be lower than any input", but no total order or transformation matrix is defined. `UNKNOWN` is a quarantine state rather than an ordinary rank, and an artefact derived from `AIRBUS_CONTROLLED` material will normally be `AIRBUS_DERIVED`, so a simple maximum-over-enum rule is inadequate. Define explicit propagation rules and policy tests for each permitted input/output combination.

Small editorial items remain: PoC Plan §10 says "0-1 FTE depending availability" (missing "on"); the Definition's revision history starts at 0.2 with no 0.1; B.2's `page: 14` ICD table coexists with F.3/F.12's page-7 "Signal/Pin/Range" table—two different tables, but a one-line note would prevent readers treating it as an inconsistency.

---

## 6. Will it achieve its objectives?

Measured against the decision it must support (§1.2: adopt / redirect / defer / stop with evidence), the guide is well constructed: outcomes are pre-enumerated, stop rules are concrete and aimed at the right failure modes (timebox erosion, circularity, leakage, review-budget exhaustion), the decision matrix in §12.7 is actionable, and "defer" is genuinely respectable — which is what protects the committed PoC. Measured against the governing documents, it is faithful: real-first sequencing, PoC Plan authority over case volumes, no fine-tuning, no autonomous-diagnosis claims, and the evaluation slices cover the Definition's §21 metrics.

The realistic strategic failure mode is not methodological error but schedule consumption: the controller (F2), the airlock (F1) and the calibration machinery are each individually justified, and collectively heavy for ~2 FTE in ten weeks. The immediate operational risk is F6: integrity controls cannot be trusted while an upstream command failure can be masked. The corrections proposed here make the plan *governable at that scale*: shrink connected Phase A to acquisition, tier the controller, force the Gate 3 either/or, decide the attainable statistical claim up-front, and make every freeze/import stage fail closed. With F1–F4 and F6 resolved, this reviewer's assessment is that the work package has a credible path to its stated decision, and—equally important—a dignified exit at every gate if the evidence says stop.

---

## Annex A — Machine-validation evidence

Validation performed with `jsonschema` 4.26 (Draft 2020-12) on JSON/YAML extracted verbatim from the HTML `<pre>` blocks. The B.7 and B.8 schemas are themselves valid 2020-12 schemas (a point in the guide's favour).

**§6.8 job-envelope example vs B.8 `job-envelope/1.0` — 9 substantive errors (placeholder-pattern errors excluded):**

```text
(root)            : 'approved_provider_surface_feature' is a required property
(root)            : 'provider_retention_profile_id' is a required property
(root)            : 'task_type' is a required property
(root)            : 'config_id' is a required property
(root)            : Additional properties are not allowed
                    ('evidence_required', 'required_output' were unexpected)
allowed_inputs/0  : Additional properties are not allowed ('evidence_pack_sha256' was unexpected)
allowed_inputs/0  : 'sha256' is a required property
allowed_inputs/0  : 'lineage_id' is a required property
limits            : 'max_tool_calls' is a required property
```

**§9.6 answer-envelope example vs B.7 `claim-evidence-response/1.0` — 6 errors:**

```text
answerability : 'ANSWERABLE' is not one of ['fully_answerable', 'partly_answerable',
                'not_answerable', 'conflicting_authority']
claims/0      : 'claim_id' is a required property
claims/0      : 'state' is a required property
claims/0      : 'contradicting_evidence_ids' is a required property
claims/0      : 'calculation' is a required property
(root)        : Additional properties are not allowed ('confidence' was unexpected)
```

**Examples that validate cleanly** (modulo `[HASH]`-style placeholders): F.3 job envelope vs B.8; B.3 claim/evidence response vs B.7; §11.5 observation vs `observation/1.0`; F.12 producer and reviewer responses vs the B.7 wrapper.

**Other checks:** all 1,278 internal `href="#…"` anchors resolve against 1,494 IDs, zero duplicates; no external script/style/font resources (96 external URLs are citation `<a>` links only); rule-of-three figures (59 → ~5%, 299 → ~1%) exact; `vmstat` column indices in A.10 correct (`$9`=bi, `$10`=bo); occurrence counts confirming vocabulary drift: `MISSING_CRITICAL_EVIDENCE` ×1 (undefined), `external_network` ×1 vs `network` ×1, `write_source_corpus` ×1 vs `write_source_record` ×1, `ICD-009-C:` ×1 vs `ICD-009:C:` ×3, `AMBIGUOUS` ×0 in enums while prose references ambiguity ×5.

**Operational reproduction/cross-check:** the §10.2/A.8 design avoids hashing `SHA256SUMS` into itself, and A.9 correctly authenticates the checksum manifest before checking listed hashes. That does **not** establish file-set completeness when the shell traversal failed. In POSIX shell pipeline semantics, the shown `find | sort | xargs` status is the final command's status unless `pipefail` or explicit stage checks are used; a failed/partial `find` can therefore leave a manifest whose listed entries all pass. The shown `find … | grep -q .` safety check likewise cannot distinguish “no unsafe file found” from an upstream traversal failure. The same masking applies to `docker save | zstd` and `curl | tee`. These are fail-open control-flow defects, not merely logging imperfections, and supersede the original statement that the airlock chain was sound apart from locale.

A minimal reproduction using the same `find | sort | xargs sha256sum` operators against a missing path produced the following result. The failed traversal was masked, `xargs` emitted the SHA-256 of empty stdin as a file named `-`, and `sha256sum --check` then accepted it:

```text
stage_status(find,sort,xargs)=1,0,0
manifest=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  -
sha256sum --check: -: OK
check_status=0
```

## Annex B — Proposed correction summary (one line each)

| # | Target | Correction |
|---|---|---|
| 1 | Guide §13.1 + new figure | Re-scope Phase A to acquisition+smoke (weeks 1–2); airlock end of week 2; bake-offs run offline in Phase B on public fixtures; cloud research off-Spark throughout |
| 2 | Guide §6.8/§9.1/§11 | Tier the controller: security-mandatory (airlock precondition) vs workflow machinery (synthetic-study batch production only); core benchmark runs under B.1 manifest discipline |
| 3 | Guide §13.1 Gate 3 row | "Authorise a bounded Phase B pilot whose Step B0 is the necessity test; continue past B0 only on recorded margin" |
| 4 | Guide §6.8 example | Regenerate to satisfy B.8 (add `task_type`, `config_id`, provider/retention fields, `max_tool_calls`, input `sha256`+`lineage_id`; drop `required_output`, `evidence_required`, `evidence_pack_sha256`) |
| 5 | Guide §9.6 example | Regenerate to satisfy B.7 (enum value, `claim_id`, `state`, `contradicting_evidence_ids`, `calculation`; drop `confidence`) |
| 6 | Guide B.9 + both envelope examples | Single registry for forbidden actions and escalation rules; replace `MISSING_CRITICAL_EVIDENCE` with `CRITICAL_CONTENT_UNREADABLE` |
| 7 | Guide B.2 + §9.6 | Define the `evidence_id` grammar once; conform all examples (`ICD-009:C:…`) |
| 8 | Guide B.7/F.9 + Concepts §8.1 | Resolve answerability vocabulary (add ambiguous state or record explicit mapping) in both documents |
| 9 | Guide §6.7/§12.5/§13 | At activation, choose and record one of: enough independent audits for the bound, near-full audit, or descriptive feasibility. At 12 zero-miss audits the exact 95% upper bound is ≈22.1% (`3/n` ≈25%); ≈59 are needed for 5% |
| 10 | Guide A.2/§10.2/A.8/A.9 | Replace traversal pipelines with explicitly checked temporary stages; any `find` diagnostic/non-zero status quarantines; reject empty/incomplete inventories before signing or accepting them |
| 11 | Guide A.3 | Do not allow `docker save` failure to be masked by `zstd`; verify the archive is non-empty, passes `zstd -t` and loads offline before hashing/acceptance |
| 12 | Guide A.5 | Add bounded connect/total timeouts; do not let `tee` mask `curl`; use deterministic `jq -e` assertions for model identity and expected text/visual results |
| 13 | Guide §10.2/A.2/A.8/A.9 | Use `LC_ALL=C`; use `xargs -r`; make an empty file set a hard failure |
| 14 | Guide A.6 | Remove the current `--internal`+`-p` incompatibility; pick and qualify loopback-bridge+host-no-egress or fully-internal same-network access |
| 15 | Guide §6.10/§6.14 | No mandatory fifth profile: optionally name a co-resident Interactive QA profile only if measured stability/latency evidence justifies it; otherwise persist evidence packs between staged profiles |
| 16 | Guide §13.1 + PoC Plan Gate 3 | At most one of {specialist vertical, family study} starts in weeks 7–9 under baseline capacity |
| 17 | Repo | Scaffold `contracts/`, `prompts/`, `policies/` from Appendices B/F after fixes; keep CI validation (script delivered: `tools/validate_guide_contracts.py`) |
| 18 | PoC Plan §2.3 | Remove empty "In scope" heading (or populate it) |
| 19 | Guide title/filename/glossary | Harmonise title vs filename; retain the existing version/date/status hero; optionally state explicitly that P42-KB is the "KB Project" named by the Word documents |
| 20 | Concepts §23.2/§29.3; glossaries | Define "SDP"; record the omitted conditional ~70B-class comparison as an explicit measured decision/ADR |
| 21 | Guide (new short table) | Trace guide chapters → KB-HLR-033…036/059…062/065, OBJ-09 → deliverables D3/D9/D10 |
| 22 | Guide B.8 policy tests | Define an explicit data-class propagation/transition matrix; treat `UNKNOWN` as quarantine, not an ordinal value |
