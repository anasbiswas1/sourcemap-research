# Schema v0 to v1: the one revision after the six-report pilot

The pilot coded six reports with schema v0 (`schema/record_schema_v0.yaml`, records in `reports/pilot_v0/`). Every place where v0 needed a free-text workaround was written to that record's `schema_gaps` (33 in all). Each change below answers one or more of them. The six records were then recoded with v1 (`reports/records/`) and v1 was frozen.

| # | Change in v1 | Gap it answers (record) |
|---|---|---|
| 1 | results.qualifier: exact, approximate, upper_bound, lower_bound | approximate baselines (Spotlighting r1, r3); compromise rates that are lower bounds under a generation budget (CounterSteer) |
| 2 | results.value_source, with figure_only allowed without a value | clean-task results shown only as charts (Spotlighting Figures 7 and 8) |
| 3 | defences.signal_dependence gains baseline_only and measured_other_checkpoint; signal_dependence_detail | prompting defences whose signal-removed condition is the instruction-only baseline (Spotlighting); rotation ablation run on another checkpoint (ASIDE, Qwen3-8B) |
| 4 | defences.pages and evaluations.pages: a page for each field read elsewhere | facts on several pages in one record (SecAlign pp. 7, 8, 11) |
| 5 | condition value matched_unstated; grade rule counts it as matched within a report and unreported across reports | decoding not printed although both arms ran in one harness (SecAlign, Jia et al., ASIDE's SEP runs) |
| 6 | comparisons.varies (required) | a comparison that varies the training method rather than a condition (SecAlign against StruQ) |
| 7 | results.unit percent_of_reference and results.reference | SEP utility set to 50.0 for the undefended model (SecAlign); utility as a percentage of the row's own clean run (CounterSteer); a win rate against the undefended model (Jia et al.) |
| 8 | evaluations.injection_position, with one evaluation per position | SEP attack success reported at the start, middle and end of the data (SecAlign) |
| 9 | evaluations.baseline_kind | the undefended reference is an instruction-tuned twin on the same data (ASIDE's Vanilla), not an off-the-shelf model |
| 10 | results.spread | means over three runs with standard deviations or standard errors (ASIDE) |
| 11 | evaluations.run | a canonical run and a comparison-battery run of the same configuration (CounterSteer) |
| 12 | defences.name_as_printed and defences.checkpoint_id | "SecAlign" printed while facebook/Meta-SecAlign-8B is run (SecFid) |
| 13 | evaluations.same_checkpoint_as | a re-measurement of a released checkpoint that another report coded (Jia et al. on SecAlign's release) |
| 14 | results.also_quantity | one printed metric that is two quantities (SecFid's processed rate: R3cp and an R2attack proxy) |
| 15 | coverage value aggregate_only, and coverage.where | safe processing reported only by task and framing (SecFid); utility under attack in an uncoded appendix table (CounterSteer) |
| 16 | report.extraction_scope (required) and report.later_version | only part of a report coded in the pilot (Jia et al. Section 5.1); a later peer-reviewed version not read (Spotlighting) |
| 17 | claims.contradicted_by | a no-loss claim that the same report's SEP Utility cuts against (ASIDE) |
| 18 | evaluations.subset_of and evaluations.locked_split | GCG runs on a 50-tuple subset (Jia et al.); a locked test split and a held-out task (SecFid) |
| 19 | evaluations.judge_reading | strict and relaxed success criteria defined in the same paper (Spotlighting, SecAlign Table 8) |
| 20 | axis-1 value fixed_embedding_transform | ASIDE's fixed rotation is not a learned token feature |
| 21 | rule, not field: amendment-1 fields are not_applicable when nothing is trained | a fitted steering direction (CounterSteer) |
| 22 | rule, not field: printed differences are recomputed, not coded; the SEP separation score is quantity other | Table 1 differences in parentheses (SecFid); SEP score (ASIDE, SecAlign) |

Kept as residual notes, not fields (2): CounterSteer's split of surviving compromises into delegated-authority tasks and the rest (a reading aid specific to one paper); SecAlign's SEP utility, which is not stated to be scored on clean or attacked inputs (a reading problem, not a schema gap).

Also fixed during the pilot, in the checker rather than the schema: numbers in table rows are looked for in a column-preserving extraction as well as the plain text, because the plain text glues adjacent cells together (".475.07994.4"); YAML files are read with a loader that keeps yes and no as words (standard YAML 1.1 turns them into true and false); anchors are limited to 14 words.
