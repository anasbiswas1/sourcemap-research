# Findings of notebook 05

Built 2026-11-23 from the records committed with notebook 04 (3ba84f2) and later record patches. Every number names the file and the rows it was counted from.

## 1. The map (RQ1)

- 95 methods in 89 reports: 57 trained, 38 prompting or fixed rules (analysis/methods.csv).
- Methods per axis-1 value: chat_roles 22; delimiters_markers 25; encodings 4; learned_token_features 6; fixed_embedding_transform 1; position 3; internal_intervention 13; no_signal 34 (analysis/methods.csv, column axis1; a method with two values counts twice).
- Methods per axis-2 value: prompting 29; soft_tokens_frozen 2; sft 33; preference_optimisation 25; distillation 22; adversarial_rl 10; fixed_inference_rule 20 (column axis2).
- 31 of 56 cells of the map hold at least one method; 25 are empty (analysis/map.csv, column methods).
- The fullest cells: no_signal x sft 14; delimiters_markers x prompting 13; no_signal x distillation 12; chat_roles x preference_optimisation 10; delimiters_markers x sft 10; no_signal x prompting 10 (analysis/map.csv).
- Methods with released weights: 18 (analysis/methods.csv, released_weights = yes: 18 ids in the file).
- Methods per year of the report: 2023 4; 2024 9; 2025 21; 2026 61.

## 2. Signal dependence and layout compatibility (RQ1)

- 61 methods show a source signal at inference; 34 show none (axis 1 no_signal).
- Trained methods with a signal: not_reported 26; stated 4; measured_other_checkpoint 3; measured 2.
- Prompting or fixed-rule methods with a signal: baseline_only 19; measured 5; not_reported 2.
- Run with the signal removed or moved (measured or measured_other_checkpoint): aside_iclr2026:aside, bipia_kdd2025:multi_turn_dialogue_with_explicit_reminder, fath_arxiv2024:fath, guardrag_uwthesis2026:guardrag_with_sage_c, ltbd_arxiv2026:ltbd, provtransformer_arxiv2026:provenance_aware_transformer, rui_preprints2026:rui, spotlighting_arxiv2024:spotlighting, tracer_emnlp2026:tracer, untrustedcomponent_arxiv2026:in_prompt_guardrail_with_spotlighting_by_datamarking (analysis/signal_dependence.csv, with what was found in signal_dependence_detail).
- Layout user_turn: untested 51; supported 44 (analysis/layout_compat.csv).
- Layout separate_role: untested 81; supported 14 (analysis/layout_compat.csv).
- Layout system_context: untested 83; supported 12 (analysis/layout_compat.csv).
- Layout agent_tool_result: untested 49; supported 45; unsupported 1 (analysis/layout_compat.csv).

## 3. Coverage of the three jobs (RQ2)

- R1: papers reporting it directly 112, by proxy 6, only pooled 4; evaluated configurations covering it 836 of 843 (analysis/coverage_by_paper.csv and coverage_by_configuration.csv).
- R2clean: papers reporting it directly 50, by proxy 12, only pooled 4; evaluated configurations covering it 419 of 843 (analysis/coverage_by_paper.csv and coverage_by_configuration.csv).
- R2attack: papers reporting it directly 36, by proxy 8, only pooled 0; evaluated configurations covering it 274 of 843 (analysis/coverage_by_paper.csv and coverage_by_configuration.csv).
- R3ns: papers reporting it directly 1, by proxy 0, only pooled 0; evaluated configurations covering it 5 of 843 (analysis/coverage_by_paper.csv and coverage_by_configuration.csv).
- R3cp: papers reporting it directly 1, by proxy 3, only pooled 0; evaluated configurations covering it 15 of 843 (analysis/coverage_by_paper.csv and coverage_by_configuration.csv).
- R3safe: papers reporting it directly 3, by proxy 0, only pooled 1; evaluated configurations covering it 27 of 843 (analysis/coverage_by_paper.csv and coverage_by_configuration.csv).
- All three jobs scored on the same replies: 39 of 843 (5 in 100) configurations, in 6 reports: actconsistency_arxiv2026, codel_arxiv2026, coer_arxiv2026, secfid_arxiv2026, tab_arxiv2026, tracer_emnlp2026 (coverage_by_configuration.csv, joint_all_three = yes).
- R1 and R2attack on the same replies: 210 of 843 (25 in 100) configurations.
- Own paper against anyone, for the named families proposed in the corpus (analysis/coverage_by_family.csv):
  - ASIDE | trained: R3 measured by its own paper: no; by anyone: yes; later reports: 2
  - DRIP | trained: R3 measured by its own paper: no; by anyone: yes; later reports: 1
  - DefensiveTokens | trained: R3 measured by its own paper: no; by anyone: yes; later reports: 4
  - FATH | prompting or rule: R3 measured by its own paper: no; by anyone: no; later reports: 0
  - ISE | trained: R3 measured by its own paper: no; by anyone: yes; later reports: 5
  - Instruction Hierarchy | trained: R3 measured by its own paper: no; by anyone: no; later reports: 0
  - Jatmo | trained: R3 measured by its own paper: no; by anyone: no; later reports: 1
  - Meta-SecAlign | trained: R3 measured by its own paper: no; by anyone: yes; later reports: 30
  - Polymorphic Prompt Assembling | prompting or rule: R3 measured by its own paper: no; by anyone: no; later reports: 0
  - RETA | trained: R3 measured by its own paper: no; by anyone: yes; later reports: 1
  - ReasAlign | trained: R3 measured by its own paper: no; by anyone: no; later reports: 1
  - Reminder prompt | prompting or rule: R3 measured by its own paper: no; by anyone: no; later reports: 2
  - SecAlign | trained: R3 measured by its own paper: no; by anyone: no; later reports: 18
  - SecOPD | trained: R3 measured by its own paper: no; by anyone: yes; later reports: 2
  - Spotlighting | prompting or rule: R3 measured by its own paper: no; by anyone: yes; later reports: 26
  - StruQ | trained: R3 measured by its own paper: no; by anyone: no; later reports: 13
  - VerIH | trained: R3 measured by its own paper: no; by anyone: no; later reports: 1

## 4. What the metrics count (RQ2, the crosswalk)

- 156 benchmark, quantity and judge-rule groups over 5950 results (analysis/crosswalk.csv).
- R1 results whose judge rule is human raters: 14 of 3673 (under 1 in 100); it cannot see: counts E as the raters judged it; blind to P and S unless scored separately.
- R1 results whose judge rule is model judge: 497 of 3673 (14 in 100); it cannot see: counts E as the judge's prompt defines it; blind to P and S unless scored separately.
- R1 results whose judge rule is not stated: 292 of 3673 (8 in 100); it cannot see: the rule that counts E is not given.
- R1 results whose judge rule is programmatic checker: 971 of 3673 (26 in 100); it cannot see: sees the actions or state the attacker wanted, not what the reply says; blind to P and S.
- R1 results whose judge rule is reference metric: 332 of 3673 (9 in 100); it cannot see: counts a wrong answer as attack success whatever caused it; blind to Rp, P and S.
- R1 results whose judge rule is string or answer match: 867 of 3673 (24 in 100); it cannot see: cannot tell an executed injection (E) from a quoted or translated one (Rp); blind to P and S.
- R1 results whose judge rule is success rule given, judge not named: 670 of 3673 (18 in 100); it cannot see: the success rule is stated, but not whether a string, a model or a person applied it.
- R1 results whose judge rule is unclassified: 30 of 3673 (1 in 100); it cannot see: the record's judge text does not say how E is counted.
- Results on general-utility benchmarks (not the user's task on the document): 386.

## 5. Support for headline claims (RQ3)

- 158 headline claims in 121 reports; best grade of their supporting comparisons: A 143; B 6; C 0; U 1; none 8 (analysis/claim_support.csv).
- Claims about security (job R1) supported by at least one grade-A comparison: 124 of 135 (92 in 100).
- Claims about utility that rest on general-utility metrics only: 13 of 72 (18 in 100) (13 ids in the file).
- Claims with a result in the same report that cuts against them: 39 (39 ids in the file).
- Cross-paper readings (purpose X): 48, of which grade U: 48 (analysis/orderings.csv, purpose = X). An unreported condition on either side leaves the reading not assessable.
- Conditions left unreported in comparisons: c1_base 7 (reports 2); c2_layout 125 (reports 2); c3_benchmark 1 (reports 1); c4_attacker 0 (reports 0); c5_judge 34 (reports 2); c6_decoding 48 (reports 1) (analysis/reporting_gaps.csv); these are the lines the Injection Defence Card asks for.

## 6. Orderings

- Grade-A comparisons between two defended arms inside one report: 780 (373 whole-configuration, 407 mechanism) in 60 reports (analysis/orderings.csv, grade = A). These are the only orderings the review states, each inside its own report.
- No ordering across papers is supported: every cross-paper reading is grade U.

## 7. Stress tests (RQ4)

- Methods that faced an adaptive, optimisation, RL or human attacker, in their own paper or a later one: 41 of 95 (43 in 100) (analysis/stress_tests.csv).
- Faced one in their own paper: 36; only in a later paper: 5; white-box attack in their own paper: 17.
- Run with the signal removed or moved: 10; re-measured by a later paper: 17.
- Trained methods pushed by a stronger attacker: 32 of 57 (56 in 100); prompting or fixed-rule methods: 9 of 38 (24 in 100).

## 8. Suppression cost per security point

- Published pairs with security and non-suppression for a defended and the undefended configuration in one grade-A comparison: 4, all in secfid_arxiv2026 (analysis/scs.csv).
- ASIDE (re-measured by SecFid) on Llama 3.1 8B: SCS 0.39 (R3ns 92.3 to 75.3, R1 50.9 to 94.3; secfid_arxiv2026:r_aside_e;secfid_arxiv2026:r_base_e;secfid_arxiv2026:r_aside_i;secfid_arxiv2026:r_base_i).
- ISE (re-measured by SecFid) on Llama 3.1 8B: SCS 0.36 (R3ns 92.3 to 79.7, R1 50.9 to 86.0; secfid_arxiv2026:r_ise_e;secfid_arxiv2026:r_base_e;secfid_arxiv2026:r_ise_i;secfid_arxiv2026:r_base_i).
- Meta-SecAlign-8B (re-measured by SecFid) on Llama 3.1 8B: SCS 0.38 (R3ns 92.3 to 73.9, R1 50.9 to 99.3; secfid_arxiv2026:r_msa_e;secfid_arxiv2026:r_base_e;secfid_arxiv2026:r_msa_i;secfid_arxiv2026:r_base_i).
- DefensiveTokens (re-measured by SecFid) on Llama 3.1 8B: SCS 0.97 (R3ns 92.3 to 46.3, R1 50.9 to 98.1; secfid_arxiv2026:r_dt_e;secfid_arxiv2026:r_base_e;secfid_arxiv2026:r_dt_i;secfid_arxiv2026:r_base_i).
- The 10 printed values behind these pairs were read by eye against their page (analysis/values_used_05.csv). SCS is computed only from published pairs and is not called a benchmark.

