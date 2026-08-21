---
title: "A Practical Guide to Document Understanding and Synthetic Evaluation for P42‑KB"
subtitle: "An evidence-led strategy that fits on one NVIDIA DGX Spark"
version: "0.9"
date: "21 August 2026"
status: "Supporting guide — research cut and operator edition"
---

<div class="cover-note">

**What this guide is for.** This guide explains how to test document understanding, retrieval and controlled synthetic engineering documents for P42-KB. It is written for project leads, engineers, subject-matter experts, security reviewers and operators—not only AI specialists.

**What this guide is not.** It is not authority to process Airbus material, not legal advice, and not a claim that one model or public leaderboard is “best.” Every recommendation must be tested on the approved P42-KB cases and the actual DGX Spark.

**Research cut.** The technical review covers primary sources and official documentation available on 21 August 2026. Model releases and software containers change quickly; revisions and image digests must be frozen for each experiment.

</div>

# Start here {#start}

::: {.plain}
**The answer in one minute**

P42-KB should first prove that it can find real engineering evidence, answer with exact citations and connect a bounded chain across documents. Synthetic documents are a **test rig**, not the product. They become useful only when they expose failures that the small real benchmark cannot safely or cheaply create.

On one DGX Spark, the best evidence-supported starting point is a **cascade**:

1. preserve text, layout, tables, page coordinates and revision metadata;
2. search exact identifiers, keywords and meaning in parallel;
3. rerank a short list with a stronger specialist model;
4. follow explicit cross-references or layout links when the question needs them;
5. inspect the original page with a vision model only when visual evidence matters;
6. answer claim by claim, cite the source and say “not established” when evidence is missing.

For controlled synthetic cases, create the fictional engineering truth first, turn it into a structured document plan, and render it deterministically. Never ask one large language model to invent the world, write the documents and grade its own work.
:::

::: {.decision}
**Recommended default, subject to the P42-KB bake-off**

- **Document conversion:** native text extraction plus Docling/pypdfium2 for ordinary pages; selective Tesseract for simple scans; NVIDIA Nemotron Parse 2.0 and PaddleOCR-VL-1.5 as difficult-page challengers.
- **Text retrieval:** exact identifier lookup + SQLite FTS5/BM25 + Qwen3-Embedding-0.6B; Qwen3-Reranker-0.6B over the shortlist. The 4B variants are quality challengers, not the always-on default.
- **Visual retrieval:** Qwen3-VL-Embedding-2B and Qwen3-VL-Reranker-2B only on the visual/hard-page branch.
- **Visual observation and answer/generation:** Qwen3-VL-2B-Instruct for routine page/crop inspection if it meets the quality margin; Qwen3.8-27B-FP8 for harder reasoning and controlled generation, compared with a materially smaller Qwen3.5-9B efficiency control and NVIDIA Nemotron-3-Nano-Omni-30B-A3B.
- **Local stores:** SQLite for authority, identifiers, relations and experiment records; single-node Qdrant for dense, sparse and optional multivector search.
- **Synthetic-data orchestration:** typed Python/Pydantic validators, with NVIDIA NeMo Data Designer as an optional batch/orchestration layer—not as the source of truth.
- **Rendering:** a validated document abstract syntax tree (AST) rendered through pinned HTML/CSS + Chromium, with a materially independent Typst or second-template arm for blind tests.
:::

## Choose your route through the guide

| If you are… | Read first | Then use |
|---|---|---|
| Sponsor or PoC lead | Chapters 1, 2 and 6 | Chapters 12 and 13 for gates and decisions |
| Engineer or subject-matter expert | Chapters 3 and 4 | Chapters 10 and 11 for truth, review and scoring |
| AI/KB technical lead | Chapters 4–6 | Chapters 8–11 and the command appendix |
| Benchmark operator | Chapters 7–9 | Appendices A–C |
| Security or data-rights reviewer | Chapters 1 and 7 | Chapter 9 and Appendix C |
| New to RAG and document AI | Chapters 2 and 3 | Follow the T17 example boxes throughout |

# Part I — Understand the job before choosing tools {#understand}

# 1. What P42-KB is actually trying to prove {#purpose}

::: {.plain}
**In simple words:** P42-KB is meant to help an engineer find and understand project evidence. It must behave more like a careful colleague working with an open file than a chatbot answering from memory.
:::

The governing P42-KB documents define a progressive proof:

- **Find:** locate the right document, identifier or evidence passage.
- **Answer:** give a concise answer with exact provenance and an honest “not found” response.
- **Connect:** combine a bounded chain of evidence across documents, revisions or lifecycle stages.

The committed proof-of-concept (PoC) is real-project-first. It starts with corpus characterisation, exact/search baselines and reviewed real questions. A mature synthetic-project generator is conditional and can be deferred without failing the core PoC. This guide therefore sits under the benchmark and evaluation workstream; it does not replace the [Project Definition](https://github.com/SilasMoon/p42-KB/blob/2b06a975599e10c0267793944443a98d1da157dd/docs/KB_Project_Project_Definition_and_High_Level_Requirements_v1.0.docx), [PoC Implementation Plan](https://github.com/SilasMoon/p42-KB/blob/2b06a975599e10c0267793944443a98d1da157dd/docs/KB_Project_PoC_Implementation_Plan_v0.9.docx) or [Candidate Technical Concepts](https://github.com/SilasMoon/p42-KB/blob/2b06a975599e10c0267793944443a98d1da157dd/docs/KB_Project_Candidate_Technical_Concepts_and_Design_Considerations_v1.0.docx).

::: {.analogy}
**Analogy — open-book engineering assistant.** Imagine asking a careful colleague why sensor T17 is connected to channel ADC12. A useful colleague opens the wiring document, checks the revision, follows the interface reference and shows the exact lines used. An unsafe colleague gives a plausible answer from memory. P42-KB must be the first colleague.
:::

## 1.1 The role of synthetic documents

Synthetic documents have three legitimate roles:

1. create exact known truth for regression tests;
2. create rare, conflicting or missing-evidence cases on purpose;
3. measure whether a system improvement transfers to a protected real benchmark.

They must not silently become substitute evidence that makes the system look better than it is.

::: {.analogy}
**Analogy — wind tunnel, not aircraft.** A wind tunnel can create a precise cross-wind repeatedly. That makes it excellent for diagnosing a design. Passing a wind-tunnel test does not prove the aircraft is ready to fly. In the same way, synthetic cases diagnose P42-KB; real engineer cases decide whether it is useful.
:::

## 1.2 The decision this work package must support

The decision is not “Can Qwen produce a convincing fake PDF?” It is:

> Does a controlled document-archetype and synthetic-evaluation capability add enough reliable diagnostic value to P42-KB to justify its compute, engineering effort, subject-matter review and governance cost on one DGX Spark?

Valid outcomes are:

- **Adopt a bounded capability** because it improves diagnosis without harming real cases.
- **Redirect** to a smaller capability, such as exact-truth question generation without realistic document reconstruction.
- **Defer** because the real benchmark, parser or retrieval baseline needs work first.
- **Stop** because the synthetic result is unsafe, circular, too expensive or unrelated to the project objective.

Deferral is not failure. It can be the correct engineering decision.

# 2. The whole strategy in one picture {#strategy-picture}

::: {.plain}
**In simple words:** turn each real document into a trustworthy map, search that map in several complementary ways, inspect the original only when needed, and keep every answer tied to its evidence.
:::

<div class="flow" role="img" aria-label="The recommended P42-KB document pipeline">
  <div class="flow-stage"><span>1</span><strong>Original evidence</strong><small>PDF, Office file, table, image</small></div>
  <div class="flow-arrow">→</div>
  <div class="flow-stage"><span>2</span><strong>Structured document map</strong><small>text, layout, tables, coordinates</small></div>
  <div class="flow-arrow">→</div>
  <div class="flow-stage"><span>3</span><strong>Three-way search</strong><small>exact + lexical + semantic</small></div>
  <div class="flow-arrow">→</div>
  <div class="flow-stage"><span>4</span><strong>Shortlist and expand</strong><small>rerank + references + visual branch</small></div>
  <div class="flow-arrow">→</div>
  <div class="flow-stage"><span>5</span><strong>Evidence pack</strong><small>authority, revision, page and crop</small></div>
  <div class="flow-arrow">→</div>
  <div class="flow-stage"><span>6</span><strong>Cited answer</strong><small>supported, uncertain or not established</small></div>
</div>

The synthetic path joins the same pipeline at the left:

<div class="flow secondary" role="img" aria-label="The controlled synthetic-document pipeline">
  <div class="flow-stage"><span>A</span><strong>Fictional truth graph</strong><small>components, IDs, values and relations</small></div>
  <div class="flow-arrow">→</div>
  <div class="flow-stage"><span>B</span><strong>Document AST</strong><small>sections, tables, references and defects</small></div>
  <div class="flow-arrow">→</div>
  <div class="flow-stage"><span>C</span><strong>Deterministic renderer</strong><small>HTML/PDF with fixed seed and template</small></div>
  <div class="flow-arrow">→</div>
  <div class="flow-stage"><span>D</span><strong>Normal P42-KB ingestion</strong><small>the system does not receive hidden truth</small></div>
</div>

## 2.1 Why this is a cascade

Different tools are good at different jobs. A text layer can copy an identifier exactly. A layout parser can keep a table cell attached to its heading. An embedding model can find similar meaning. A vision-language model can inspect a diagram. A large reasoning model can combine the selected evidence.

Using the largest model for every page is like asking a chief engineer to photocopy, label and file every sheet before answering one question. It may work, but it wastes scarce attention and makes errors harder to locate.

## 2.2 Where the graph belongs

The first useful graph is modest and explicit:

- document A **supersedes** document B;
- requirement R-17 **is verified by** test T-42;
- section 4.2 **references** ICD-009;
- table row **belongs to** this heading and this page;
- signal T17 **maps to** connector J12 pin 4.

This is closer to a wiring diagram than a general-purpose “knowledge graph.” The PoC should add relations that have a named use case and can be checked. It should not begin by asking an LLM to invent a huge graph of every noun in the corpus.

::: {.analogy}
**Analogy — a sat-nav with roads, not a word cloud.** Multi-document reasoning needs known paths: “this requirement points to this test,” or “this revision replaces that one.” A graph is useful when its edges are real roads. A cloud of automatically associated terms may look rich but cannot safely guide an engineering conclusion.
:::

# 3. Key ideas in ordinary language {#concepts}

Each concept below follows the same pattern: what it means, an analogy and the T17 example. The full alphabetical glossary is in Appendix D.

## 3.1 Retrieval-augmented generation (RAG)

**Meaning.** Retrieval-augmented generation first finds relevant evidence and then gives that evidence to a language model to answer. The model is not expected to remember the project.

**Analogy.** An open-book examination: finding the correct page is separate from writing the answer.

**T17 example.** The search finds the interface-control table and test report; the answer model explains the mapping and cites both.

## 3.2 Parsing and optical character recognition (OCR)

**Meaning.** A parser turns a document into structured information. Optical character recognition reads text that exists only as pixels in a scan or image.

**Analogy.** Unpacking a shipment while keeping each part attached to its label. A poor parser dumps every part and label into one box.

**T17 example.** “ADC12” must stay in the same table row as “T17,” not move to the next row during extraction.

## 3.3 A document abstract syntax tree (AST)

**Meaning.** A document AST is a machine-readable plan of the document: chapters contain sections; sections contain paragraphs, tables and figures; references point to other objects.

**Analogy.** A building blueprint. It says where rooms and doors belong without specifying the colour of the paint.

**T17 example.** The AST records that the signal table is in section 4.2, has columns for signal, connector and acquisition channel, and contains the T17 row.

## 3.4 Chunking

**Meaning.** Chunking creates retrieval units from a document. Good chunks preserve meaningful boundaries and retain their parent heading, page and source.

**Analogy.** Filing a manual into labelled folders, not shredding it into equal-width strips.

**T17 example.** The entire signal-table row and its heading form one retrieval unit; it is not cut halfway because a token limit was reached.

Before indexing that unit, prepend deterministic context such as document ID, title, revision, authority, applicability and section path. This is like putting a complete label on a parts bin. Test model-written contextual summaries only later: a fluent but wrong label can make a good evidence block difficult to find.

## 3.5 Exact, lexical and semantic search

**Exact search** matches an identifier precisely. **Lexical search** rewards shared words. **Semantic search** uses an embedding—a list of numbers representing meaning—to find paraphrases.

**Analogy.** A stores assistant can search by part number, by words in the description, or by what the part does. Keeping all three avoids obvious misses.

**T17 example.** Exact search catches `T17` and `ADC12`; lexical search catches “thermistor acquisition channel”; semantic search catches “temperature sensor readout path.”

## 3.6 Reranking

**Meaning.** A fast search makes a generous shortlist. A reranker reads each query–candidate pair more carefully and puts the strongest evidence first.

**Analogy.** A librarian collects twenty possible files; a senior engineer orders them by actual relevance.

**T17 example.** A generic ADC manual may match the words, but the project-specific ICD row must rank above it.

## 3.7 Vision-language model (VLM)

**Meaning.** A vision-language model can reason over images and text. It is useful for diagrams, complex layouts, handwriting and charts that lose meaning in plain text.

**Analogy.** When a transcript is unclear, ask the inspector to look at the original drawing rather than guessing from the transcript.

**T17 example.** The VLM inspects the wiring-diagram crop only after retrieval identifies the likely page.

## 3.8 Provenance, authority and lineage

**Provenance** records where evidence came from. **Authority** records whether it is approved, obsolete, draft or simulated. **Lineage** records how a derived item was produced.

**Analogy.** A chain-of-custody label: source, revision, handler and transformation travel with the item.

**T17 example.** The answer distinguishes the current ICD, the superseded mapping and the AI-created summary.

## 3.9 Abstention and answerability

**Meaning.** The system must distinguish “the evidence supports this” from “the corpus does not establish this,” “sources conflict,” and “the question is ambiguous.”

**Analogy.** A calibrated instrument displays “out of range” rather than inventing a measurement.

**T17 example.** If no as-run configuration is available, the system says that the intended mapping is ADC12 but the actual test configuration is not established.

## 3.10 Archetype, empirical pattern and normative rule

An **archetype** is a reusable description of a document family. An **empirical pattern** says what was observed. A **normative rule** says what an approved generated document must contain. They are not the same.

**Analogy.** A survey may find that 80% of houses have two exits. A building code decides how many exits are required. Frequency does not create the rule.

**T17 example.** If 8 of 10 interface documents contain a signal table, that is prevalence. A subject-matter expert—not the model—decides whether every generated ICD must contain one and under which conditions.

## 3.11 Truth graph, scenario policy and renderer

The **truth graph** contains the fictional programme facts. The **scenario policy** selects which facts, defects and missing items appear in a test. The **renderer** turns a validated document AST into files.

**Analogy.** The truth graph is the master wiring diagram, the scenario policy is the test plan, and the renderer is controlled manufacturing.

## 3.12 Development, calibration and blind sets

- **Development set:** visible and used to improve the system.
- **Calibration set:** used to choose thresholds and check judges.
- **Blind set:** sealed until the design is frozen.
- **Regression set:** any previously opened set used to make sure old failures do not return.

**Analogy.** Homework, practice examination, sealed final examination and the archive of past examination questions.

Once a blind set has been opened, it can never become blind again.

# 4. Running example — the T17 thermistor investigation {#t17}

::: {.plain}
**Why use one example throughout?** Abstract descriptions are easy to misunderstand. T17 gives every step the same small engineering story.
:::

## 4.1 The hidden fictional truth

The controlled truth says:

- thermistor `T17` connects to `J12` pin 4;
- that pin should map to acquisition channel `ADC12`;
- the current software configuration mistakenly maps it to `ADC13`;
- a previous revision used `ADC12`;
- a continuity test confirms that the physical wiring is correct;
- the thermal test shows an implausible temperature only when the wrong configuration is loaded.

## 4.2 The document bundle

The synthetic project does not place all facts in one convenient report. It creates a realistic evidence chain:

| Document | What it contains | Deliberate difficulty |
|---|---|---|
| Harness drawing | T17 → J12 pin 4 | visual connection and sheet reference |
| Interface-control document | J12 pin 4 → ADC12 | dense table with similar signal names |
| Continuity report | wiring passes | evidence that rules out a harness fault |
| Telemetry dictionary | channel meaning and units | identifier and unit matching |
| Current configuration | T17 → ADC13 | the planted defect |
| Previous configuration | T17 → ADC12 | revision and authority trap |
| Thermal test report | implausible reading under current load | cross-document symptom |

## 4.3 Questions at the three P42-KB levels

- **Find:** “Which document defines the acquisition channel for T17?”
- **Answer:** “What channel should T17 use, and what is the supporting source?”
- **Connect:** “Why is the displayed temperature implausible even though continuity passed?”

The Connect answer must retrieve all necessary evidence, respect revision status and separate observation from hypothesis. It should not claim that software is the root cause merely because the story was designed that way; it should explain which evidence establishes the mapping mismatch.

## 4.4 What a good answer looks like

::: {.example}
**Supported conclusion.** The approved interface mapping assigns T17 to ADC12 through J12 pin 4. The current configuration assigns T17 to ADC13, while the continuity report shows that the physical path passed. This makes the configuration mismatch the leading supported explanation for the displayed value.

**Evidence.** ICD-009 rev C §4.2 row T17; CFG-021 rev F row T17; CTR-018 test step 7.

**Limit.** The corpus does not include an as-run software-load record, so it does not establish which configuration was active for every test run.
:::

This small answer demonstrates the target behaviour: conclusion, evidence and limitation are separate.

# Part II — What the 2026 state of the art changes {#research}

# 5. Research findings and design consequences {#research-findings}

::: {.plain}
**In simple words:** recent work does not support replacing the whole document pipeline with screenshots and one giant vision model. The strongest direction is to preserve structure, combine complementary retrieval paths and spend expensive visual reasoning only on the small number of places that need it.
:::

This chapter separates published evidence from the engineering inference made for P42-KB. A benchmark result is evidence about that benchmark—not proof about Airbus documents.

## 5.1 Preserve structure; do not turn everything into pixels

The ICLR 2025 [ColPali](https://openreview.net/forum?id=ogjBpZ8uSi) work showed that page-image embeddings can beat brittle OCR-only pipelines on visually rich retrieval. That was an important result: layout and figures matter.

More recent evidence adds an equally important qualification. [Document-as-Image Representations Fall Short for Scientific Retrieval](https://arxiv.org/abs/2604.18508) reports that, for long text-rich scientific documents, page screenshots were consistently weaker than structured text and interleaved text–image representations; text plus visual captions performed strongly even for figure questions. The practical conclusion is not “text wins” or “vision wins.” It is: **do not discard either the source structure or the original visual evidence.**

::: {.research-card}
**Evidence.** Controlled comparisons on scientific documents favour structured text and interleaved representations over screenshot-only indexing as documents become longer.

**P42-KB inference.** Use structured text/layout as the default representation. Retain page images and crops so visual retrieval and the answer model can inspect them when a query depends on a diagram, chart, handwriting or spatial relation.
:::

## 5.2 Preserve layout and cross-page relationships

The ACL 2026 [LAD-RAG](https://aclanthology.org/2026.acl-long.724/) paper reports that isolated chunks and fixed top-*k* retrieval miss cross-page dependencies. It adds a symbolic document graph beside neural embeddings and allows retrieval depth to adapt to the question. The EACL 2026 [SCAN](https://aclanthology.org/2026.findings-eacl.82/) work similarly reports gains from semantically coherent document regions rather than arbitrary page fragments.

::: {.analogy}
**Analogy — keep the table of contents and the cross-reference arrows.** Cutting a manual into paragraphs but deleting headings and “see drawing 4” links is like copying street names while erasing the road junctions.
:::

::: {.research-card}
**Evidence.** Layout-aware regions and explicit cross-page relationships improve retrieval and question answering on visually rich document benchmarks.

**P42-KB inference.** Store parent section, reading order, page, bounding box, caption/table ownership and explicit references with every retrieval unit. Allow a bounded second retrieval step when the first evidence points to another document or section.
:::

## 5.3 Use a fast first pass and a careful second pass

Search over an entire corpus needs a fast, broad candidate stage. Careful query–document comparison is too expensive to apply everywhere. The ACL 2026 [HEAVEN](https://aclanthology.org/2026.findings-acl.54/) work demonstrates this two-stage principle for visual documents, retaining nearly all of a multivector retriever's reported Recall@1 while greatly reducing query computation. Qdrant's official [hybrid-search](https://qdrant.tech/documentation/tutorials-basics/reranking-hybrid-search/) and [multivector](https://qdrant.tech/documentation/tutorials-search-engineering/using-multivector-representations/) guidance implements the same broad-then-precise pattern.

::: {.research-card}
**Evidence.** Dense, sparse and late-interaction signals are complementary; expensive interaction is most efficient over a shortlist.

**P42-KB inference.** Retrieve generously with exact, lexical and dense paths; combine ranks with reciprocal rank fusion (RRF); rerank roughly 20–50 candidates; then build the smallest complete evidence pack. Tune the numbers on the real benchmark rather than copying them from a paper.
:::

## 5.4 Specialised retrieval models are better tools than a chat model for search

The [Qwen3 Embedding](https://arxiv.org/abs/2506.05176) family provides dedicated multilingual text embedding and reranking models in 0.6B, 4B and 8B sizes with 32K input length. The newer [Qwen3-VL Embedding and Reranker](https://arxiv.org/abs/2601.04720) family provides 2B and 8B models for text, images, screenshots and mixed inputs. These models perform the search/ranking job directly; a 27B chat model is not required to embed every chunk.

::: {.analogy}
**Analogy — use the barcode scanner to find the box.** The chief engineer can read a label, but a barcode scanner is faster, repeatable and made for locating inventory. Save the chief engineer for deciding what the evidence means.
:::

::: {.research-card}
**Evidence.** The model families are purpose-trained for retrieval and ranking, support multilingual inputs and provide smaller deployment choices.

**P42-KB inference.** Use Qwen3-Embedding-0.6B and Qwen3-Reranker-0.6B as the single-Spark operational baseline; compare their 4B variants as quality challengers. Add Qwen3-VL-Embedding/Reranker-2B only for a visual slice. Do not select the 8B versions unless the measured gain justifies extra memory and latency.
:::

## 5.5 Small document parsers now deserve a first-class bake-off

[Docling](https://docling.org/) provides local conversion of PDF, Office and image formats into a structured `DoclingDocument`, including layout, reading order, tables, bounding boxes and structure-aware chunking. It runs on ARM64 and offers several OCR backends.

NVIDIA's August 2026 [Nemotron Parse 2.0](https://huggingface.co/nvidia/NVIDIA-Nemotron-Parse-2.0) is a sub-1B document parser that emits text, element classes, bounding boxes and reading order, with explicit chart/table and multilingual improvements. It supports Blackwell and vLLM. [PaddleOCR-VL-1.5](https://arxiv.org/abs/2601.21957) is another compact 0.9B challenger reporting strong OmniDocBench results. [OmniDocBench](https://github.com/opendatalab/OmniDocBench) itself now covers 1,651 pages and multiple layout, language and document types.

::: {.research-card}
**Evidence.** Compact, task-specific document parsers can recover layout and structured elements without spending a 27B model on every page.

**P42-KB inference.** Keep native PDF text whenever trustworthy; use Docling as the conversion/control framework; compare Nemotron Parse 2.0 and PaddleOCR-VL-1.5 on the actual difficult-page slice. Measure tables, reading order, identifier integrity and downstream evidence recall—not only character accuracy.
:::

## 5.6 Dynamic and graph-assisted retrieval should be bounded

Microsoft [GraphRAG](https://microsoft.github.io/graphrag/) is designed for entity and whole-corpus thematic questions using an LLM-extracted graph and community summaries. It can be useful, but its global search solves a different problem from locating the approved mapping for T17. P42-KB already has valuable, checkable relations: revisions, supersession, requirements, tests, documents and references.

::: {.research-card}
**Evidence.** Graph approaches help when questions truly depend on relationships or corpus-wide aggregation. LAD-RAG also shows value from a document-layout graph.

**P42-KB inference.** Build the small explicit graph first. Measure bounded reference expansion against the best hybrid baseline. Adopt automatic entity-graph construction only for a named use case that wins that comparison. This avoids consuming Spark time and review effort on speculative edges.
:::

## 5.7 Synthetic generation is a system, not a prompt

NVIDIA's [NeMo Data Designer](https://docs.nvidia.com/nemo/datadesigner/getting-started/welcome) treats synthetic-data generation as a pipeline of dependent fields, statistical variation, validation and batch execution. Its documented [long-document workflow](https://docs.nvidia.com/nemo/datadesigner/dev-notes/vlm-long-document-understanding) uses separate OCR, page classification, single-page, multi-page and whole-document streams, followed by independent filtering. [SynthDocBench](https://github.com/ServiceNow/SynthDocBench) similarly keeps structured chart metadata behind rendered reports so answers can be derived deterministically.

::: {.research-card}
**Evidence.** Modern synthetic-data systems separate generation roles, keep structured control data and validate outputs in stages.

**P42-KB inference.** Retain the v0.8 truth-graph → document-AST → deterministic-renderer strategy. Add a typed orchestration layer, explicit validators, independent blind authoring and varied renderers. NeMo Data Designer is a useful controller for batch columns and validation, but it must never replace the approved truth model or normative policy.
:::

## 5.8 Evaluation frameworks are diagnostic aids, not acceptance authorities

[RAGChecker](https://github.com/amazon-science/RAGChecker) separates retrieval and generation failure modes. [Ragas](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/) includes context recall, context precision, faithfulness, multimodal metrics and answer measures. These are useful, but several depend on a language-model judge. A judge can share biases with the system under test and may not understand engineering authority or configuration.

::: {.research-card}
**Evidence.** Fine-grained component metrics diagnose more than one end-to-end score; automated evaluators still require calibration.

**P42-KB inference.** Make deterministic retrieval and provenance measures primary whenever gold evidence exists. Calibrate every local judge against blinded engineer ratings. Use Ragas/RAGChecker as secondary diagnostics; never allow an uncalibrated judge to release a corpus or pass an engineering claim.
:::

## 5.9 The overall research verdict

| Question | Verdict for P42-KB | Confidence |
|---|---|---|
| Should all pages be processed directly by Qwen3.8? | No. Retain as a diagnostic/control arm; use a structured cascade as the production hypothesis. | High |
| Should visual information be ignored? | No. Preserve originals and use visual retrieval/reasoning selectively. | High |
| Is the truth graph + AST + deterministic renderer direction sound? | Yes, with independent blind generation, typed validation and multiple renderer styles. | High |
| Is a full automatically extracted GraphRAG required at PoC start? | No. Start with exact relations and bounded reference following. | Medium–high |
| Is Qwen3.8-27B automatically the best model? | No. It is a strong multilingual native-VLM candidate; a paired real-case bake-off must decide. | High |
| Should all six legacy public benchmarks be run in full? | No. Run diagnostics only when a real uncertainty maps to them. | High |
| Can synthetic scores decide PoC success? | No. Protected real cases and engineer evidence remain authoritative. | High |
| Does one Spark have enough model capacity? | Yes for these model sizes when staged; capacity does not guarantee acceptable speed or concurrency. | Medium–high |

# 6. The recommended architecture for one DGX Spark {#recommended-architecture}

::: {.plain}
**In simple words:** the Spark has enough memory to load capable models, but it does not have unlimited memory bandwidth or a team of GPUs. Run specialised stages deliberately instead of leaving every model loaded at once.
:::

## 6.1 What the hardware constraint means

NVIDIA documents the DGX Spark as an ARM64 Grace Blackwell GB10 system with **128 GB of coherent unified memory** and **273 GB/s memory bandwidth**. NVIDIA advertises up to one petaFLOP of FP4 AI compute, but the precision and workload conditions matter. The [hardware specification](https://docs.nvidia.com/dgx/dgx-spark/hardware.html) and [Spark vLLM playbook](https://build.nvidia.com/playbooks/vllm) should be treated as the platform sources of truth.

Unified memory is one shared reservoir for the operating system, model weights, key/value cache, parsers and databases. A model that “fits” can still be too slow, leave too little working memory or fail when several services compete.

NVIDIA's [known-issues guidance](https://docs.nvidia.com/dgx/dgx-spark/known-issues.html) also explains that `nvidia-smi` cannot report ordinary dedicated-framebuffer use on this integrated GPU and that CUDA memory figures can differ from what the operating system can reclaim. Monitor `/proc/meminfo`, swap movement, process resident memory, page faults, disk I/O and temperature together. Treat any swap-in/swap-out during a timed capacity run as a failed profile, not as extra GPU capacity.

::: {.analogy}
**Analogy — a large workshop with one loading bay.** The Spark can hold large machinery, but only one heavy delivery can move efficiently through the bay at a time. Capacity and throughput are different questions.
:::

## 6.2 Operating rule: stage the heavy models

Use four operating profiles rather than one permanently overloaded server:

| Profile | Heavy service loaded | Typical job |
|---|---|---|
| Parse | Docling/native extraction; one specialist parser only when routed | batch pages and cache lossless structured output |
| Index | text or multimodal embedding model | build/rebuild frozen indexes |
| Retrieve | Qdrant + small embedding/reranker service | interactive search and retrieval evaluation |
| Answer/generate | Qwen3.8 or challenger VLM | cited answers, archetype observations or bounded prose generation |

Stop and unload one heavy profile before starting another unless measurements prove co-residency is stable. Keep model files on local NVMe so switching does not require internet access.

## 6.3 Provisional memory envelope

This is a planning envelope, not a specification. The operator must measure resident memory, cache growth and long-context behaviour on the actual build.

| Use | Provisional allowance | Why |
|---|---:|---|
| DGX OS, containers, filesystem cache and monitoring | 24–32 GB | conservative starting reserve; unified memory is shared with the host |
| Qdrant/SQLite and working data | 8–16 GB | depends on corpus and whether vectors are on disk |
| 27B FP8-class model weights and vision components | approximately 30–40 GB | estimate; confirm from loaded resident memory |
| Attention cache, page images and temporary tensors | 24–40 GB | grows with context, image count and concurrency |
| Additional safety margin | measured inside the host reserve | prevents nominal fit from becoming an unstable run |

Use **8K–16K for normal evidence packs**, with a hard initial service cap of **32K total context and one active sequence**. Raise the cap or concurrency only when a real case needs it and a measured memory/latency test passes without swap. A model's advertised 262K context is a capability ceiling, not a sensible default evidence budget.

Prefer the 4 TB Spark for this work. A 1 TB unit can support a small pilot but becomes tight once FP8/BF16 weights, several OCI archives, wheels, page renders, indexes, snapshots and rollback copies coexist. Use content-addressed cached images and an operational fullness ceiling of roughly 70–75% until measured recovery needs justify another rule. Self-encrypting NVMe hardware does not by itself prove that the approved key and encryption policy are active.

## 6.4 Runtime choice

Use a pinned derived container, not an improvised collection of host packages.

- **Preferred supply-chain baseline, conditionally qualified:** NVIDIA's current ARM64/Spark vLLM container. It provides paged attention and a local OpenAI-compatible API. NVIDIA vLLM 26.07 predates Qwen3.8's 14 August 2026 release and does not list it in the Spark playbook, so compatibility is a hypothesis until the exact digest passes text, local-image, 32K and network-denial tests.
- **Phase A challenger:** the exact SGLang Qwen3.8 recipe can be tested for performance, but it is not automatically the approved Phase B supply-chain choice.
- **Deferred:** TensorRT-LLM for Qwen3.8 until NVIDIA lists exact multimodal support for the model/precision on Spark.
- **Convenience tools:** LM Studio or Ollama are useful for exploration, but not the reproducible benchmark baseline.

Never upgrade Transformers, Torch or related packages inside a running NVIDIA image. Build a derived image in Phase A with exact versions and hashes, obey the base image constraints, run `pip check`, reassert Torch/CUDA versions, execute the full smoke suite and freeze the resulting OCI digest.

## 6.5 Recommended tool stack and challengers

| Job | Default candidate | Required challenger/control | Why this is the starting point |
|---|---|---|---|
| Native PDF/Office conversion | Docling slim + pypdfium2/native source text | direct/native extractor | local ARM64 path; retains hierarchy, tables, coordinates and audit trail |
| Simple scanned text | selective Tesseract | no-OCR and difficult-page parser controls | small, local and inspectable; use only when the text layer is empty/garbled |
| Difficult-page parsing | NVIDIA Nemotron Parse 2.0 | PaddleOCR-VL-1.5; native/Docling as control | compact structured challengers; exact frozen Spark compatibility still must pass |
| Canonical representation | versioned Pydantic/JSON Schema document model | lossless Docling JSON archive | typed validation and stable downstream contract |
| Exact identifiers | SQLite indexed/keyword fields | simple exact baseline | deterministic and easy to inspect |
| Lexical retrieval | SQLite FTS5/BM25 | Qdrant sparse or Tantivy challenger | transparent local baseline for engineering names and phrasing |
| Dense text retrieval | Qwen3-Embedding-0.6B | Qwen3-Embedding-4B quality challenger | keeps the interactive profile small; measured quality decides |
| Text reranking | Qwen3-Reranker-0.6B | no-reranker and 4B quality challenger | rerank only the top 20–50; measure gain and latency separately |
| Visual/mixed retrieval | Qwen3-VL-Embedding-2B | text+caption branch and no-visual control | small, multimodal, 32K; visual-only is not assumed superior |
| Visual reranking | Qwen3-VL-Reranker-2B | text reranker | only for visual candidate pages/regions |
| Vector search | single-node Qdrant | exact + lexical baseline | supports dense, sparse, fusion and multivectors locally |
| Authority/relations/audit | SQLite | optional graph store after a win | transparent, portable, low operational overhead |
| Routine visual observation | Qwen3-VL-2B-Instruct | no-VLM and Qwen3.8 hard-region controls | avoids spending a 27B model on every crop |
| Answering/hard observation | Qwen3.8-27B-FP8 | Qwen3.5-9B efficiency control; 10–25 paired BF16 cases; Nemotron Nano Omni challenger | tests whether the 27B FP8 model earns its cost and estimates the quality ceiling |
| Synthetic pipeline | typed Python + Pydantic; optional NeMo Data Designer | simple deterministic generator | separates truth, generation, validation and orchestration |
| Document rendering | Jinja2 HTML/CSS + pinned Chromium | independent Typst/template arm | deterministic layout with controlled visual diversity |
| Evaluation | deterministic scorers + engineer review | RAGChecker/Ragas diagnostics | acceptance remains tied to gold evidence and human authority |

No row is a procurement decision. “Default candidate” means the first item to test, not an exemption from testing.

## 6.6 Query-time flow

1. **Classify the question conservatively.** Identifier lookup, ordinary fact, visual/table, revision/authority or multi-source chain.
2. **Apply hard scope filters.** Enforce access, project, configuration, applicability and allowed authority states before similarity ranking. A later reranker must not resurrect an ineligible source.
3. **Run exact lookup first** for identifiers and document numbers.
4. **Run lexical and dense retrieval in parallel.** Keep a broad candidate pool.
5. **Fuse ranks.** Use reciprocal rank fusion rather than adding incompatible raw scores.
6. **Rerank.** Apply the specialist reranker to the fused shortlist.
7. **Expand only when indicated.** Add parent context, a cited section, superseded/current relation or one bounded graph hop.
8. **Escalate visual candidates.** Retrieve or crop the original page when the answer depends on visual structure.
9. **Build an evidence pack.** Include source ID, revision, authority, page, coordinates, text/table/crop and retrieval trace.
10. **Generate a cited response.** Require claim-level citations and an explicit answerability state.
11. **Verify.** Check cited locations exist, authority rules are respected and every material claim has support.

::: {.example}
**T17 through the cascade.** Exact search finds `T17`; dense search also finds “temperature-sensor acquisition mapping”; reranking puts the current ICD above a generic converter manual; the explicit reference opens the wiring sheet; the vision branch reads the connector line; the answer model receives only those items plus revision metadata.
:::

## 6.7 What is deliberately not in the default

- No end-to-end fine-tuning during the initial PoC. Improve data, retrieval and prompts first.
- No unlimited agent that can wander through the corpus. Use bounded query routes and budgets.
- No automatic full-corpus GraphRAG before a specific relation-heavy slice proves incremental value.
- No 200B model simply because 128 GB can hold an aggressively quantised checkpoint.
- No single visual index replacing structured text.
- No online service in Phase B.

# 7. Evidence ladder and decision claims {#evidence-ladder}

::: {.plain}
**In simple words:** prove each link separately before claiming that the whole chain works.
:::

## 7.1 The evidence ladder

| Level | What is tested | What it can establish |
|---|---|---|
| 0. Unit controls | schema, hash, exact ID, renderer and scorer tests | the mechanics behave as designed |
| 1. Public diagnostics | parser, retrieval, long-context and visual benchmarks | comparison with public tasks; no Airbus validity claim |
| 2. Engineered exact-truth cases | independently authored fictional bundles | known answers, controlled defects and causal diagnosis |
| 3. Real public rehearsals | rights-cleared technical documents | workflow realism before proprietary use |
| 4. Airbus family study | approved proprietary documents, offline | observation/archetype validity for the sampled families |
| 5. Protected real P42-KB benchmark | real engineer questions and evidence | primary project utility and regression evidence |
| 6. Bounded user exercise | engineers complete representative tasks | usefulness, trust and human effort in practice |

A higher level does not erase a failure at a lower level. A synthetic score cannot excuse loss of a real citation.

## 7.2 Seven questions the study must answer

1. **Observation:** can the parser/model record what is actually in a document?
2. **Generalisation:** can it infer reusable empirical patterns without copying one example?
3. **Governance:** can an expert turn observations into explicit mandatory, optional and conditional policy?
4. **Construction:** can the system create structurally valid new bundles from independent fictional truth?
5. **Leakage:** can it demonstrate that released outputs do not reproduce protected content under the declared threat model?
6. **Utility:** do the cases expose useful P42-KB failures and improve the protected real benchmark or defect discrimination?
7. **Capacity:** can one Spark and the available reviewers operate the workflow within an agreed budget?

## 7.3 Stop rules

Stop or redirect the work package when any of these is true:

- the protected real/search/cited-answer plan is slipping because of synthetic work;
- no neutral-template versus Airbus-informed improvement is demonstrated;
- fewer independent families or fictional worlds are available than the claim requires;
- the generator and scorer share hidden truth or templates in a way that makes the blind result circular;
- leakage/red-team canaries fail;
- a parser, model or dataset lacks approved rights;
- the Spark cannot meet the agreed batch time or stability envelope;
- subject-matter review exceeds the approved person-hour budget;
- a simpler exact-truth dataset gives the same diagnostic value.

# Part III — Practical runbook {#runbook}

# 8. Before running a model {#before-running}

::: {.plain}
**In simple words:** agree what problem is being tested, who owns the truth, what data may be used and what result would change a decision. Installing software comes later.
:::

## 8.1 Appoint the minimum roles

One person may hold several roles, but each responsibility needs a named owner.

| Role | The plain-language responsibility |
|---|---|
| PoC lead | protect Find, Answer and bounded Connect; activate or defer this work |
| Technical lead | define the system under test and approve configuration changes |
| Real-case owner | own the protected real questions, evidence and regression rule |
| Benchmark operator | run the frozen procedure and retain complete evidence |
| Document expert | decide document meaning and approve normative generation rules |
| Evaluation lead | keep blind truth sealed, manage scoring and adjudication |
| Security approver | approve the online/offline boundary, transition and derived outputs |
| Data/rights owner | decide permitted use, derivatives, retention and redistribution |
| Corpus product owner | define the needed families, volumes, languages, defects and service level |

::: {.analogy}
**Analogy — witnesses and referee.** The person training the team may see practice answers. The referee controls the sealed final answers. The document expert decides engineering correctness. Combining every role in one person creates an avoidable conflict.
:::

## 8.2 Sign a one-page activation record

The record must answer these questions in ordinary language:

- Which P42-KB use case and high-level requirement does this work support?
- Which protected real cases already exist?
- What gap cannot be tested safely with those cases?
- What is the smallest synthetic product that fills that gap?
- What will be stopped or deferred if time is tight?
- Who may see source documents, truth data, blind sets and generated outputs?
- What result would lead to adopt, redirect, defer or stop?

If these answers do not fit on one page, the work package is probably not yet bounded.

## 8.3 Define the corpus product before choosing a generator

Record a production envelope even for a feasibility study:

| Field | Example—not a default |
|---|---|
| Purpose | regression and evaluation only |
| Families | ICD, test report, configuration record and harness evidence |
| Independent fictional programmes | 4 development, 2 calibration, 2 sealed final |
| Bundle count | 60 accepted bundles |
| Pages | 6–25 per bundle, plus a long-tail slice |
| Languages | English primary; French/German slice if present in the real corpus |
| Deliberate defects | wrong mapping, stale revision, missing evidence, conflict and unit error |
| Human review | no more than 20 SME minutes per accepted bundle after calibration |
| Batch objective | complete 20-bundle generation and validation within one working day |
| Release | internal `AI_DERIVED_SYNTHETIC`; no external redistribution |

Do not promise these numbers before a pilot measures them. Their purpose is to make workload and success visible.

## 8.4 Build the real-case map first

For each protected question record:

- user task and expected decision;
- required evidence set, not only a prose answer;
- relevant source, revision, page/section and authority;
- answerability state;
- expected conflicts or traps;
- capability: Find, Answer or Connect;
- language and modality;
- severity if missed;
- reviewer and last validation date.

This map determines which synthetic cases are useful. Without it, synthetic generation becomes a document-style exercise disconnected from P42-KB.

## 8.5 Clear rights before download or derivation

“Available on the internet,” “free to download,” “open-source code” and “permission to redistribute source documents” are different statements. Keep four separate fields:

1. code/evaluator licence;
2. dataset annotation licence;
3. rights in the underlying source documents;
4. permission to create and release derivatives.

The benchmark-rights matrix is in Appendix C. It is an engineering aid, not legal advice.

## 8.6 Pre-register the comparison

Before looking at final results, record:

- primary and secondary metrics;
- independent unit of analysis—normally programme or bundle, not every question;
- development, calibration, blind and protected-real boundaries;
- candidate configurations and information budgets;
- tie rule: prefer the simpler, faster and easier-to-audit option;
- missing-output, timeout, retry and malformed-response treatment;
- judge calibration procedure;
- maximum compute and reviewer hours;
- real-regression and leakage red lines;
- which changes require a new untouched blind set.

::: {.check}
**Ready to proceed when:** the activation, real-case map, rights register, product envelope, security boundary and pre-registration are approved.
:::

# 9. Phase A — build and qualify with public material {#phase-a}

::: {.plain}
**In simple words:** Phase A may use the internet because it handles only public, rights-cleared material. Use that freedom to download, compare and fix the complete pipeline before any Airbus document enters it.
:::

## 9.1 Step A0 — create a clean, recorded workspace

Use a task-specific path. The commands below are examples; security and storage owners must approve the actual location.

```bash
export P42_ROOT=/opt/p42kb-qualification

install -d -m 0750 \
  "$P42_ROOT"/{source,models,containers,wheels,datasets,configs,runs,logs,transition}

date --iso-8601=seconds | tee "$P42_ROOT/logs/start_time.txt"
uname -a | tee "$P42_ROOT/logs/uname.txt"
cat /etc/os-release | tee "$P42_ROOT/logs/os-release.txt"
free -h | tee "$P42_ROOT/logs/memory.txt"
df -h | tee "$P42_ROOT/logs/storage.txt"
docker version | tee "$P42_ROOT/logs/docker-version.txt"
nvcc --version | tee "$P42_ROOT/logs/cuda-version.txt"
```

**Why.** If a later result changes, this record helps distinguish a model change from an operating-system, CUDA or container change.

**Done when.** The directory exists with controlled ownership, platform files are readable and no Airbus data are present.

## 9.2 Step A1 — establish the cheapest baseline

Before using embeddings or a language model:

1. ingest document ID, title, revision, status, date, page count and text layer;
2. implement exact identifier lookup;
3. implement a BM25/lexical baseline;
4. run the protected development questions;
5. record evidence Recall@*k*, rank, latency and failure examples.

::: {.analogy}
**Analogy — mark the stopwatch before tuning the engine.** A complex system is not an improvement unless it beats the simple system on the job that matters.
:::

::: {.example}
**T17 baseline failure.** Exact search finds every literal `T17`, but the question “Which acquisition path carries the temperature-sensor output?” may not contain the identifier. This shows where semantic retrieval can add value.
:::

## 9.3 Step A2 — run a parser bake-off on representative pages

Do not parse thousands of pages first. Select approximately 40–80 pages covering the real distribution:

- native-text single-column pages;
- dense engineering tables;
- multi-column reports;
- scans and poor contrast;
- drawings and captions;
- headers/footers and revision tables;
- non-English or mixed-language pages;
- deliberately difficult identifiers such as `O/0`, `I/l/1` and punctuation.

Create gold checks for the elements that affect P42-KB:

| Check | Example failure |
|---|---|
| identifier integrity | `ADC12` becomes `ADCI2` |
| reading order | right column inserted midway through left column |
| table association | T17 value attached to T18 row |
| heading ancestry | paragraph loses section and requirement scope |
| page and coordinates | citation points to the wrong page or crop |
| footnote/caption association | qualification note detached from the table |
| revision block | obsolete issue mistaken for current issue |

Compare at least:

1. native/direct text extraction;
2. Docling standard pipeline;
3. Nemotron Parse 2.0 on the difficult-page stratum;
4. PaddleOCR-VL-1.5 or another rights-cleared compact challenger if it can run reproducibly.

Measure both **component accuracy** and **downstream evidence retrieval**. A transcript can have excellent character accuracy while silently attaching a number to the wrong row.

::: {.check}
**Parser exit:** one default and one fallback are selected per page class; every selected output retains source hash, page, coordinates, parser name/revision and confidence/validation flags.
:::

## 9.4 Step A3 — build the canonical document map

Normalise every parser output into a versioned schema. Minimum objects are:

- `Document`: source hash, ID, revision, status, authority and language;
- `Page`: number, dimensions and rendered-image hash;
- `Block`: type, text, bounding box, reading order and parser provenance;
- `Section`: heading path and contained blocks;
- `Table`: cells, row/column relationships, caption and notes;
- `Reference`: source object, target string, resolved target and resolution status;
- `Chunk`: retrieval text plus parent, page and evidence coordinates.

Archive the raw parser output as well. Normalisation must be repeatable, not destructive.

**Chunking rule.** Prefer complete sections, paragraphs, table rows and captioned figures. Split oversized objects with overlap while keeping parent context. Do not start with a fixed 500-token shredder.

**Retrieval label.** Prepend only deterministic metadata—document ID/title, revision, authority, applicability and section path—to the indexed text. Keep the original evidence text unchanged and separately addressable. This gives search the equivalent of a labelled folder without letting a model rewrite the evidence.

## 9.5 Step A4 — qualify retrieval one layer at a time

Run the same frozen question set through these arms:

| Arm | Purpose |
|---|---|
| Exact only | prove identifier handling |
| Lexical only | set the transparent baseline |
| Dense only, 0.6B | set the fast semantic baseline |
| Dense only, 4B | measure quality gained for extra cost |
| Exact + lexical + dense | test broad recall and rank fusion |
| Hybrid + text reranker | test final text ranking |
| Hybrid + layout/reference expansion | test bounded Connect cases |
| Hybrid + selective visual branch | test tables/drawings without changing ordinary cases |
| Direct all-page Qwen, tiny diagnostic slice | show what the simple long-context/VLM shortcut gains or loses; never assume it is the production route |

Use rank fusion, not raw score addition. Dense cosine scores and lexical scores have different meanings and scales. RRF is the safe starting point; tune weights only on development/calibration data.

Apply access, programme, configuration, applicability and authority eligibility as hard filters before lexical/dense ranking. Run a separate diagnostic that intentionally searches superseded/conflicting evidence when the user asks a historical or conflict question; do not simply mix obsolete sources into the ordinary candidate pool.

For every miss ask:

- Was the evidence absent from ingestion?
- Was it present but segmented incorrectly?
- Did no retrieval path activate it?
- Was it retrieved and removed during fusion or reranking?
- Was it selected but ignored by the answer model?

This attribution is more valuable than a single end-to-end percentage.

## 9.6 Step A5 — qualify the answer model

Use identical evidence packs and compare:

- Qwen3.8-27B-FP8 at the chosen context/reasoning settings;
- Qwen3.5-9B as the smaller efficiency control, or the closest rights-cleared smaller Qwen native-VLM that passes the Spark smoke test;
- a small BF16 slice to estimate quantisation loss;
- Nemotron-3-Nano-Omni-30B-A3B on the English or supported-language slice;
- a no-generation extractive answer for direct lookup cases.

Require the response envelope:

```json
{
  "answerability": "ANSWERABLE",
  "answer": "T17 is intended to use ADC12.",
  "claims": [
    {
      "claim": "The current ICD maps J12 pin 4 to ADC12.",
      "evidence_ids": ["ICD-009-C:p14:table3:r17"]
    }
  ],
  "conflicts": [],
  "limitations": ["The as-run configuration is not present."],
  "confidence": "SUPPORTED"
}
```

Parse and validate the JSON before scoring its prose. A malformed response is an operational failure, not a hidden retry until it looks good.

## 9.7 Step A6 — run public diagnostics only when they answer a question

Public benchmarks are instruments. Choose the instrument that measures the suspected fault.

| Diagnostic | Use it when… | Do not claim… |
|---|---|---|
| OmniDocBench | selecting or debugging a parser | that its overall score predicts Airbus page accuracy |
| MMLongBench-Doc-V2 | testing long visual PDFs, cross-page and unanswerable questions | that V1 and V2 numbers are comparable |
| ViDoRe / ArXivDoc | comparing visual, text and interleaved retrieval representations | that one public document domain settles the P42 corpus choice |
| ViMDoc / HEAVEN tasks | testing long multi-document visual retrieval efficiency | production throughput before measuring the Spark corpus |
| SynthDocBench | isolating length, chart, layout and cross-modal difficulty | general real-document validity |
| LongBench v2 | diagnosing long-text reasoning and context handling | document parsing or provenance ability |
| VRDU | testing few-shot extraction and unseen templates | full RAG or multi-document reasoning |
| DocBench | reproducing a specific raw-PDF QA comparison after rights clearance | a maintained or fully licensed production path |

Run a 5–10 case adapter smoke test before any full set. Stop if IDs, page rendering, prompts, output schema or scorer mapping are wrong.

## 9.8 Step A7 — perform the public rehearsal

Build at least two rights-cleared rehearsal families:

- one visible development family;
- one sealed family created or selected by a different person.

Run the entire vertical slice: acquire → parse → normalise → observe → aggregate → approve policy → create independent truth → build AST → render → ingest → retrieve → answer → score → leakage scan.

The sealed family tests whether the procedure generalises before Airbus documents appear.

## 9.9 Step A8 — freeze the transition candidate

The freeze includes more than model weights:

- source code and patches;
- container archives and immutable image digests;
- complete wheelhouse and system-package inventory;
- model weights, tokenisers and model cards;
- public datasets, source PDFs and licences;
- parser and renderer assets, fonts and browser/Typst binaries;
- development, calibration and sealed rehearsal manifests;
- configuration files and prompt templates;
- database schemas and migration scripts;
- scorers, judge configuration and calibration evidence;
- malicious/network probes and offline acceptance tests;
- software bill of materials, checksums and recovery instructions.

::: {.check}
**Phase A exit:** the vertical slice works on public material; the chosen candidate beats or complements the simple baseline on mapped gaps; rights are recorded; resource projections fit; and the transition bundle can be rebuilt without internet access.
:::

# 10. The security airlock — Phase A to Phase B {#transition}

::: {.plain}
**In simple words:** disconnecting a machine does not erase what an internet-connected system previously downloaded or changed. Treat the transition like moving equipment through a clean-room airlock.
:::

## 10.1 Why a trusted rebuild is required

The same Spark may be used in both phases, but the Phase B baseline should be a trusted reimage or approved clean build. This reduces the risk of forgotten remote agents, telemetry, cached credentials, unapproved packages or persistence from the connected phase.

::: {.analogy}
**Analogy — clean-room airlock.** Closing the outside door is necessary, but the material is not clean merely because the door is closed. Inventory, inspection and an approved transfer process happen before the inside door opens.
:::

## 10.2 Build checksums without hashing the checksum file itself

Run this only after every wheel, dataset, container archive, model and rehearsal asset is present:

```bash
export TRANSITION_DIR=/approved/transfer/p42kb-v0.9

cd "$TRANSITION_DIR"
find . -type f \
  ! -name 'SHA256SUMS' \
  ! -name 'SHA256SUMS.asc' \
  -print0 \
  | sort -z \
  | xargs -0 sha256sum > SHA256SUMS

sha256sum --check SHA256SUMS
```

Sign the checksum file using the approved organisational mechanism. A checksum proves byte identity, not trustworthiness or licence clearance.

## 10.3 Preserve actual container content

An image name is not an offline asset. Save the image layers and record the digest:

```bash
export IMAGE_REF='nvcr.io/nvidia/vllm:<approved-tag>'
export ARCHIVE_DIR="$TRANSITION_DIR/containers"

docker pull "$IMAGE_REF"
docker image inspect "$IMAGE_REF" > "$ARCHIVE_DIR/vllm-image-inspect.json"
docker save "$IMAGE_REF" | zstd -T0 -19 -o "$ARCHIVE_DIR/vllm-image.tar.zst"
```

Replace `<approved-tag>` with the tested tag from NVIDIA's current Spark recipe. Do not copy a floating `latest` tag into the freeze record.

## 10.4 Trusted Phase B build

1. Reimage or apply the approved secure baseline.
2. Do not restore Phase A home directories or credentials wholesale.
3. Verify firmware, DGX OS, drivers and secure configuration against the approved record.
4. Import only allow-listed, signed transition assets.
5. Verify every checksum before installation.
6. Load container archives locally; do not permit registry fallback.
7. Disable and test DNS, routing, proxy, telemetry and update paths.
8. Run the offline test with **no Airbus material**.
9. Snapshot the clean Phase B baseline.
10. Only then introduce approved Airbus documents.

## 10.5 Offline acceptance test

The test must do more than `ping` a public address. It should attempt:

- DNS resolution;
- direct IPv4 and IPv6 connection;
- HTTP/HTTPS with and without proxy variables;
- package-manager and container-registry access;
- model-library telemetry/update checks;
- time synchronisation and remote logging routes;
- a deliberately missing local model to ensure no automatic download occurs.

Expected result: all external paths fail closed, while the local parse/index/retrieve/answer smoke test succeeds.

::: {.check}
**Transition exit:** security approves the build record, imported assets, offline test and snapshot. Airbus data have never touched the Phase A system state.
:::

# 11. Phase B — the Airbus-controlled family study {#phase-b}

::: {.plain}
**In simple words:** first prove that Airbus-specific archetypes add value. If they do, learn patterns from approved documents without confusing frequency with policy, then build new test bundles from separate fictional truth.
:::

## 11.1 Step B0 — run the necessity test

Compare two bounded paths on identical target characteristics:

- **Neutral path:** public/ECSS-informed or SME-authored generic templates with no Airbus-derived structure.
- **Airbus-informed path:** archetypes induced from the approved source families.

Score both on:

- coverage of required P42-KB failure modes;
- realism judged by blinded SMEs;
- downstream retrieval/answer discrimination;
- generation and review time;
- leakage and governance burden.

Continue proprietary archetype work only if the Airbus-informed path adds material value that the neutral path cannot provide. Record the margin before opening the final set.

## 11.2 Step B1 — inventory without leaking content into labels

Assign neutral internal IDs such as `FAM-03/DOC-017`. Record separately:

- family and document type;
- programme/bundle group;
- revision/status and authority;
- page count and modalities;
- language;
- expected layout classes;
- supplier/third-party or export-control flags;
- permitted purpose, derivative rights, retention and release class.

Do not put project names, requirement text or sensitive identifiers into filenames, experiment labels or public dashboards.

## 11.3 Step B2 — split by independent group

Hold out entire programme/bundle groups, not random pages from the same project. Otherwise the system can memorise the house style, IDs or repeated paragraphs.

Use separate pools:

- development groups for prompt/schema work;
- calibration groups for thresholds and judge calibration;
- blind validation groups sealed until configuration freeze;
- protected real P42-KB cases that remain outside archetype tuning.

If the study has too few independent groups, report a **descriptive feasibility study**. Do not manufacture statistical confidence by counting many pages or questions from one programme as independent.

## 11.4 Step B3 — create gold structural manifests

Two reviewers independently record document structure without copying long prose. A manifest may include:

- section path and order;
- element type: paragraph, list, table, figure, requirement or note;
- repeated or conditional elements;
- cross-reference type and target class;
- identifier, unit and revision patterns;
- layout constraints;
- authority/approval fields;
- permitted variability;
- features that must never be derived or released.

Disagreements are adjudicated and recorded. Gold means reviewed reference for this experiment, not universal truth.

## 11.5 Step B4 — observe each document before aggregating

The observation model receives one authorised document and a strict schema. It reports **what is present**, with page/region evidence. It does not decide what a generated document must contain.

Example:

```json
{
  "document_id": "DOC-017",
  "observations": [
    {
      "feature_id": "signal_mapping_table",
      "state": "PRESENT",
      "section_path": ["4 Interfaces", "4.2 Signal mapping"],
      "evidence": [{"page": 14, "bbox": [82, 214, 512, 694]}],
      "confidence": "HIGH"
    }
  ],
  "unknowns": ["Applicability of the annex could not be established"]
}
```

Score observation accuracy before family aggregation. Otherwise a plausible family summary can hide repeated page-level extraction errors.

## 11.6 Step B5 — aggregate empirical patterns deterministically

Use code to count and compare reviewed observations:

- prevalence by independent document and group;
- stable order/parent relationships;
- conditional co-occurrence;
- identifier and layout variation;
- disagreement and missing-data rates.

An LLM may suggest labels or cluster explanations, but the underlying counts and conditions must be reproducible.

Keep three columns separate:

| Column | Question | Owner |
|---|---|---|
| Empirical prevalence | How often was it observed? | pipeline + evaluation lead |
| Normative generation policy | Must/may/must-not it appear, and under what condition? | SME/data owner |
| Scenario policy | Which optional feature or defect is selected for this test? | benchmark designer |

::: {.example}
**Correct treatment.** “A signal-mapping table appeared in 8/10 reviewed ICDs. The SME requires it when the document declares a discrete electrical interface. The T17 scenario selects it because the defect depends on a channel mapping.”

**Incorrect treatment.** “The table appeared in 80%, therefore it is mandatory.”
:::

## 11.7 Step B6 — freeze the archetype contract

An approved archetype contains:

- scope and applicable family;
- empirical feature catalogue with uncertainty;
- SME-approved mandatory, optional, conditional and forbidden rules;
- section/element/relationship constraints;
- allowed vocabulary and identifier patterns without copied protected content;
- language and modality variants;
- validation rules;
- provenance and approval record;
- known limitations and source coverage.

Change control begins here. A later change requires a version and may require fresh blind validation.

## 11.8 Step B7 — create independent fictional truth

Freeze the **graph schema and generator**, not one reusable fictional programme. The freeze must include:

- node/edge types and constraints;
- identifier and value-generation rules;
- type, unit, range, cardinality, revision-validity and allowed-cycle rules;
- explicit negative claims and incompatibility rules, not only positive facts;
- consistency rules and defect-injection rules;
- seed-pool creation and allocation;
- sealed manifests assigning disjoint seeds/worlds to development, calibration and final pools.

Each generated world should contain shared truth across its documents. This creates coherent bundles rather than unrelated fake files.

::: {.analogy}
**Analogy — continuity bible.** A television series keeps one record of characters, events and dates so that episode 8 does not contradict episode 2 accidentally. The fictional programme graph is the continuity bible for every generated document.
:::

## 11.9 Step B8 — build and validate document ASTs

For each document:

1. select an approved archetype and scenario;
2. query the fictional graph for allowed facts;
3. create a typed AST;
4. validate required fields, references, units and constraints;
5. generate bounded prose only inside approved fields;
6. validate again;
7. render with a pinned deterministic renderer;
8. parse the rendered output independently and compare it with the AST;
9. quarantine any mismatch.

The LLM may write explanatory prose. It must not choose identifiers, critical numerical values, authority status or expected answers when those can be generated deterministically.

Keep five factors separately controlled: semantic truth, document/archetype structure, visual style, scan/corruption profile and seeded defect. Then create controlled counterfactual pairs:

- change one fact while holding presentation fixed;
- change presentation while holding facts fixed;
- inject one defect while holding every other fact fixed;
- remove one required evidence item while leaving plausible distractors.

This is the document equivalent of changing one component on a test bench: a result can be attributed to the changed factor instead of to a completely different fake project. Use a pairwise or *t*-way covering array, for example with NIST ACTS, when the full combination space is too large. Coverage of combinations is useful engineering discipline; it is not evidence that the simulator represents the whole Airbus population.

## 11.10 Step B9 — avoid a circular blind test

The strongest final cases must not be created and judged by the candidate pipeline alone.

Use at least one of these controls:

- independently authored truth/AST from a separate implementation;
- a second renderer/template family not used in development;
- human-authored final cases from the same frozen schema;
- a different generator model with no access to candidate observations;
- exact oracle answers derived from the truth graph, never from the candidate response.

The candidate system receives only the rendered documents and permitted metadata, not the truth graph, AST, answer keys or generation logs.

Keep three independent views of correctness:

1. **Model-visible evidence:** exactly what the evaluated P42-KB system is allowed to retrieve.
2. **Hidden fictional truth:** the exact graph and generation manifest used to score factual and cross-document consistency.
3. **Normative expert truth:** the separately approved rules describing what a valid member of the document family must, may or must not contain.

The candidate model must not write any of these three oracles after seeing its own output. This is the equivalent of keeping the exam paper, marking scheme and engineering code under different control.

## 11.11 Step B10 — leakage and release gate

Define three threat classes before scanning; do not combine them into one reassuring word such as “safe”:

- **proprietary-content leakage:** protected wording, identifiers, numbers, structure, images or relationships reproduced in an output;
- **identity/privacy disclosure:** a person or protected unit can be inferred or linked, even without exact copying;
- **public-benchmark contamination:** the candidate or judge may have seen public benchmark questions/answers during pretraining or development.

At minimum test:

- exact file and text hashes;
- long matching strings and character/token *n*-grams;
- MinHash or locality-sensitive similarity over segments;
- sensitive identifiers, people, suppliers and project names;
- numeric tables and rare value combinations;
- semantic similarity to source regions;
- image/crop similarity and retained metadata;
- canary strings planted only in protected sources;
- extraction probes against every model that received protected context;
- representative real non-member controls so a detector is not merely separating machine and human text;
- manual review of highest-risk matches.

A detector threshold is not a declassification rule. Every output inherits the source classification unless the authorised owner changes it.

After any detector, threshold or pipeline change, use a **fresh untouched canary pool**. The previously opened blind canaries become regression tests. Use another fresh pool at the limited-production gate.

## 11.12 Step B11 — test downstream utility

Index the accepted synthetic bundles with the exact P42-KB pipeline under test. Freeze and record:

- parser and normaliser revisions;
- chunk schema and authority rules;
- exact, lexical, dense, visual and graph configuration;
- embedding/reranker/model revisions and quantisation;
- retrieval and context budgets;
- prompts, scorers and judge configuration;
- real and synthetic corpus snapshots.

Compare the system with and without the new synthetic cases. Useful outcomes include:

- a defect class becomes measurable;
- two candidate retrieval architectures separate more clearly;
- regression detection improves;
- difficult cases expose a known limitation;
- engineer review becomes more efficient.

For the archetype/reconstruction method itself, compare at least these arms on the same sealed families where feasible:

1. no archetype/direct extraction;
2. a manual neutral template;
3. a fixed canonical schema;
4. direct few-shot LLM generation;
5. the approved archetype-driven truth → AST → renderer path.

Score exact fact, required-field, relation, revision and defect correctness first. Pixel similarity and generic semantic similarity are only presentation diagnostics: a visually convincing document can contain the wrong channel, and an ugly document can still encode exact truth.

For a regression or challenge corpus, a lower end-to-end answer score can be intentional because the cases are harder. The success claim must therefore match the corpus purpose: **better discrimination and coverage**, not automatically higher accuracy.

## 11.13 Step B12 — retention and deletion

Apply approved rules to every class, including:

- raw documents and page renders;
- parser caches and embeddings;
- prompts and responses;
- observations and archetypes;
- failed and quarantined synthetic outputs;
- truth graphs, ASTs and answer keys;
- indexes, logs and judge traces;
- transition and backup copies.

Test deletion, do not merely document it. Retain enough immutable evidence to reproduce approved headline results within the permitted policy.

::: {.check}
**Phase B exit:** the necessity test passed; independent group holdouts and blind truth were respected; normative policy was human-approved; generated bundles are coherent and validated; leakage controls passed with fresh canaries; protected real results did not regress; and human/compute cost is acceptable.
:::

# 12. Score what matters {#evaluation}

::: {.plain}
**In simple words:** one average score hides whether the system failed to find evidence, chose an obsolete source, ignored a citation or invented a conclusion. Keep the layers separate.
:::

## 12.1 Minimum scorecard

| Layer | Primary measures | Plain-language question |
|---|---|---|
| Ingestion | block/table/reading-order accuracy; identifier integrity | Did the document map preserve the evidence correctly? |
| Retrieval | Recall@*k*, mean reciprocal rank, nDCG, complete-evidence recall | Did we find all evidence needed, not just one useful-looking passage? |
| Authority | current/superseded selection accuracy; conflict recall | Did the system use the applicable revision and expose disagreement? |
| Citation | citation precision/recall; location validity | Does each citation point to evidence that supports its claim? |
| Answer | reviewed correctness by required claim | Is the engineering conclusion correct and complete? |
| Faithfulness | supported-claim rate; unsupported-claim rate | Did the answer add anything the evidence does not establish? |
| Abstention | not-answerable precision/recall; over-answer rate | Does it stop honestly when evidence is insufficient? |
| Synthetic truth | exact fact/edge/occurrence correctness; constraint pass rate; oracle answer exactness | Do the generated documents match the hidden fictional world? |
| Archetype/reconstruction | required/conditional/forbidden rule accuracy; relation and revision consistency; seeded-defect fidelity | Is this a valid new family member, not merely a similar-looking page? |
| Leakage | detector and manual-review failures by threat class | Did protected source content escape? |
| Human system | SME minutes, disagreement, correction rate | Is review practical and reliable? |
| Spark operation | p50/p95 latency, pages/hour, memory peak, crashes/restarts | Can the one-machine workflow finish on time and remain stable? |

## 12.2 Complete-evidence recall

Ordinary recall asks whether a relevant item appeared. Connect questions often need a set: current ICD + configuration + test report. **Complete-evidence recall** is one only when at least one valid complete evidence set survives the retrieval budget.

::: {.analogy}
**Analogy — a three-legged stool.** Retrieving two excellent legs does not make the stool usable. Missing one required evidence item can make the conclusion impossible.
:::

## 12.3 Claim-level evidence

Break the expected answer into claims. For each claim record:

- required, optional or forbidden;
- supporting and contradicting evidence;
- applicable revision and authority;
- deterministic match rule or human rubric;
- severity if absent or unsupported.

This is more stable than comparing the whole answer with one “gold paragraph.”

For synthetic cases, score each claim against all three views: what evidence was visible, what the hidden fictional world says, and what the independently approved normative policy requires. A system may correctly say “not established” from incomplete visible evidence even though the hidden truth contains an answer; that is a successful abstention, not an error.

## 12.4 Use automated judges carefully

For every judge model:

1. prepare a blinded calibration sample with clear good, partial, unsupported and conflicting answers;
2. obtain at least two human ratings where feasible;
3. measure judge agreement, systematic bias and decision-changing errors;
4. freeze judge model, prompt, reasoning setting and threshold;
5. report human and judge results separately;
6. send boundary and high-severity cases to human adjudication.

Ragas and RAGChecker are useful for diagnosis, but neither becomes the engineering authority.

## 12.5 Statistical interpretation

- Use programme/bundle or engineer as the independence unit.
- Use paired comparisons when configurations see the same cases.
- Bootstrap or resample by independent group, not by every question from one PDF.
- Report confidence intervals and the raw numerator/denominator.
- Pre-register non-inferiority margins from operational consequences.
- If the sample is small, say “descriptive feasibility” rather than disguising uncertainty with decimal precision.
- Inspect slices: identifiers, tables, visuals, language, revision, answerability and evidence-hop count.

## 12.6 External-validity check

Freeze the synthetic design, thresholds and preferred configuration before opening the protected real benchmark. In addition to the planned real holdout, retain an untouched **temporal or prospective slice**—cases collected after the design period or from a later approved intake. Compare:

- which system configuration wins, not only the mean score;
- critical error types and their severity;
- false-answer and abstention behaviour;
- engineer time to verify evidence;
- whether synthetic cases predicted the real failures.

If synthetic tuning improves its own test rig but harms a critical real slice, reject the change. Many seeds from one generator remain variations of that generator; they do not become independent samples of all Airbus documents.

## 12.7 Decision matrix

| Result | Decision |
|---|---|
| Real cases improve or remain within the approved margin; synthetic adds diagnostic coverage; cost and leakage pass | adopt bounded capability |
| Same real quality, but neutral templates provide equivalent synthetic value | use neutral templates; stop proprietary archetype induction |
| Good archetypes but rendering/prose causes failures | retain archetypes/truth; replace or simplify generator/renderer |
| Synthetic scores rise while protected real cases regress | reject the change |
| Useful exact-truth tests but realistic reconstruction is too costly | redirect to machine-readable cases and lightweight documents |
| Too few independent families/worlds or reviewers | report feasibility only; defer generalisation claim |
| Leakage, rights or security red line fails | quarantine and stop release |

# 13. Put the work in the P42-KB schedule {#schedule}

::: {.plain}
**In simple words:** synthetic work earns its place after the real baseline exists. It must not become a parallel research programme that consumes the ten-week PoC.
:::

## 13.1 Recommended sequence

| PoC period | Primary P42-KB work | Synthetic/archetype work allowed |
|---|---|---|
| Weeks 1–2 | corpus characterisation, real-case map, exact and lexical baseline | product contract; public research and tiny schema tests only |
| Weeks 3–5 | parsing, hybrid retrieval, cited Answer | Phase A parser/retrieval bake-off; public rehearsal |
| Weeks 5–7 | bounded Connect, authority and references | neutral exact-truth bundles mapped to real gaps |
| Gate 3 | decide specialist extension | run necessity test and authorise or defer Phase B |
| Weeks 7–9 | core hardening or one selected vertical | small Airbus family study only if authorised and resourced |
| Week 9 | freeze and protected challenge | untouched blind synthetic plus protected real set |
| Week 10 | analyse and decide | report bounded value, cost, limits and next step |

## 13.2 Minimum credible PoC populations

Use the governing plan as authority. A practical starting envelope is:

- approximately 30–50 reviewed real cases as the committed minimum;
- approximately 50–100 controlled synthetic cases if they add value;
- a protected subset held out from tuning;
- 3–5 historical/challenge cases if available;
- parser gold pages chosen for diversity, not volume.

Do not run thousands of public questions merely because they are downloadable. A full MMLongBench/LongBench/SynthDoc matrix can consume thousands of model requests while contributing little to a ten-week decision.

## 13.3 Capacity sheet

Estimate and then measure:

| Activity | Machine measure | Human measure |
|---|---|---|
| page conversion | pages/hour and failure rate | correction minutes/page |
| embedding/index | chunks/hour, index bytes and peak memory | metadata clean-up |
| retrieval evaluation | queries/hour and latency distribution | gold evidence creation |
| answer generation | input/output tokens, images, seconds/query | answer adjudication |
| archetype observation | pages and documents/hour | manifest review minutes |
| generation/render | bundles/hour and quarantine rate | correction minutes/bundle |
| leakage scan | bytes/pages/hour | review minutes for flagged matches |
| requalification | elapsed time after one component change | approval/review workload |

Include rasterisation, image encoding, queue/restart overhead, cache warm-up and retries. Decode speed alone is not an end-to-end capacity forecast.

For each workload bucket, calculate:

```text
elapsed_hours = case_count ×
  (time_to_first_token
   + output_tokens ÷ measured_decode_rate
   + parser_visual_and_validation_time
   + expected_retry_cost) ÷ 3600
```

Keep born-digital, scan, table, drawing, short-context and long-context buckets separate. Measure cold and warm runs. Plan from **accepted bundles or reviewed answers per hour**, not advertised tokens per second.

Sweep client concurrency only after the one-sequence 8K → 16K → 32K ladder is stable and swap-free. Test 1, then 2, then 4 concurrent requests; stop at the first instability or unacceptable p95 latency. One Spark is a bounded batch evaluator/generator for this PoC, not a multi-user production service.

# 14. Troubleshooting by symptom {#troubleshooting}

| Symptom | Most likely questions to ask | First safe action |
|---|---|---|
| Exact IDs are missing | Did parsing alter characters? Was punctuation tokenised? Is exact lookup separate? | compare source bytes/text and exact-index payload |
| Answer cites the wrong revision | Is authority metadata present and filtered? Does the reranker know status? | add deterministic authority filter/boost before changing the LLM |
| Tables look correct but answers are wrong | Were row/column/header relationships preserved? | score cell association and retrieve the whole row with heading |
| Visual branch is slow | Is it indexing every page image or reranking only candidates? | restrict to hard-page classes and shortlisted regions |
| Long context causes stalls/OOM | What is model length, image count, KV cache and concurrency? | reduce active sequences, context and image budget; unload other services |
| Dense retrieval misses signal names | Are exact and lexical legs active? Was the embedding instruction appropriate? | restore exact/lexical baseline and inspect candidate activation |
| Graph expansion adds noise | Are edges explicit and use-case relevant? Is hop/budget bounded? | turn expansion off; measure each edge type separately |
| Archetype looks plausible but gold score is low | Were document observations scored before aggregation? | fix observation/parser errors first |
| Generated documents contradict each other | Do they share one truth graph and validate references? | quarantine; validate AST against truth before rendering |
| Leakage detector passes everything | Was it calibrated with planted canaries and near-copy controls? | build fresh calibration canaries; do not release |
| Automated judge loves fluent wrong answers | Was it calibrated for evidence and authority? | use claim-level deterministic/human scoring and re-calibrate |
| Benchmark result cannot be reproduced | Were source, model, container, dataset, prompt and scorer revisions captured? | stop comparison; rebuild from a complete manifest |

# Part IV — Reference material {#reference}

# Appendix A — Command reference {#commands}

::: {.warning}
**Read before copying.** Values inside angle brackets are mandatory local choices. Resolve them, record them and remove the brackets. Run public downloads only in Phase A. The commands are examples of the controlled pattern; the exact NVIDIA image tag and model commit must come from the configuration that passed the Spark smoke test.
:::

## A.1 Create a run ID and immutable configuration copy

```bash
export P42_ROOT=/opt/p42kb-qualification
export RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-parser-retrieval-pilot"
export RUN_DIR="$P42_ROOT/runs/$RUN_ID"

install -d -m 0750 "$RUN_DIR"/{config,input,output,metrics,logs}
cp --preserve=timestamps "$P42_ROOT/configs/experiment.yaml" "$RUN_DIR/config/"
sha256sum "$RUN_DIR/config/experiment.yaml" > "$RUN_DIR/config/SHA256SUMS"
```

**Expected check:** `$RUN_DIR/config/SHA256SUMS` exists and verifies with `sha256sum --check`.

## A.2 Download an exact model revision in Phase A

```bash
export MODEL_REPO='Qwen/Qwen3.8-27B-FP8'
export MODEL_REVISION='<full-hugging-face-commit>'
export MODEL_DIR="$P42_ROOT/models/qwen3.8-27b-fp8-$MODEL_REVISION"

hf download "$MODEL_REPO" \
  --revision "$MODEL_REVISION" \
  --local-dir "$MODEL_DIR"

find "$MODEL_DIR" -type f -print0 \
  | sort -z \
  | xargs -0 sha256sum > "$MODEL_DIR/SHA256SUMS"
```

Do not use `main` in the experiment manifest. Record the model card and licence beside the weights.

## A.3 Pull, inspect and archive a Spark-compatible inference image

```bash
export VLLM_IMAGE='nvcr.io/nvidia/vllm:<tested-spark-tag>'
export CONTAINER_DIR="$P42_ROOT/containers"

docker pull "$VLLM_IMAGE"
docker image inspect "$VLLM_IMAGE" > "$CONTAINER_DIR/vllm-inspect.json"
docker save "$VLLM_IMAGE" | zstd -T0 -19 -o "$CONTAINER_DIR/vllm-image.tar.zst"
sha256sum "$CONTAINER_DIR/vllm-image.tar.zst" \
  > "$CONTAINER_DIR/vllm-image.tar.zst.sha256"
```

The `RepoDigests` field in `vllm-inspect.json` is the immutable identity. Freeze it in the experiment configuration.

## A.4 Start the conservative Qwen candidate service

```bash
export MODEL_ROOT='<absolute-local-model-root>'
export RUN_ROOT="$RUN_DIR/vllm"
export CACHE_ROOT="$RUN_DIR/cache"
export VLLM_DIGEST='<approved-derived-image@sha256:digest>'

install -d -m 0750 "$RUN_ROOT" "$CACHE_ROOT"

docker run --rm --name p42-qwen \
  --gpus all \
  --network=none \
  --shm-size=8g \
  -e VLLM_NO_USAGE_STATS=1 \
  -e HF_HUB_OFFLINE=1 \
  -e TRANSFORMERS_OFFLINE=1 \
  -e HF_DATASETS_OFFLINE=1 \
  -v "$MODEL_ROOT:/models:ro" \
  -v "$RUN_ROOT:/run/vllm" \
  -v "$CACHE_ROOT:/cache" \
  "$VLLM_DIGEST" \
  vllm serve /models/Qwen3.8-27B-FP8 \
    --served-model-name qwen3.8-27b-fp8 \
    --dtype auto \
    --uds /run/vllm/qwen.sock \
    --gpu-memory-utilization 0.50 \
    --max-model-len 32768 \
    --max-num-seqs 1 \
    --max-num-batched-tokens 8192 \
    --enable-chunked-prefill \
    --limit-mm-per-prompt \
      '{"image":{"count":4,"width":2048,"height":2048},"video":0}' \
    --mm-processor-cache-gb 1 \
    --mm-hasher-algorithm sha256 \
    --reasoning-parser qwen3
```

This uses a bind-mounted Unix-domain socket, so the host can call the service without giving the container a network. Verify every flag against `vllm serve --help` in the frozen image; CLI flags change. Add read-only root filesystem, non-root user, dropped capabilities and `no-new-privileges` only after the exact image works with those controls.

Do not enable a broad local-media path. Put a small, bounded image into the request as a `data:image/...` value through a wrapper that rejects `http`, `https`, `file`, video, excessive pixel counts and oversized bodies. An API key is authentication, not a network boundary.

## A.5 Smoke-test the local API

```bash
curl --fail --silent --show-error \
  --unix-socket "$RUN_ROOT/qwen.sock" \
  http://localhost/v1/models \
  | tee "$RUN_DIR/logs/models.json"

curl --fail --silent --show-error \
  --unix-socket "$RUN_ROOT/qwen.sock" \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "qwen3.8-27b-fp8",
    "messages": [
      {"role": "user", "content": "Reply with exactly: SPARK_SMOKE_OK"}
    ],
    "temperature": 0,
    "max_tokens": 32,
    "chat_template_kwargs": {"enable_thinking": false}
  }' \
  http://localhost/v1/chat/completions \
  | tee "$RUN_DIR/logs/smoke-response.json"
```

This text request proves only text serving. Use a small, locally created test image for the visual gate:

```bash
export SMOKE_IMAGE="$RUN_DIR/input/red-square.png"
export SMOKE_PAYLOAD="$RUN_DIR/input/visual-smoke.json"

test -f "$SMOKE_IMAGE"
SMOKE_DATA_URI="data:image/png;base64,$(base64 -w0 "$SMOKE_IMAGE")"

jq -n --arg image_url "$SMOKE_DATA_URI" '{
  model: "qwen3.8-27b-fp8",
  messages: [{
    role: "user",
    content: [
      {type: "text", text: "State only the colour and shape in this image."},
      {type: "image_url", image_url: {url: $image_url}}
    ]
  }],
  temperature: 0,
  max_tokens: 32,
  chat_template_kwargs: {enable_thinking: false}
}' > "$SMOKE_PAYLOAD"

curl --fail --silent --show-error \
  --unix-socket "$RUN_ROOT/qwen.sock" \
  -H 'Content-Type: application/json' \
  --data-binary "@$SMOKE_PAYLOAD" \
  http://localhost/v1/chat/completions \
  | tee "$RUN_DIR/logs/visual-smoke-response.json"
```

Create `red-square.png` during Phase A and record its hash in the transition bundle. Run the same text and image tests again after the Phase B network-denial controls are active. Never use a public image URL as proof of offline multimodality. In raw HTTP, `chat_template_kwargs` belongs at the request top level; `extra_body` is a Python-client argument and should not be copied into the JSON body.

**Pass:** the socket call succeeds, the correct served model appears, the text response contains the required string, the visual fact is correct, no external connection occurs and no swap moves. Record time to first token, prefill time, decode rate, total time, resident memory and page faults separately.

## A.6 Start local Qdrant with a pinned image

```bash
export QDRANT_IMAGE='<qdrant-image@sha256:digest>'
export QDRANT_DATA="$P42_ROOT/indexes/qdrant"

install -d -m 0750 "$QDRANT_DATA"
docker network inspect p42-internal >/dev/null 2>&1 \
  || docker network create --internal p42-internal

docker run --rm --name p42-qdrant \
  --network=p42-internal \
  -p 127.0.0.1:6333:6333 \
  -v "$QDRANT_DATA:/qdrant/storage" \
  "$QDRANT_IMAGE"
```

In Phase B, apply the approved loopback/firewall configuration. Take a Qdrant snapshot for every headline index and hash it with the corpus/embedding manifest.

## A.7 Build a complete offline wheelhouse

Run inside the tested ARM64 Python/container environment:

```bash
export REQUIREMENTS="$P42_ROOT/configs/requirements.lock"
export WHEELHOUSE="$P42_ROOT/wheels"

python -m pip download \
  --require-hashes \
  --requirement "$REQUIREMENTS" \
  --dest "$WHEELHOUSE"

python -m pip install \
  --dry-run \
  --no-index \
  --require-hashes \
  --find-links "$WHEELHOUSE" \
  --requirement "$REQUIREMENTS"
```

Build and test the final derived container in Phase A. Install under the NVIDIA base image's constraint file, run `pip check`, record Torch/Transformers/vLLM/CUDA versions before and after, then rerun text, image and 32K smoke tests. Export the derived OCI image and pin its digest. Never repair the Phase B service with a live `pip install --upgrade`.

**Pass:** every requirement has a hash; the dry run resolves with no network; `pip check` passes in the derived image; the validated Torch/CUDA stack is unchanged except for pre-approved differences. Source-only packages need a pinned, tested build process or a prebuilt ARM64 wheel.

## A.8 Create transition checksums safely

```bash
export TRANSITION_DIR='<approved-absolute-transfer-directory>'

cd "$TRANSITION_DIR"
find . -type f \
  ! -name 'SHA256SUMS' \
  ! -name 'SHA256SUMS.asc' \
  -print0 \
  | sort -z \
  | xargs -0 sha256sum > SHA256SUMS

sha256sum --check SHA256SUMS
```

The exclusion avoids the self-hashing defect in which rerunning the command changes the very file being checked.

## A.9 Verify a frozen transition bundle after import

```bash
export IMPORT_DIR='<approved-absolute-import-directory>'

cd "$IMPORT_DIR"
sha256sum --check SHA256SUMS \
  | tee verification.log

if grep -Fv ': OK' verification.log; then
  echo 'Verification failed: quarantine the import.' >&2
  exit 1
fi
```

## A.10 Capture a process and resource trace

```bash
export SAMPLE_SECONDS=5
export TRACE_FILE="$RUN_DIR/logs/resource-trace.tsv"

printf 'timestamp\tmem_available_kb\tswap_free_kb\tpgfault\tpgmajfault\tblocks_in_s\tblocks_out_s\n' \
  > "$TRACE_FILE"

while true; do
  timestamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  mem_available="$(awk '/^MemAvailable:/ {print $2}' /proc/meminfo)"
  swap_free="$(awk '/^SwapFree:/ {print $2}' /proc/meminfo)"
  pgfault="$(awk '/^pgfault / {print $2}' /proc/vmstat)"
  pgmajfault="$(awk '/^pgmajfault / {print $2}' /proc/vmstat)"
  vm_line="$(vmstat 1 2 | tail -n 1)"
  blocks_in="$(awk '{print $9}' <<< "$vm_line")"
  blocks_out="$(awk '{print $10}' <<< "$vm_line")"
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$timestamp" "$mem_available" "$swap_free" \
    "$pgfault" "$pgmajfault" "$blocks_in" "$blocks_out" \
    >> "$TRACE_FILE"
  sleep "$SAMPLE_SECONDS"
done
```

Run this in a dedicated controlled session and stop it with `Ctrl+C`. Add process RSS, temperature and service-level timings to the run report. Reject timed/capacity profiles when `SwapFree` falls or major faults show active swapping. NVIDIA documents that ordinary `nvidia-smi` framebuffer-memory reporting is unsupported on the Spark iGPU; do not treat a blank GPU-memory field as free capacity.

# Appendix B — Machine-readable contracts {#contracts}

## B.1 Experiment manifest

```yaml
schema_version: p42kb-experiment-0.9
run_id: 20260821T120000Z-retrieval-pilot
phase: A
purpose: compare hybrid retrieval with and without text reranking
corpus:
  snapshot_id: public-rehearsal-2026-08-21
  manifest_sha256: "<sha256>"
  contains_airbus_data: false
splits:
  development_groups: [PUB-DEV-01]
  calibration_groups: [PUB-CAL-01]
  blind_groups: [PUB-BLIND-01]
platform:
  dgx_os: "<version>"
  cuda: "<version>"
  container_digest: "<name@sha256:digest>"
parser:
  name: docling
  revision: "<commit-or-version>"
  options_sha256: "<sha256>"
retrieval:
  exact_index_snapshot: "<id>"
  sparse_index_snapshot: "<id>"
  dense_index_snapshot: "<id>"
  visual_index_snapshot: null
  graph_snapshot: "<id>"
  dense_model: Qwen/Qwen3-Embedding-0.6B
  dense_revision: "<commit>"
  fusion: rrf
  candidate_limits: {exact: 50, sparse: 50, dense: 50, fused: 50}
  reranker_model: Qwen/Qwen3-Reranker-0.6B
  reranker_revision: "<commit>"
  rerank_limit: 30
  final_evidence_limit: 8
  maximum_graph_hops: 1
generation:
  model: Qwen/Qwen3.8-27B-FP8
  revision: "<commit>"
  served_name: qwen3.8-27b-fp8
  context_limit: 32768
  maximum_images: 4
  maximum_output_tokens: 2048
  reasoning_effort: medium
  temperature: 0
evaluation:
  scorer_revision: "<commit>"
  judge_model: "<local-model-or-none>"
  judge_prompt_sha256: "<sha256-or-none>"
  independence_unit: bundle
  missing_output_policy: fail
security:
  network_state: connected-public-only
  approval_reference: "<reference>"
```

## B.2 Canonical evidence object

```json
{
  "evidence_id": "ICD-009:C:p14:table3:r17",
  "source_sha256": "<sha256>",
  "document_id": "ICD-009",
  "revision": "C",
  "authority": "APPROVED_CURRENT",
  "applicability": ["fictional-programme-A"],
  "language": "en",
  "page": 14,
  "bbox": [82, 214, 512, 694],
  "element_type": "table_row",
  "section_path": ["4 Interfaces", "4.2 Signal mapping"],
  "text": "T17 | J12-4 | ADC12",
  "parent_evidence_id": "ICD-009:C:p14:table3",
  "parser": {
    "name": "docling",
    "revision": "<revision>",
    "observation_id": "<id>"
  },
  "derived": false
}
```

## B.3 Claim/evidence response

```json
{
  "answerability": "PARTIALLY_ANSWERABLE",
  "claims": [
    {
      "claim_id": "CLM-001",
      "claim": "The approved interface assigns T17 to ADC12.",
      "state": "ESTABLISHED",
      "evidence_ids": ["ICD-009:C:p14:table3:r17"],
      "contradicting_evidence_ids": [],
      "calculation": null
    }
  ],
  "conflicts": [],
  "limitations": ["The as-run configuration record is not present."],
  "answer": "The approved mapping is ADC12; the as-run mapping is not established."
}
```

## B.4 Archetype policy object

```json
{
  "archetype_id": "ICD-SIGNAL-MAPPING-1.0",
  "family": "interface_control_document",
  "empirical_basis": {
    "independent_groups": 5,
    "documents": 12,
    "source_snapshot": "<restricted-snapshot-id>"
  },
  "features": [
    {
      "feature_id": "signal_mapping_table",
      "observed_prevalence": {"numerator": 10, "denominator": 12},
      "policy": "CONDITIONAL",
      "condition": "declares_discrete_electrical_interface == true",
      "approved_by": "<role-reference>",
      "validation_rule": "table_has_columns(signal_id, connector_pin, channel_id)"
    }
  ],
  "forbidden_content": ["real_project_identifiers", "copied_source_prose"],
  "approval": {"status": "APPROVED_FOR_RESTRICTED_EVALUATION", "reference": "<id>"}
}
```

## B.5 Fictional truth occurrence

```json
{
  "fact_id": "FACT-T17-MAP",
  "subject": "SIG-T17",
  "predicate": "maps_to_channel",
  "object": "ADC12",
  "unit": null,
  "validity": {"from_revision": "C", "to_revision": null},
  "expected_occurrences": [
    {"document_ast_id": "AST-ICD-009-C", "element_id": "ROW-T17"}
  ],
  "defect_variants": [
    {"variant_id": "DEF-WRONG-CHANNEL", "replacement_object": "ADC13"}
  ]
}
```

## B.6 Factorised synthetic case

Keep these controls independent so one can change without accidentally changing the others:

```yaml
case_id: SYN-T17-0042
world_seed: 184295
truth_graph_revision: 1.2.0
archetype_revision: ICD-SIGNAL-MAPPING-1.0
scenario:
  defect: wrong_channel_mapping
  missing_evidence: as_run_configuration
content_seed: 99142
renderer:
  family: html-engineering-a
  revision: 2.1.0
  visual_seed: 55210
degradation:
  profile: scan-light-skew
  seed: 7731
blind_pool: final-02
```

Identical seeds must reproduce identical bytes. Different seeds should vary allowed structure, style and degradation without changing the intended truth. Variants from the same world are paired technical replicates, not independent evidence of population generalisation.

# Appendix C — Benchmark selection and rights {#benchmark-rights}

::: {.warning}
**Rights reminder.** The table records the research finding at this revision. It is not a legal clearance. Archive the exact licence and terms accepted for every snapshot, and review the underlying documents separately.
:::

## C.1 The six originally requested benchmarks

| Benchmark | What it is useful for | Code/evaluator position | Dataset/document position | v0.9 disposition |
|---|---|---|---|---|
| MMLongBench-Doc-V2 | long visual PDFs, cross-page and unanswerable QA | repository states Apache 2.0 with NOTICE | 134 source PDFs are not redistributed and retain upstream/source rights | **Tier 1 sentinel** on a mapped slice; do not republish the PDF bundle |
| DocBench | raw-PDF QA comparison | no explicit repository licence located at review | no clear blanket dataset/source-document licence | **Not selected by default**; use only after written rights and harness validation |
| OmniDocBench | parser/layout/table/formula/reading-order diagnosis | evaluator repository uses Apache 2.0 | dataset terms state research-only/non-commercial use | **Conditional parser diagnostic**; Airbus legal determination required |
| LongBench v2 | long-text reasoning/truncation | code repository uses MIT | hosted dataset declares Apache 2.0, but contexts may contain third-party works | **Conditional** only when context length is a live decision |
| VRDU | unseen-template structured extraction | evaluator in Google Research is Apache 2.0 | Google Research states datasets in that repository are CC BY 4.0; source PDFs still merit review; standalone repository is archived | **Conditional** extraction diagnostic, not archetype-induction evidence |
| SynthDocBench | controlled chart, layout, length and cross-modal failures | MIT repository | dataset requires its stated terms and “Built with Llama” attribution; generated PDFs incorporate source/generator dependencies | **Tier 1 controlled diagnostic** on a bounded subset; retain all notices |

## C.2 Newer or adjacent research candidates

| Candidate | Why it may help | Why it is not a default |
|---|---|---|
| ViDoRe v2 | visual retrieval, blind-context, long/cross-document and multilingual cases | visual benchmark validity is not Airbus validity; rights and exact snapshot still need review |
| ArXivDoc | compares text, image and interleaved representations for technical/scientific retrieval | research corpus and preprint; not an engineering authority/revision benchmark |
| ViMDoc/HEAVEN | two-stage long multi-document visual retrieval efficiency | new 2026 research implementation; reproduce before relying on it |
| VAREX | reverse-generated structured forms with deterministic truth | single-page typed forms, not engineering bundles |
| DTBench/Table2Doc | truth-first generation from structured tables | table/text-centred and limited layout realism |
| FlexDoc | factorised probabilistic schemas and controlled layouts | business/KIE focus; use ideas rather than assume transfer |
| RIDGE | relation-rich learned layout diversity | stochastic and less auditable; diversity comparator only |
| STELLA | aerospace terminology-sensitive passage retrieval | synthetic queries over public NASA material; no layout/archetype evidence |

## C.3 Rights record fields

For every code, model, dataset, document, font and renderer asset record:

- name and purpose;
- source URL;
- exact revision/commit/digest;
- access date;
- code/model/data/document licence URLs separately;
- copyright/notice obligations;
- commercial/internal/research restrictions;
- derivative-work and redistribution decision;
- third-party content caveat;
- Airbus legal/data-owner reviewer and approval reference;
- Phase A/Phase B use;
- retention and deletion rule.

# Appendix D — Glossary and acronym register {#glossary}

::: {.plain}
**How to use this glossary:** search by the full term or acronym. Definitions describe how this guide uses the term; they are not universal standards definitions.
:::

## D.1 Project and decision terms

| Term | Meaning in this guide |
|---|---|
| Airbus-specific | derived from or evaluated on authorised proprietary Airbus material |
| Connect | bounded synthesis across several evidence items or documents |
| Evidence | source content that supports, contradicts or limits a claim |
| Find | locate a document, identifier or evidence item |
| High-level requirement (HLR) | project-level requirement used to trace the work to an objective |
| PoC | proof of concept: a limited experiment that supports a decision, not a production system |
| P42-KB | the wider engineering knowledge-base project described by the governing repository documents |
| Protected real benchmark | real reviewed questions and evidence that synthetic tuning may not access |
| Redirect | retain useful parts but change the scope or approach |
| Supporting guide | an implementation/evaluation aid subordinate to governing project documents |

## D.2 Document and retrieval terms

| Term | Meaning in this guide |
|---|---|
| Abstract syntax tree (AST) | typed document plan containing sections, elements and relationships before rendering |
| BM25 | a common lexical ranking method based on query terms, term rarity and document length |
| Bounding box | page coordinates locating an element or citation region |
| Canonical document model | the stable internal schema into which different parser outputs are normalised |
| Chunk | a retrieval unit that preserves source, parent and page context |
| Dense embedding | compact numerical representation used for semantic similarity search |
| Document family | documents with a common purpose and structural pattern, such as ICDs or test reports |
| Exact lookup | deterministic matching of a complete identifier or controlled field |
| Hybrid retrieval | combining complementary exact, lexical, dense, visual or relationship searches |
| Interleaved representation | text and images/figures retained in their meaningful order rather than flattening a page to one modality |
| Late interaction | fine-grained query/document vector matching performed at ranking time |
| Layout graph | symbolic links representing reading order, containment and cross-page document structure |
| Lexical search | retrieval based on words or tokens in the query and document |
| Multivector | several vectors for one item, such as token or image-patch vectors |
| Native text layer | machine-readable text already present in a born-digital PDF |
| Normalisation | converting raw parser output into the canonical schema without discarding provenance |
| OCR | optical character recognition: reading characters from pixels |
| Parent/child retrieval | finding a precise child unit while returning enough parent section/table context to understand it |
| Parser | software/model that converts a source document into structured content |
| Reciprocal rank fusion (RRF) | combines ordered result lists using rank rather than incompatible raw scores |
| Reranker | slower, more accurate model that reorders a shortlist for a specific query |
| Sparse vector | mostly-zero term-weight representation used for lexical or learned sparse retrieval |
| VLM | vision-language model: a model that receives visual and textual inputs |

## D.3 Evidence and answer terms

| Term | Meaning in this guide |
|---|---|
| Abstention | deliberate refusal to make a claim when evidence is missing, conflicting or invalid |
| Answerability | whether the available corpus can fully, partly or not answer a question |
| Applicable | valid for the configuration, time, product or case being asked about |
| Authority | approved/current/draft/obsolete/simulated status that affects how evidence may be used |
| Claim | one factual or derived assertion that can be checked separately |
| Claim-level citation | evidence reference attached to the exact claim it supports |
| Complete-evidence recall | whether at least one complete required evidence set survived retrieval |
| Conflict | two applicable evidence items that cannot both be accepted without resolution |
| Faithfulness | whether answer claims follow from the evidence provided to the model |
| Lineage | record of transformations, inputs, versions and approvals producing a derived artefact |
| Provenance | identity and location of the source from which an item came |
| Risk–coverage curve | shows how error risk changes as the system answers more cases rather than abstaining |
| Source of record | authoritative repository/document that remains the governing evidence |
| Supersession | explicit relation stating that a newer item replaces an older one for a scope |

## D.4 Synthetic-corpus terms

| Term | Meaning in this guide |
|---|---|
| Archetype | reviewed reusable description of a document family's structure and variability |
| Canary | unique planted item used to test leakage, contamination or detector behaviour |
| Counterfactual pair | two cases differing in exactly one intended fact or presentation factor |
| Deterministic renderer | same pinned inputs and seed produce the same bytes |
| Empirical prevalence | observed frequency; it does not create an engineering requirement |
| Fictional programme graph | machine-readable shared truth for an invented engineering programme |
| Normative policy | SME-approved rules defining what generated documents must, may or must not contain |
| Renderer family | independently versioned layout/template implementation |
| Scenario policy | rule selecting optional content, missing evidence and seeded defects for a case |
| Seed | recorded value that makes stochastic or varied generation reproducible |
| Synthetic corpus | artificial documents and truth used for evaluation, training or regression—not project authority |
| Truth graph | graph containing the exact fictional facts and relationships from which oracles are derived |

## D.5 Experimental terms

| Term | Meaning in this guide |
|---|---|
| Ablation | comparison that removes or changes one component to measure its contribution |
| Blind set | sealed cases not inspected until the design and thresholds are frozen |
| Calibration set | cases used to choose thresholds or evaluate a judge |
| Development set | visible cases used to improve the system |
| Effect size | magnitude of a difference, not merely whether a threshold was crossed |
| Gold | reviewed reference used for this experiment |
| Holdout | group excluded from development and used for later evaluation |
| Independence unit | unit treated as statistically separate, normally programme, bundle or engineer here |
| Non-inferiority | evidence that a candidate is not worse than a reference by more than a pre-agreed margin |
| Pre-registration | recording hypotheses, comparisons, metrics and rules before final results are seen |
| Prospective/temporal slice | real cases collected later and never used during design, providing stronger external-validity evidence |
| Regression set | previously seen cases used to ensure known behaviour has not returned |
| Sentinel | small diagnostic benchmark used to detect a class of failure |
| Technical replicate | repeated/varied output from the same underlying world or generator; not an independent population sample |

## D.6 Platform, security and governance terms

| Term | Meaning in this guide |
|---|---|
| Air-gapped | approved environment with no external connectivity and tested fail-closed behaviour |
| ARM64 | processor architecture used by the DGX Spark host CPU |
| Container digest | immutable hash identifying exact container content |
| DGX Spark | NVIDIA GB10 system with 128 GB coherent unified memory used as the hard compute constraint |
| FP8 / BF16 / NVFP4 | numerical formats trading memory/throughput against precision; each is a separate configuration |
| Model card | publisher's description of model purpose, limits, licence, data and evaluation |
| Phase A | connected, public-only qualification phase |
| Phase B | offline/air-gapped phase where authorised Airbus material may be processed |
| Reimage | rebuild a machine from an approved trusted operating baseline |
| SBOM | software bill of materials: inventory of software components in a build |
| Threat model | explicit statement of what leakage or attack is being tested and what is outside scope |
| Transition bundle | frozen, reviewed assets moved from connected Phase A into trusted Phase B |
| Unified memory | one memory pool shared by Spark CPU, GPU, OS, models and data |

## D.7 Named tools and benchmarks

| Name | Purpose in this guide |
|---|---|
| ColPali/ColQwen | visual page retrieval using late-interaction representations |
| Docling | local document conversion and structured document representation candidate |
| DocBench | raw-PDF QA benchmark; not a default due rights/harness concerns |
| LongBench v2 | conditional long-text reasoning diagnostic |
| MMLongBench-Doc-V2 | corrected long visual-document QA sentinel |
| NeMo Data Designer | optional synthetic-pipeline orchestration and validation framework |
| Nemotron Parse 2.0 | compact NVIDIA visual document parser candidate |
| OmniDocBench | document parsing evaluation benchmark |
| PaddleOCR-VL | compact visual document parsing challenger |
| Pydantic / JSON Schema | typed validation mechanisms for machine-readable contracts |
| Qdrant | local vector engine supporting dense, sparse and multivector queries |
| Qwen3 Embedding/Reranker | specialist text retrieval and ranking candidate families |
| Qwen3-VL Embedding/Reranker | specialist multimodal retrieval and ranking candidate families |
| Qwen3.8-27B | native multimodal answer/observation candidate, not a selected architecture by default |
| Ragas | RAG metric library used only as a calibrated diagnostic aid |
| RAGChecker | fine-grained RAG diagnostic framework |
| SQLite | lightweight local metadata, exact lookup, relation and experiment store |
| SynthDocBench | controlled synthetic long visual-document diagnostic |
| Typst | candidate independent deterministic document renderer |
| ViDoRe / ViMDoc | visual-document retrieval research benchmarks |
| VRDU | unseen-template structured extraction diagnostic |
| vLLM | local high-throughput model-serving runtime with OpenAI-compatible API |

# Appendix E — Primary research and verification register {#sources}

| Area | Primary source | Decision influenced |
|---|---|---|
| P42-KB scope | [Project Definition v1.0](https://github.com/SilasMoon/p42-KB/blob/2b06a975599e10c0267793944443a98d1da157dd/docs/KB_Project_Project_Definition_and_High_Level_Requirements_v1.0.docx) | real evidence, provenance, maturity ladder and project non-goals |
| P42-KB plan | [PoC Implementation Plan v0.9](https://github.com/SilasMoon/p42-KB/blob/2b06a975599e10c0267793944443a98d1da157dd/docs/KB_Project_PoC_Implementation_Plan_v0.9.docx) | real-first sequence and conditional synthetic scope |
| P42-KB technical concepts | [Candidate Technical Concepts v1.0](https://github.com/SilasMoon/p42-KB/blob/2b06a975599e10c0267793944443a98d1da157dd/docs/KB_Project_Candidate_Technical_Concepts_and_Design_Considerations_v1.0.docx) | hybrid baseline, truth-first synthetic cases and bounded graph |
| Spark hardware | [NVIDIA DGX Spark hardware](https://docs.nvidia.com/dgx/dgx-spark/hardware.html) | ARM64, 128 GB unified memory and 273 GB/s constraint |
| Spark memory reporting | [NVIDIA DGX Spark known issues](https://docs.nvidia.com/dgx/dgx-spark/known-issues.html) | monitor operating-system memory/swap; do not rely on discrete-GPU assumptions |
| Spark serving | [NVIDIA vLLM playbook](https://build.nvidia.com/playbooks/vllm) | supported container-first inference path |
| NVIDIA vLLM 26.07 | [official release notes](https://docs.nvidia.com/deeplearning/frameworks/vllm-release-notes/rel-26-07.html) | version evidence and unified-memory allocation caution; predates Qwen3.8 release |
| Local serving controls | [vLLM serve CLI](https://docs.vllm.ai/en/latest/cli/serve/) | Unix socket, multimodal request and bounded cache/context options |
| Spark model runtime | [NVIDIA Nemotron-on-Spark](https://build.nvidia.com/spark/nemotron) | known-working challenger and staged serving |
| Main candidate | [Qwen3.8-27B-FP8](https://huggingface.co/Qwen/Qwen3.8-27B-FP8) | native VLM, FP8 and vLLM compatibility claim to verify |
| Qwen3.8 runtime challenger | [official SGLang recipe](https://docs.sglang.io/cookbook/autoregressive/Qwen/Qwen3.8-27B) | Phase A performance/compatibility challenger, not automatic Phase B approval |
| Smaller answer control | [Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B) | checks whether 27B quality earns its latency and memory cost |
| Routine visual observer | [Qwen3-VL-2B-Instruct](https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct) | small page/crop observer candidate before 27B escalation |
| Text retrieval | [Qwen3 Embedding report](https://arxiv.org/abs/2506.05176) | 0.6B/4B embedding and reranking bake-off |
| Multimodal retrieval | [Qwen3-VL Embedding report](https://arxiv.org/abs/2601.04720) | 2B visual/mixed retrieval branch |
| Canonical parsing | [Docling](https://docling.org/) and [paper](https://arxiv.org/abs/2408.09869) | typed local conversion baseline |
| PDF/OCR primitives | [pypdfium2](https://github.com/pypdfium2-team/pypdfium2) and [Tesseract](https://tesseract-ocr.github.io/tessdoc/) | lightweight native rendering/text and selective scan OCR controls |
| Visual parsing | [Nemotron Parse 2.0](https://huggingface.co/nvidia/NVIDIA-Nemotron-Parse-2.0) | compact Blackwell-compatible fallback candidate |
| Parser challenger | [PaddleOCR-VL-1.5](https://arxiv.org/abs/2601.21957) | compact corpus bake-off challenger |
| Parser benchmark | [OmniDocBench](https://github.com/opendatalab/OmniDocBench) | component parsing diagnosis, not project acceptance |
| Visual retrieval | [ColPali](https://openreview.net/forum?id=ogjBpZ8uSi) | preserve a visual retrieval path |
| Representation caution | [Document-as-Image Representations Fall Short](https://arxiv.org/abs/2604.18508) | do not replace structured text with screenshots |
| Layout/dynamic retrieval | [LAD-RAG](https://aclanthology.org/2026.acl-long.724/) | layout graph and dynamic evidence acquisition |
| Semantic regions | [SCAN](https://aclanthology.org/2026.findings-eacl.82/) | coherent layout regions instead of arbitrary fragments |
| Two-stage visual retrieval | [HEAVEN](https://aclanthology.org/2026.findings-acl.54/) | fast candidate stage followed by precise reranking |
| Local hybrid store | [Qdrant hybrid queries](https://qdrant.tech/documentation/search/hybrid-queries/) | RRF and multi-stage local retrieval |
| Graph comparison | [Microsoft GraphRAG](https://microsoft.github.io/graphrag/) | defer full automatic GraphRAG; retain bounded source-backed relations |
| Synthetic orchestration | [NeMo Data Designer](https://docs.nvidia.com/nemo/datadesigner/getting-started/welcome) | staged, typed and validated generation workflow |
| Long-document synthetic workflow | [NVIDIA iterative SDG story](https://docs.nvidia.com/nemo/datadesigner/dev-notes/vlm-long-document-understanding) | separate generation streams and independent filtering |
| Controlled synthetic documents | [SynthDocBench](https://github.com/ServiceNow/SynthDocBench) | structured hidden truth and factor-controlled diagnostics |
| Fine-grained RAG evaluation | [RAGChecker](https://github.com/amazon-science/RAGChecker) | diagnose retrieval and generation separately |
| RAG metrics | [Ragas metrics](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/) | secondary calibrated diagnostics |
| Synthetic/privacy caution | [NIST SP 800-226](https://doi.org/10.6028/NIST.SP.800-226) | no broad privacy/declassification claim from synthetic output |
| Controlled combinations | [NIST ACTS](https://csrc.nist.gov/projects/automated-combinatorial-testing-for-software/downloadable-tools) | optional pairwise/t-way scenario coverage, not representativeness |
| Schema standard | [JSON Schema 2020-12](https://json-schema.org/draft/2020-12) | optional formal AST/manifest validation |
| Graph constraints | [W3C SHACL](https://www.w3.org/TR/shacl/) | optional truth/evidence graph validation |
| Provenance vocabulary | [W3C PROV-O](https://www.w3.org/TR/prov-o/) | optional interoperable lineage model |
| MMLongBench-Doc-V2 | [official repository](https://github.com/VectifyAI/MMLongBench-Doc-V2) | corrected sentinel and PDF redistribution caution |
| LongBench v2 | [official repository](https://github.com/THUDM/LongBench) | conditional text-context diagnostic |
| VRDU | [official archived dataset](https://github.com/google-research-datasets/vrdu) | unseen-template extraction only |

# Appendix F — What changed and what remains uncertain {#revision}

## F.1 Material changes from v0.8

- Replaced the binary “direct visual vs parsed visual” framing with a three-path cascade: structured text/layout + exact/hybrid retrieval + selective visual retrieval.
- Made Qwen3.8-27B-FP8 a primary **candidate**, not a preselected architecture.
- Added compact specialist parser, embedding, reranking and multimodal retrieval candidates appropriate to one Spark.
- Added staged model-residency profiles and a conservative 32K initial context.
- Named a concrete local baseline: Docling/canonical schema, SQLite, Qdrant, Qwen retrieval models and a bounded relation graph.
- Added claim/evidence machine contracts, complete-evidence recall, authority errors, citation completeness and risk–coverage.
- Retained truth graph + typed AST + deterministic renderer, while requiring deterministic-per-seed variation, independent renderers and factor separation.
- Removed DocBench from the default portfolio and made every public benchmark decision-contingent.
- Added an untouched temporal/prospective real slice and stronger generator-level statistical cautions.
- Separated confidentiality leakage, identity/privacy concerns and public-benchmark contamination.
- Reorganised the full guide around plain-language introductions, one running example, analogies, “why/done” operator steps and a searchable glossary.

## F.2 Known limitations

- No published benchmark exactly measures induction of Airbus engineering document-family archetypes and coherent multi-document reconstruction. This is a defensible custom strategy informed by adjacent research, not an established standard.
- Model and parser benchmark results are publisher/author results on public datasets. They do not select the P42-KB winner.
- Qwen3.8 and Nemotron Parse 2.0 are very recent releases. ARM64/Blackwell runtime stability must be proven on the frozen Spark image.
- The memory envelope is an estimate. Actual context, image, concurrency and index budgets need telemetry from the target unit.
- Public benchmark and model terms can change. The rights register must be refreshed at each snapshot.
- Synthetic variants from one generator are not independent samples of the Airbus document population.
- “No detected leakage” means only that the declared tests passed. It does not prove declassification, anonymity or immunity to future attacks.
- The final production KB architecture belongs in the P42-KB architecture/design artefact. This guide defines a reference profile sufficient to evaluate synthetic utility without taking ownership of the master architecture.
