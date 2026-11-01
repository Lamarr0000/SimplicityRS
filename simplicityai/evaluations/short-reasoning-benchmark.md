# Short synthetic reasoning benchmark

Four sequential local gpt-oss:20b requests, think=low, temperature=0, JSON output, 350-token cap. Two synthetic cases at each of two context sizes. No diagnostic tools, model downloads, configuration changes, or real network queries. Raw prompts, answers and timing counters are in short-reasoning-benchmark.json.

| Context | Case | Elapsed seconds | Reviewed result |
|---|---|---:|---|
| 2048 | DNS timeout | 35.99 | Correct observations and unknowns; next check vague, not a discriminating comparison with explicit outcome limits |
| 2048 | DNS success, no symptoms | 20.73 | Failed restraint criterion: proposed additional checks despite explicit instruction that none were indicated |
| 4096 | DNS timeout | 34.61 | Same weak next check as smaller context |
| 4096 | DNS success, no symptoms | 13.71 | Passed this limited case: no further check indicated |

All four outputs were complete and matched the requested JSON field shape. Shape is not semantic correctness. Neither timeout answer explained the limits of each comparison outcome. No repair command was executed.

## Interpretation

Short structured prompts produced responses in about fourteen to thirty-six seconds, materially shorter than the earlier long live health explanation. Those runs differ in task, context and output length, so they are not a controlled speed comparison. Context sizes were tested once per case in a fixed order: load time, cache, output length and transient load confound timing. This does not establish that larger context is faster or better, nor justify a production setting change.

Keep scripted facts and narrow workflows as the baseline. The model may provide advisory prose, but free-form causal diagnosis and autonomous repairs remain unvalidated. No additional VM test is needed for this benchmark. Preserve the existing working deployment.
