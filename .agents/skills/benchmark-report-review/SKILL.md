---
name: benchmark-report-review
description: Collect clean completed results for new model benchmarks and review imports, coverage and report migrations without losing measurement meaning. Not for routine text or CSS edits.
---

# Benchmark Results and Reports

Read [AGENTS.md](../../../AGENTS.md), [MAINTAINERS.md](../../../MAINTAINERS.md)
and [evaluation/README.md](../../../evaluation/README.md).

## One working source

- Keep complete clean originals for published completed tests in `evaluation/`:
  request inputs, responses, native results, effective configuration and the
  timing, memory and queue evidence used to support the results
- Keep failed attempts, debug files, intermediate runs and experiment history on
  the benchmark host. Select completed cases explicitly; never bulk-import a run
  directory or copy an archive without inspecting its contents
- Group originals in lossless bundles under `evaluation/raw/`; index members in
  `evaluation/raw-manifest.json` with original host/path, byte size and SHA-256,
  plus the bundle checksum. Include input dependencies even when stored elsewhere
- Maintain measurements and report metadata in `evaluation/benchmark-data.json`.
  Keep model revision, quantization, engine build, hardware, sampling, context,
  clients, cache, workload and source identity sufficient to distinguish cohorts
- Generate `reports/benchmark-data.js` from that JSON using the README command.
  Both local-file and HTTP views use this derived copy; never edit it independently
  or maintain another set of measurement values in HTML

## Collection and review

1. Inspect the index and working diff separately and preserve staged work
2. For a newly authorized model run, retain originals at collection time. Import
   the selected completed cases once results are ready, before publishing the
   report. This workflow does not authorize tests, host changes or publication
3. Check source completeness and checksums before import. If a required original
   is missing, state the gap; never invent a measurement or rerun an old test
   merely to repair an import without permission
4. Preserve native metric definitions. Distinguish prefill, TTFT, per-request
   decode and throughput in the shared decode window. Do not infer tokens from
   SSE fragments or label mean per-user speed multiplied by clients as measured
   aggregate decode
5. Compare record IDs, saved answers and source coverage before and after the
   change. Preserve approved hidden or excluded series as such; do not restore
   them to the viewer or add technical run details that the user removed
6. Regenerate the report copy and verify it contains the same data as the working
   JSON. When UI verification is authorized, inspect both disk and HTTP views,
   filters and existing image previews. Do not imply runtime verification from
   static inspection

Current historical results are a one-time migration, not a backlog of reruns.
Apply this workflow to new models. Report unresolved gaps in the existing TODO;
keep completed results in the dataset and concise model report, not a second log.
