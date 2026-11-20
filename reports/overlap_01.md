# Overlap assessment (gate G1), 2026-11-20

Outcome: **UNRESOLVED**

- not yet confirmed from the PDF: correia_2601.22240, geng_cmc_2026, hashemi_2606.31639, hong_2510.15476, ji_2511.15203, mourad_electronics_2026, sammartino_kbs_2026, secfid_2606.30783, wang_2602.10453

| id | kind | a: source axis | b: three jobs | c: layout rule | confirmed | read basis |
|---|---|---|---|---|---|---|
| correia_2601.22240 | survey | partial | no | no | no | full PDF (research pass, 19 Nov 2026) |
| geng_cmc_2026 | survey | partial | unknown | unknown | no | journal page (19 Nov 2026) |
| hashemi_2606.31639 | survey | no | no | partial | no | full PDF (research pass, 19 Nov 2026) |
| hong_2510.15476 | sok | partial | no | partial | no | arXiv abstract page and v3 HTML snippets (19 Nov 2026) |
| ji_2511.15203 | sok | partial | no | no | no | full PDF (research pass, 19 Nov 2026) |
| mourad_electronics_2026 | survey | partial | unknown | unknown | no | MDPI landing page (19 Nov 2026) |
| sammartino_kbs_2026 | survey | unknown | unknown | unknown | no | journal abstract page (19 Nov 2026) |
| secfid_2606.30783 | benchmark | no | partial | no | no | full PDF (research pass, 19 Nov 2026) |
| wang_2602.10453 | sok | partial | no | no | no | full PDF (research pass, 19 Nov 2026) |

## correia_2601.22240: A Systematic Literature Review on LLM Defenses Against Prompt Injection and Jailbreaking: Expanding NIST Taxonomy

- **scope**: Systematic literature review of LLM defences against prompt injection and jailbreaking; 88 studies to August 2025.
- **corpus cutoff**: August 2025
- **organising dimensions**: NIST-based tree: training-time interventions; deployment-time interventions (prompt instruction and formatting, input modification, aggregation, model-level mitigations such as decoding steering and defensive pruning, detection, monitoring); indirect mitigations.
- **treatment user task**: ASR is the main metric; some studies also report performance; trade-offs often not reported (p. 15).
- **treatment document handling**: Not treated.
- **treatment comparability**: RQ3 asks whether results are comparable; Section 6.2 names dataset splits, model variants and temperature; prompt layout is not among the factors.
- **evidence granularity**: Catalogue with model, attack dataset, code and model-agnosticism per study (Table 3).
- **what this review adds**: The inference-time signal axis separated from the training axis; R2 and R3; layout as a condition; grades.
- **pages**: a ; b ; c 

## geng_cmc_2026: Prompt Injection Attacks on Large Language Models: A Survey of Attack Methods, Root Causes, and Defense Strategies

- **scope**: Survey of prompt injection attack methods, root causes and defences; 128 studies 2022 to 2025.
- **corpus cutoff**: 2025
- **organising dimensions**: Attacks by vector, objective and implementation; defences in three groups (input filtering, system architecture, model level); root causes at philosophical, architectural and training levels.
- **treatment user task**: unknown (PDF not yet read)
- **treatment document handling**: unknown (PDF not yet read)
- **treatment comparability**: unknown (PDF not yet read)
- **evidence granularity**: unknown (PDF not yet read)
- **what this review adds**: to fill after reading
- **pages**: a ; b ; c 

## hashemi_2606.31639: A Lifecycle and Application-Stack Survey of Large Language Model Vulnerabilities: Attacks, Risks, Defenses, and Open Problems

- **scope**: Lifecycle and application-stack survey of LLM vulnerabilities; systematisation rather than exhaustive bibliometrics.
- **corpus cutoff**: mid 2026 (to confirm)
- **organising dimensions**: Defence-in-depth: deterministic controls; model-level and prompt-level controls; retrieval and memory controls; tool and agent controls; monitoring, red teaming, governance.
- **treatment user task**: No numbers reported.
- **treatment document handling**: Not treated.
- **treatment comparability**: A reporting checklist (Table 5) lists context construction including delimiters and templates as items to report; not a comparability condition.
- **evidence granularity**: Narrative; no extracted evidence tables.
- **what this review adds**: Measured coverage of the three jobs; graded comparisons; the card as a filled artefact.
- **pages**: a ; b ; c 

## hong_2510.15476: SoK: Systematizing LLM Prompt Security: Taxonomies, Datasets, and Unified Evaluation of Attacks and Defenses

- **scope**: SoK of LLM prompt security, jailbreak-centred; 272 studies; three taxonomies; unified evaluation.
- **corpus cutoff**: 2025 (v4 October 2026; to confirm)
- **organising dimensions**: Taxonomies of attacks, defences (by goal and methodology; a defence decision layer of input, output, internal state or prompt policy) and vulnerabilities; an evaluation protocol over model, access setting, attack, defence, sample and judge.
- **treatment user task**: Not as its own quantity (to confirm).
- **treatment document handling**: Not treated (jailbreak setting).
- **treatment comparability**: Configuration-aware reporting over the tuple; prompt layout is not in the tuple.
- **evidence granularity**: 11 models, 20 attacks, 9 defences, 3 judges under one protocol.
- **what this review adds**: Indirect injection as the subject; the signal axis; R2 and R3; layout as a condition.
- **pages**: a ; b ; c 

## ji_2511.15203: Taxonomy, Evaluation and Exploitation of IPI-Centric LLM Agent Defense Frameworks

- **scope**: Defence frameworks for indirect prompt injection in LLM agents.
- **corpus cutoff**: late 2025 (to confirm)
- **organising dimensions**: Five dimensions: technical paradigm, intervention stage, model access, explainability, automation level.
- **treatment user task**: Utility on AgentDojo (task success) for nine frameworks; not the user's instruction as its own quantity.
- **treatment document handling**: Not measured.
- **treatment comparability**: Prompt templates and delimiters appear as implementation details; no comparability condition.
- **evidence granularity**: ASR and utility for nine frameworks under three adaptive attacks; Meta-SecAlign the only training defence.
- **what this review adds**: Model-side defences as the subject; the two axes; R2 and R3; grades.
- **pages**: a ; b ; c 

## mourad_electronics_2026: Securing the Prompt Pipeline: A Systematic Review of Defense Mechanisms Against Prompt-Based Attacks in LLM Agents

- **scope**: Systematic review of defence mechanisms against prompt-based attacks in LLM agents; 19 studies.
- **corpus cutoff**: to confirm from the PDF
- **organising dimensions**: Pipeline stage (prompt, model, pipeline; Section 1.1); system architecture (single-LLM, multi-agent); technical approach (ML-based, rule-based, hybrid).
- **treatment user task**: unknown (PDF not yet read)
- **treatment document handling**: unknown (PDF not yet read)
- **treatment comparability**: unknown (PDF not yet read)
- **evidence granularity**: unknown (PDF not yet read)
- **what this review adds**: to fill after reading
- **pages**: a ; b ; c 

## sammartino_kbs_2026: Vulnerabilities in autonomous execution: A survey of security threats and defenses in LLM-driven agentic and multi-agent systems

- **scope**: PRISMA-informed review of threats and defences in LLM-driven agentic and multi-agent systems, 2023 to early 2026.
- **corpus cutoff**: early 2026
- **organising dimensions**: Threats by entry point, propagation path and target asset; four threat families; five defence categories mapped to threats.
- **treatment user task**: unknown (full text paywalled)
- **treatment document handling**: unknown (full text paywalled)
- **treatment comparability**: Defences assessed for adaptive-attack resistance, cost and residual risk (abstract); layout not mentioned in the abstract.
- **evidence granularity**: unknown (full text paywalled)
- **what this review adds**: to fill after reading
- **pages**: a ; b ; c 

## secfid_2606.30783: Security-Fidelity Tradeoffs: The Hidden Cost of Prompt Injection Defense

- **scope**: Benchmark, not a survey: security and fidelity measured together for four defences on three bases; 1,168 instances.
- **corpus cutoff**: not applicable
- **organising dimensions**: Outcomes executed, processed, ignored, other; fidelity as one minus the ignored rate (non-suppression); safe processing as processed and not executed.
- **treatment user task**: Not measured separately.
- **treatment document handling**: Measured: non-suppression and safe processing on translation, editing, extraction and counting.
- **treatment comparability**: Each defence run with its own specified inference procedure (Appendix B.1).
- **evidence granularity**: Per defence and base model: security and fidelity percentages.
- **what this review adds**: SecFid is the source of the R3 definitions and of published pairs; the review places its numbers on the map with their layouts.
- **pages**: a ; b ; c 

## wang_2602.10453: The Landscape of Prompt Injection Threats in LLM Agents: From Taxonomy to Analysis

- **scope**: Prompt-injection threats and defences in LLM agents; 78 papers; defences by the stage at which they act.
- **corpus cutoff**: early 2026 (to confirm from the PDF)
- **organising dimensions**: Attacks by payload generation. Defences by stage: text level (detection filters, prompt enhancement), model level (model alignment by task, preference or format; internal-representation detectors), execution level (task alignment, access control, isolation).
- **treatment user task**: Utility without attack as a general score on AgentPI; not the user's instruction under attack as its own quantity.
- **treatment document handling**: Not measured. The paper finds that defences look good by suppressing contextual inputs, which is the symptom.
- **treatment comparability**: Prompt-structure changes counted as a compatibility cost; layout not treated as a condition for comparing numbers.
- **evidence granularity**: Benchmark results (ASR, utility, time, tokens) for eight text- and execution-level defences; no model-level defence run.
- **what this review adds**: Finer first axis with no-signal as a value; signal dependence; R2 and R3 coverage; evidence grades for comparisons.
- **pages**: a ; b ; c 
