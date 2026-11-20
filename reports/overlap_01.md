# Overlap assessment (gate G1), 2026-11-20

Outcome: **SUPPORTED**

- no confirmed form answers yes to any of the three questions
- partial overlaps to be named in the related-work table: correia_2601.22240 (a_source_axis, c_equal_layout_rule); geng_cmc_2026 (a_source_axis, c_equal_layout_rule); hashemi_2606.31639 (a_source_axis, c_equal_layout_rule); hong_2510.15476 (a_source_axis, b_three_jobs_together, c_equal_layout_rule); ji_2511.15203 (a_source_axis, c_equal_layout_rule); mourad_electronics_2026 (a_source_axis, c_equal_layout_rule); sammartino_kbs_2026 (a_source_axis, b_three_jobs_together, c_equal_layout_rule); secfid_2606.30783 (b_three_jobs_together); wang_2602.10453 (a_source_axis, c_equal_layout_rule)

## How the three questions were graded

**a_source_axis**: organises defences by how the model is shown where the instruction came from.
- yes: an axis whose values are forms of the source signal (chat roles, delimiters or markers, encodings, learned tokens or embeddings, position, no signal)
- partial: defences are grouped by where they act or where the attack enters (a stage, level or component axis), or signal forms appear as scattered categories but not as one axis
- no: neither

**b_three_jobs_together**: reports security, the user's task and document handling together, per defence.
- yes: security, the user's task and the handling of the document content reported together per defence
- partial: two of the three reported together per defence, or their joint reporting measured as coverage
- no: security alone, or utility discussed in prose or recommended but not extracted per defence

**c_equal_layout_rule**: states or applies a rule that numbers are comparable only in the same prompt layout.
- yes: the prompt layout (template, roles, delimiters) is named as a condition for comparing numbers
- partial: a comparability condition or reporting standard is stated or applied (model, benchmark, attacker, judge, decoding) but the layout is not among its items, or the layout is named only as a reporting item
- no: no comparability condition

Pages are 1-based page indices of the PDF in `data/surveys/`; each page was located by searching the PDF text for the anchor phrase recorded in the form (`verification` field).

| id | kind | a: source axis | b: three jobs | c: layout rule | pages a / b / c | confirmed | read basis |
|---|---|---|---|---|---|---|---|
| correia_2601.22240 | survey | partial | no | partial | 9 / 15 / 16 | yes | full PDF text, arXiv 2601.22240 (latest version on 20 Nov 2026), 27 pages, read 20 Nov 2026 |
| geng_cmc_2026 | survey | partial | no | partial | 28 / 33 / 41 | yes | full PDF, Computers, Materials & Continua 87(1), 52 pages, read 20 Nov 2026 |
| hashemi_2606.31639 | survey | partial | no | partial | 9 / 10 / 12 | yes | full PDF text, arXiv 2606.31639 (latest version on 20 Nov 2026), 19 pages, read 20 Nov 2026 |
| hong_2510.15476 | sok | partial | partial | partial | 4 / 12 / 7 | yes | full PDF text, arXiv 2510.15476 (latest version on 20 Nov 2026); page numbers located by anchor search, read 20 Nov 2026 |
| ji_2511.15203 | sok | partial | no | partial | 4 / 9 / 8 | yes | full PDF text, arXiv 2511.15203 (latest version on 20 Nov 2026); page numbers located by anchor search, read 20 Nov 2026 |
| mourad_electronics_2026 | survey | partial | no | partial | 11 / 12 / 14 | yes | full PDF, Electronics 15(16):3700, 27 pages, read 20 Nov 2026 |
| sammartino_kbs_2026 | survey | partial | partial | partial | 14 / 17 / 21 | yes | full PDF, Knowledge-Based Systems 352 (2026) 117001, 25 pages, read 20 Nov 2026 |
| secfid_2606.30783 | benchmark | no | partial | no | 9 / 4 / 24 | yes | full PDF text, arXiv 2606.30783 (latest version on 20 Nov 2026); page numbers located by anchor search, read 20 Nov 2026 |
| wang_2602.10453 | sok | partial | no | partial | 7 / 12 / 10 | yes | full PDF text, arXiv 2602.10453 (latest version on 20 Nov 2026), 20 pages, read 20 Nov 2026 |

## correia_2601.22240: A Systematic Literature Review on LLM Defenses Against Prompt Injection and Jailbreaking: Expanding NIST Taxonomy

- **scope**: Systematic literature review of LLM defences against prompt injection and jailbreaking, extending the NIST taxonomy; 88 primary studies from Scopus; states it was submitted to Computer Science Review (p. 1, p. 6).
- **corpus cutoff**: August 2025 (p. 6)
- **organising dimensions**: Training-time interventions (post-training, pre-training); deployment-time interventions (prompt instruction and formatting, input modification, aggregation, prompt-stealing prevention, model-level mitigations, detection and termination, monitoring, usage restrictions); indirect mitigations; mitigations against indirect prompt injection; evaluation-time interventions (Figure 1, p. 2; Sections 5.1-5.5). Delimiters sit under prompt instruction and formatting (p. 9); instruction hierarchy in embeddings and spotlighting under indirect-injection mitigations (p. 14).
- **treatment user task**: Not extracted. The catalogue columns are method, description, model-agnostic, attack mitigation (mostly ASR, occasionally a false-positive value), attack, source code (Tables A.5-A.11). States that many works do not report trade-offs such as overall performance degradation (p. 15).
- **treatment document handling**: Not treated beyond row descriptions.
- **treatment comparability**: RQ3 asks whether results are comparable (p. 2). The answer names dataset splits, model variants and parameters such as temperature as what prevents comparison (pp. 15-16). Layout or template is not named.
- **evidence granularity**: Per study catalogue rows (Tables A.5-A.11) with ASR where reported; no cross-study numbers.
- **what this review adds**: The signal axis separated from the training axis (this paper's top split is training-time versus deployment-time, a coarse form of the second axis only); the three requirements per defence; layout added to the comparability factors; graded comparisons.
- **a_source_axis** = partial; p.9: "Enclosing queries within random characters or XML"
- **b_three_jobs_together** = no; p.15: "Many works do not report trade-offs such as overall performance degradation"
- **c_equal_layout_rule** = partial; p.16: "dataset splits, model variants, and parameters like temperature"
- **verification**: a: p.9 ok; b: p.15 ok; c: p.16 ok; sha256 6cca48951f7d

## geng_cmc_2026: Prompt Injection Attacks on Large Language Models: A Survey of Attack Methods, Root Causes, and Defense Strategies

- **scope**: Kitchenham-style systematic review of prompt injection attacks, root causes and defences; 128 studies 2022-2025; 37 defence studies tabulated (abstract, p. 1; Table 6, pp. 28-30).
- **corpus cutoff**: 2025 (p. 1, p. 28)
- **organising dimensions**: Attacks by vector, objective and implementation (Section 3). Root causes at philosophical, technical and training levels (Section 4). Defences in three categories: input preprocessing and filtering, system architecture, model-level (Section 5, p. 28). Spotlighting, DefensiveToken, StruQ, SecAlign are placed in these categories by where they act, not by how the source is shown.
- **treatment user task**: Not extracted. Table 7 (p. 33) lists baseline ASR and ASR with defence only, for seven defences on different benchmarks and models. A unified evaluation framework is recommended with three dimensions: security (ASR), efficiency, usability (false positive rate, task completion accuracy) (Section 6.3, pp. 41-42).
- **treatment document handling**: Not treated.
- **treatment comparability**: States that studies use varying datasets, metrics and settings, giving incomparable results (p. 41), yet Table 7 (p. 33) places ASR figures from different benchmarks and models side by side. Layout is not named.
- **evidence granularity**: Per defence: year, category, authors, one-line strategy (Table 6); ASR before and after for seven defences (Table 7); datasets and metrics (Table 9).
- **what this review adds**: The signal axis; measurement coverage of the three requirements per defence; comparisons admitted only with a grade, which would mark Table 7's juxtaposition as not comparable; the layout condition.
- **a_source_axis** = partial; p.28: "Input Preprocessing and Filtering, System Architecture Defenses, and Model-Level Defenses"
- **b_three_jobs_together** = no; p.33: "Quantitative comparison of defense mechanism effectiveness"
- **c_equal_layout_rule** = partial; p.41: "leading to inconsistent and sometimes incomparable results"
- **verification**: a: p.28 ok; b: p.33 ok; c: p.41 ok; sha256 2ebcaf320118

## hashemi_2606.31639: A Lifecycle and Application-Stack Survey of Large Language Model Vulnerabilities: Attacks, Risks, Defenses, and Open Problems

- **scope**: Lifecycle and application-stack survey of LLM vulnerabilities; systematisation from seed papers and citation chasing, cross-checked against OWASP, MITRE ATLAS and NIST; no paper count or search dates (Section 2.2, p. 2).
- **corpus cutoff**: not stated; arXiv v1 30 June 2026
- **organising dimensions**: Attacks by lifecycle stage and application stack (Section 3). Defences in a defence-in-depth architecture: deterministic controls; model-level and prompt-level controls; retrieval and memory controls; tool and agent controls; monitoring, red teaming and governance (Section 6, pp. 9-10). Delimiters, role labels and instruction hierarchy are listed as examples of prompt-level controls, not as an axis.
- **treatment user task**: Named as metrics to report (clean-task accuracy, user-task utility; Section 7, p. 10); no numbers for any defence.
- **treatment document handling**: Named as a design goal: a model should read untrusted content for information without letting it change goals (Section 9, p. 13); not measured.
- **treatment comparability**: A reporting checklist (Table 5, p. 12) includes context construction: system prompt, retrieved documents, memory policy, delimiters, tool schemas, with the rationale that it is critical for prompt-injection and RAG studies. It is a reporting item; no rule says numbers are comparable only under the same layout.
- **evidence granularity**: Narrative with reference tables; no extracted per-defence evidence.
- **what this review adds**: Filled records rather than a checklist: the signal axis, per-defence coverage of the three requirements, layout as a comparison condition with graded comparisons, and the defence card. This paper's Table 5 is the nearest prior naming of delimiters and templates as something to report.
- **a_source_axis** = partial; p.9: "system prompts, instruction hierarchy, delimiters, reminders about untrusted content"
- **b_three_jobs_together** = no; p.10: "clean-task accuracy"
- **c_equal_layout_rule** = partial; p.12: "critical for prompt-injection and RAG studies"
- **verification**: a: p.9 ok; b: p.10 ok; c: p.12 ok; sha256 87b8c6c9be81

## hong_2510.15476: SoK: Systematizing LLM Prompt Security: Taxonomies, Datasets, and Unified Evaluation of Attacks and Defenses

- **scope**: SoK of LLM prompt security centred on jailbreaks: 272 papers, collection last updated May 2026; three taxonomies and a unified evaluation platform (Sections 1, 2.1, 3). States that it focuses on textual jailbreak attacks and defences (Section 1); the platform supports single-turn interactions only (Section 3.2).
- **corpus cutoff**: May 2026 (Section 2.1); arXiv v6 read
- **organising dimensions**: Defence taxonomy by goal (detection, mitigation), then intervention point (input, output, inner state; input processing, model training, model-side intervention, output processing), then operation (Section 2.5, Figure 2). Prompt modification (provenance marking, delimiting, paraphrasing) is one technique group under input processing (p. 4); safety prompts with optimised embeddings sit beside it. No axis over signal forms.
- **treatment user task**: Per defence under one protocol: ASR, defence gain, sample-wise transitions (Table 2, Section 4.1); benign utility on MMLU, TruthfulQA, FollowBench, IFEval and refusal rate, with over-refusal relative to no defence (Section 4.4). This is general capability without attack, not the user's task under attack.
- **treatment document handling**: Not measured; the evaluated attacks are direct harmful queries, not instructions carried in documents or tool outputs.
- **treatment comparability**: States that two results are directly comparable only when component identities and relevant settings match, over the tuple model, attack, defence, dataset, judge plus decoding, assistant models, budgets, thresholds, judge rubrics and parsing rules (Section 3.1). The strongest comparability rule among the surveys; the prompt layout is not a listed element.
- **evidence granularity**: 11 models, 20 attacks, 9 defences, 3 judges run under one protocol with audit logs.
- **what this review adds**: Indirect injection as the subject; the signal axis; the user's task under attack and document handling; the layout condition added to a comparability rule that this paper already states for model, attack, dataset, judge and decoding; grades for published comparisons instead of a re-run.
- **a_source_axis** = partial; p.4: "Prompt Modification rewrites or constrains prompts"
- **b_three_jobs_together** = partial; p.12: "defense-induced over-refusal relative to no_defense"
- **c_equal_layout_rule** = partial; p.7: "Two results are directly comparable only when both component identities and relevant settings match"
- **verification**: a: p.4 ok; b: p.12 ok; c: p.7 ok; sha256 639d8ba358c9

## ji_2511.15203: Taxonomy, Evaluation and Exploitation of IPI-Centric LLM Agent Defense Frameworks

- **scope**: Taxonomy, evaluation and exploitation of defence frameworks for indirect prompt injection in LLM agents; 26 frameworks in the taxonomy (Table 1), nine evaluated (Section 4).
- **corpus cutoff**: arXiv v1 19 November 2025; no search window stated
- **organising dimensions**: Five dimensions: technical paradigm (detection, prompt engineering, fine-tuning, system design, runtime checking, policy enforcing), intervention stage, model access, explainability, automation level (Section 3, Table 1). Delimiters, hash tags and defensive tokens are described inside the prompt-engineering paradigm, not as a dimension.
- **treatment user task**: Utility measured as the proportion of user-specified tasks completed in AgentDojo without attack (Section 4.1, Table 3); false positives (Appendix B); time and tokens (Table 3). Utility under attack is not measured.
- **treatment document handling**: Not measured.
- **treatment comparability**: Configurations standardised across benchmarks and frameworks: GPT-4o backend, temperature 0, OpenAI function-calling template (Section 4); fine-tuned frameworks run on Llama-3.1-8B instead, and frameworks needing manual configuration are run on their automated parts only. An applied equal-conditions rule for the backbone and tool template; each framework's own prompt layout is not held equal and is not described.
- **evidence granularity**: Per framework: ASR on AgentDojo, ASB and InjecAgent under benchmark and adaptive attacks (Table 2); utility, false positives, cost (Table 3, Table 8).
- **what this review adds**: Model-side defences as the subject (this paper runs one trained defence, on a different model from the rest); the two axes; the user's task under attack and document handling; the layout condition made explicit; graded comparisons rather than one platform's run.
- **a_source_axis** = partial; p.4: "unpredictable data delimiters"
- **b_three_jobs_together** = no; p.9: "the proportion of user-specified tasks completed in the AgentDojo benchmark"
- **c_equal_layout_rule** = partial; p.8: "we standardize the configurations across all benchmarks and defense frameworks"
- **verification**: a: p.4 ok; b: p.9 ok; c: p.8 ok; sha256 ada6210f63d4

## mourad_electronics_2026: Securing the Prompt Pipeline: A Systematic Review of Defense Mechanisms Against Prompt-Based Attacks in LLM Agents

- **scope**: Systematic review of defence mechanisms against prompt-based attacks (jailbreak, direct and indirect injection) in LLMs and LLM agents; 19 studies from ACM and IEEE, 2023-2025 (Figure 2, p. 6; Table 2, p. 8).
- **corpus cutoff**: 2025 (inclusion criterion I3, p. 8)
- **organising dimensions**: System architecture (single-LLM, multi-agent); defence methodology (ML-based, rule-based, hybrid); pipeline stage at which the defence applies (prompt-, model-, pipeline-level) (Section 1.1, p. 3; Section 6, p. 12; RQ6, p. 11). Entry sources of malicious text are an attack question (RQ2, p. 11). Fixed delimiters and guardrail text appear as one rule-based technique (RQ7, p. 11).
- **treatment user task**: Listed among reported metrics in prose: latency, throughput and task accuracy degradation (RQ9, p. 12); a trade-off paragraph (Section 8.2, p. 23); a recommendation to report ASR alongside a utility metric (Section 8.3, p. 24). Not extracted per study.
- **treatment document handling**: Not treated.
- **treatment comparability**: States that reported attack success rates are not directly comparable across studies because of differing datasets, threat models and reporting conventions, and declines to build a unified comparison table (p. 14). Layout or template is not named.
- **evidence granularity**: Per study: attack type, defence, dataset, metrics, architecture (Tables 6 and 7); quality scores (Table 5). No numbers compared across studies.
- **what this review adds**: A corpus of model-side defences against indirect injection (this paper's 19 studies are mostly jailbreak detectors); the two axes; per-defence measurement coverage of the three requirements; the layout condition and graded comparisons in place of a refusal to compare.
- **a_source_axis** = partial; p.11: "fixed delimiters or guardrail text that separate system instructions from user input"
- **b_three_jobs_together** = no; p.12: "Utility-related metrics such as latency, throughput, and task accuracy degradation"
- **c_equal_layout_rule** = partial; p.14: "not directly comparable across studies because of differing datasets, threat models"
- **verification**: a: p.11 ok; b: p.12 ok; c: p.14 ok; sha256 7eb9d98248fa

## sammartino_kbs_2026: Vulnerabilities in autonomous execution: A survey of security threats and defenses in LLM-driven agentic and multi-agent systems

- **scope**: PRISMA-informed review of attacks and defences in LLM-driven agentic and multi-agent systems; 102-paper corpus (44 attack papers, 31 defence papers); window 1 January 2023 to 31 January 2026 (p. 4, p. 7).
- **corpus cutoff**: 31 January 2026 (search closed; p. 7, p. 21)
- **organising dimensions**: Threats by entry point, propagation path and target asset (Section 4, pp. 7-9). Defences in five families ordered by the taxonomy dimension they act on: detection and filtering; structural separation of instructions and data (StruQ, SecAlign, Jatmo, spotlighting in one family); execution isolation and least privilege; information-flow control; alignment-side and multi-agent hardening (Section 8, pp. 13-17). A defence-to-threat coverage map graded by evidence type: containment argument, empirical reduction, principled extension, not addressed (Section 8.1 and Table 4, pp. 13 and 18).
- **treatment user task**: Security and the user's task together is the paper's main methodological point: ASR reported alone is called uninterpretable and the joint (ASR, utility) point is called the only result (Section 9.2, p. 17). Pairing is measured as coverage: 25 of 44 attack papers and 12 of 31 defence papers report no benign-utility measurement (quality item Q3, p. 5; Table 3, pp. 15-16); Table 5 carries a utility-cost column per family (p. 19). The user's task under attack is not separated from clean utility.
- **treatment document handling**: Not measured. Whether a defended model still reads the untrusted content is not among the quality items, the tables or the reporting standard.
- **treatment comparability**: Section 9.3 names threat-model incommensurability (attacker capability, defender scope). The reporting standard of Section 11.7 (p. 21) asks for attacker capability, defender scope, paired (ASR, utility), adaptivity, judge, cost, taxonomic coordinates, a reproducibility block (checkpoint, decoding, seeds, runs) and residual risk. The prompt layout or template is not an item.
- **evidence granularity**: Per attack paper: ASR as reported, paired utility (value, per-configuration or not reported), models, environment (Table 3). Per defence family, not per defence: adaptive resistance, utility cost, deployment cost, residual risk, evidence grade (Table 5). No per-defence numbers are extracted.
- **what this review adds**: Model-side defences at the level of individual defences rather than families; the signal axis with its no-signal value; the user's task measured under attack and the document-handling requirement, which this paper does not have; the prompt layout as a comparison condition added to a reporting list that already has checkpoint, decoding, judge and attacker; and an evidence grade for each pairwise comparison rather than for each family-threat cell. This paper's utility-trap argument and Q3 coverage count are the closest prior statement of the pairing requirement and must be cited as such.
- **a_source_axis** = partial; p.14: "structural separation of instructions and data"
- **b_three_jobs_together** = partial; p.17: "Reported alone, ASR is uninterpretable"
- **c_equal_layout_rule** = partial; p.21: "Defender scope. What the defense may modify"
- **verification**: a: p.14 ok; b: p.17 ok; c: p.21 ok; sha256 1ccb890643fa

## secfid_2606.30783: Security-Fidelity Tradeoffs: The Hidden Cost of Prompt Injection Defense

- **scope**: Benchmark and evaluation paper, not a survey: 1,168 instances (plus a 252-scenario agentic extension), four defences in eight variants over 15 base-model settings, 48 configurations (Sections 1, 4); ICML 2026, PMLR 306.
- **corpus cutoff**: not applicable
- **organising dimensions**: Related work groups defences by intervention point: input-centric filtering, prompting-level delimiters, model-centric fine-tuning or architecture (Section 6). The paper's own structure is the outcome coding: executed, processed, ignored, other (Section 3.4).
- **treatment user task**: Not measured as a separate quantity; the task in each instance is the document task itself.
- **treatment document handling**: Measured and defined: security is one minus the executed rate; fidelity is one minus the ignored rate; safe processing is processed and not executed (Section 3.5). On Llama 3.1 8B (Table 1): executed and ignored rates of 49.1/7.7 undefended, 5.7/24.7 ASIDE, 14.0/20.3 ISE, 0.7/26.1 SecAlign, 1.9/53.7 DefensiveTokens. Section 4.2 text gives 1.2 and 3.0 for the last two where Table 1 gives 0.7 and 1.9; cite Table 1 and Table 22 (confidence intervals), not the prose.
- **treatment comparability**: Each defence is run with the inference procedure its authors specify (Appendix B.1); ASIDE and ISE from the official ASIDE repository. No comparability rule; layouts therefore differ across the compared defences.
- **evidence granularity**: Per defence and base model: executed, ignored, processed rates with confidence intervals.
- **what this review adds**: SecFid is the source of the document-handling definitions and of published security-fidelity pairs; this review places those pairs on the two-axis map with their layouts recorded, adds the user's task, and grades every comparison for layout equality, which SecFid's own protocol does not hold.
- **a_source_axis** = no; p.9: "Input-centric methods attempt to filter malicious content before it reaches the model"
- **b_three_jobs_together** = partial; p.4: "We define Fidelity as 1 - Ignored Rate"
- **c_equal_layout_rule** = no; p.24: "we use the inference procedure specified by each defense"
- **verification**: a: p.9 ok; b: p.4 ok; c: p.24 ok; sha256 3c27d8cb98ee

## wang_2602.10453: The Landscape of Prompt Injection Threats in LLM Agents: From Taxonomy to Analysis

- **scope**: SoK of prompt injection threats in LLM agents; 78 papers (37 attack, 41 defence); search ended 20 October 2025 (p. 1; pp. 4 and 6).
- **corpus cutoff**: 20 October 2025 (p. 1)
- **organising dimensions**: Defences by level: text-level (detection filters; prompt enhancement by separation, negative prompts, rewriting), model-level (alignment by fine-tuning; internal-representation probes), execution-level (task alignment, access control, isolation) (Figure 2, p. 5; Table 2, p. 6; Sections 4.1-4.3, pp. 7-9). The 'separate' family uses delimiters and structure, and alignment trains on specific interaction formats, but there is no axis over signal forms.
- **treatment user task**: Eight defences run on AgentPI with GPT-4o-mini: ASR and utility under no attack (Figure 6, p. 12), time and tokens (Table 5, p. 13). Utility under attack is not reported.
- **treatment document handling**: Not measured. The paper states that many defences appear effective by suppressing contextual inputs (abstract, p. 1) and by coarse-grained refusal (p. 11), which is the symptom this review's third requirement measures.
- **treatment comparability**: All defences run on one model and one benchmark, an applied condition; a change of prompt structure is counted as an intrusiveness cost (p. 10), not as a condition for comparing numbers.
- **evidence granularity**: Per defence on one model: ASR, no-attack utility, time, tokens (Figure 6, Table 5); the model-level defences are not run.
- **what this review adds**: The signal axis with the no-signal value; the user's task under attack and the document-handling requirement measured, which turns this paper's suppression remark into a number; layout as a comparison condition; graded comparisons across published numbers including model-side defences.
- **a_source_axis** = partial; p.7: "uses structural transformations and delimiters"
- **b_three_jobs_together** = no; p.12: "utility under no attack cases"
- **c_equal_layout_rule** = partial; p.10: "require a change of the prompt structure"
- **verification**: a: p.7 ok; b: p.12 ok; c: p.10 ok; sha256 01b7926b7818
