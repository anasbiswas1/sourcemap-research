# Coding rules for the record files (frozen with schema v1 in notebook 03)

These rules say how a paper is turned into a record file in `reports/records/<report_id>.yaml`. They were committed before full extraction (notebook 04). Amendment 2 (notebook 04r) was added after the second pass of notebook 04_second_pass showed gaps in rules 7, 8, 9 and 32; the text before each amendment is unchanged, and every record was re-coded under it. The schema in `schema/record_schema.yaml` says which fields exist and which values they take; these rules say how to choose the values.

## 1. Reading and pages

1. Every record is filled from the PDF in `data/defences/`, whose SHA-256 is in `reports/defences.csv`. Nothing is filled from memory, from an abstract alone or from another paper's description of the work.
2. Every record holding a fact from the paper carries `page`, the 1-based page index of the PDF (not the printed page number). A fact on a different page goes in `pages: {field: page}`.
3. `extraction_scope` says what was coded: "whole report", or the sections and table rows coded. A quantity outside the scope is never coded "not reported".
4. `read: F` means the full text was read. Main-table rows need F.

## 2. Defences

5. One defence record per method or variant on one base checkpoint. A method from another paper that this report runs is a defence record with `origin: other_report`.
6. `name` is the method's own name. When the paper prints one name but runs another checkpoint (SecFid prints "SecAlign" and runs facebook/Meta-SecAlign-8B), `name_as_printed` keeps the printed name and `checkpoint_id` names what was run.
7. Axis 1 (how the source is shown at inference) and axis 2 (how the behaviour was built) take every value that applies. A fixed, non-learned change to the data tokens' embeddings (ASIDE) is `fixed_embedding_transform`, not a learned token feature. Amendment 2 (axis 1): `chat_roles` only when the method itself adds a role or turn for the untrusted text, trains an order of privilege over roles, or uses each segment's role as an input to its inference rule; roles that the chat template or the agent harness already has do not count on their own. Wording in a prompt alone, and labels that are only numbers (numbered references), are `no_signal`. `internal_intervention` only when the intervention acts by source (on the tokens marked as untrusted, or keyed by their source); an intervention applied at a fixed position or by another score, wherever the untrusted text sits, is `no_signal`. A defence from another report whose layout this report does not describe takes axis 1 from its own report, or from how the other re-runs of the method in the corpus are coded.
8. `isolation: ablation_present` only when the paper runs the defence with a component removed or changed and reports the result. Amendment 2: isolation belongs to the method, so every base-checkpoint record of the method takes the same value. `no_ablation` is a method the report runs as its own with no such run. `not_applicable` is a record that is itself a variant or a control of another record in the same report (an ablation arm; an objective, data or training-stage variant; a checkpoint other than the final one; a control direction or prompt; the comparison arm of a training method), or another report's defence that this report runs without removing or changing its components.
9. Signal dependence: `measured` (the defence run with its signal removed or moved, with numbers); `measured_other_checkpoint` (measured, but on another checkpoint of the method, named in `signal_dependence_detail`); `stated` (the paper says the signal is needed, without numbers); `baseline_only` (a prompting defence whose signal-removed condition is just the instruction-only baseline); `not_reported`; `not_applicable` (no inference-time signal). Amendment 2: `not_applicable` exactly when axis 1 is `no_signal`. A prompting defence or a fixed inference rule with a signal is `measured` when the same defence is run with the signal removed or moved, otherwise `baseline_only` when the run without the defence is reported (the undefended model; for a prompt stacked on another defence, that defence alone), otherwise `not_reported`; `stated` is not used for these. A trained defence with a signal is `measured`, `measured_other_checkpoint`, `stated` or `not_reported`, never `baseline_only`.
10. Layout compatibility marks only layouts the paper ran (`supported` or `unsupported`); everything else is `untested`.
11. Amendment 1 (training targets): `trains_instruction_pair` is yes when training pairs the user's own instruction with the same injected words, partly when some injected strings also appear as legitimate instructions with other data, no otherwise. `trains_carry_through` is yes_exact_targets or yes_by_preference when training rewards carrying instruction-bearing text through as data. Both are `not_applicable` when nothing is trained: prompting defences and fixed inference rules, including a steering direction fitted from examples.

## 3. Evaluations

12. One evaluation per configuration under one protocol: one defence (or undefended model), one benchmark split, one attacker, one judge. An injection position reported separately (start, middle, end) is a separate evaluation.
13. The undefended reference is `defence_id: none:<base>`, with `baseline_kind`: off_the_shelf; same_data_twin (instruction-tuned by the authors on the same data, as ASIDE's Vanilla); instruction_prompt_only.
14. `measured_by` is the report whose authors ran the evaluation. A re-measurement of a released checkpoint carries `same_checkpoint_as: <report_id>:<defence_id>` only when the text says the released checkpoint was used.
15. Attacker: static (fixed injections), optimisation (gradient or search on this model), adaptive (built against this defence), human, rl. Access and budget as stated; "unreported" when not given.
16. Decoding as stated. When both arms of a within-report comparison ran in one harness and the paper does not print the setting, the condition is `matched_unstated`.
17. `run` names the run when a paper reports more than one run of the same configuration (canonical, comparison battery, replicate).
18. `subset_of` names the parent set when an evaluation uses a subset; `locked_split` says whether the test split was fixed before testing.
19. `judge_reading` is strict or relaxed when the paper defines both; otherwise single, or absent when not stated.

## 4. Results and the outcome coding

20. One result per printed number, with the metric name as printed and the value as printed. `value_source` says where it is printed. A result shown only in a chart is `value_source: figure_only` with no value; it counts for coverage and is never used in a comparison or a derived number.
21. `qualifier`: exact; approximate ("about 50%"); upper_bound ("below 3%"); lower_bound (CounterSteer's compromise rates under a generation budget).
22. A value relative to a reference uses `unit: percent_of_reference` and names the reference in `reference` (SEP utility set to 50.0 for the undefended model; benign utility as a percentage of the same row's clean run).
23. `spread` keeps the printed spread and the number of runs. Printed differences between two results are not coded; they are recomputed from the results.
24. Quantities: R1 from attack success, compromise or execution rates (R1 = 1 − rate). R2clean is the user's task done on clean data; R2attack under attack. R3ns is non-suppression (SecFid's fidelity, 1 − ignored rate); R3cp is correct handling of the data the task asked for (SecFid's processed rate); R3safe is processed and not executed.
25. AlpacaEval, MMLU and similar general benchmarks are `general_utility`, never R2. SEP utility and "utility under attack" scored on the user's task are R2 proxies unless the paper scores the user's instruction directly. AgentDojo's task checker scores the user's task and is R2 direct. A summary-quality score is at most an R3 proxy. The SEP separation score maps to no single quantity and is `other`.
26. When one printed metric is two quantities at once (SecFid's processed rate in translation and editing is R3cp and an R2attack proxy), the first goes in `quantity` and the second in `also_quantity`.
27. A string-matched attack success that also fires on quoted text is E or Rp in the outcome coding; it is coded Rp when the task asked for the text.

## 5. Comparisons and grades

28. A comparison has a purpose: W (which whole configuration does better), M (does this component cause the change) or X (a reading across two reports). `varies` says what differs between the arms.
29. Six conditions: c1 base checkpoint, c2 layout, c3 benchmark and split, c4 attacker, c5 judge and denominator, c6 decoding. Each is matched, matched_unstated, unmatched, unreported or manipulated (the one condition an M comparison varies on purpose).
30. Grade (plan v2 equation 4), computed by code: A when every condition is matched or is the one manipulated condition; B when exactly one is unmatched; C when two or more are; U when any is unreported. In W the layout may differ by design and is left out. matched_unstated counts as matched within one report and as unreported in an X comparison.

## 6. Claims and coverage

31. A claim is a headline claim from the abstract or introduction, with a verbatim anchor of at most 14 words, the jobs it speaks to, the comparisons that support it and, in `contradicted_by`, any result in the same report that cuts against it.
32. Coverage per quantity: direct; proxy (instrument named); aggregate_only (reported only pooled over defences, models or tasks); not_reported (inside the extraction scope); unclear; not_applicable. `where` points to the table or section. Amendment 2: `aggregate_only` applies whenever the quantity is reported only pooled, whatever the instrument, and `where` names the instrument. R1 counts the execution of any injected instruction, malicious or not; a changed answer counted whatever the injected goal (an answer flip) is an R1 proxy. A metric that scores the task done and the attack failed together is R3safe. A score on data the task needs that itself carries instruction-bearing text (a cue the agent must act on, valid evidence with an injection inside) is an R3cp proxy, in `also_quantity` when the metric is first another quantity.
33. A task partition that changes how a result should be read (CounterSteer's delegated-authority tasks) is described in a residual note; the schema has no field for it.

## 7. What is checked by code

34. Allowed values, required fields, references between records, page within the PDF, every printed value found on its page (in the plain text or in a column-preserving extraction, so table cells are not glued together), every anchor found on its page (a page break is allowed), anchors at most 14 words, and the PDF's SHA-256 against the manifest.
