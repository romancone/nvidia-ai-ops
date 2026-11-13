---
name: benchmark-report-layout
description: Create or adjust NVIDIA benchmark overview cards and model report tables using the agreed compact layout. Use for reports/index.html and shared report presentation, not benchmark execution or data imports.
---

# Benchmark Report Layout

Keep the public report compact and readable. Read [AGENTS.md](../../../AGENTS.md)
for scope and permissions and [MAINTAINERS.md](../../../MAINTAINERS.md) for ownership.

## Overview cards

- Group each model and quantization variant under its full model name and engine
- Show exactly three workload cards per model variant: Short, Long and Max, in
  that order: three columns above 700 px and one column at 700 px or narrower
- Stack Short, Long and Max vertically on mobile; keep compact tables inside
  each card and preserve the three-column layout on wider screens
- Inside each card, use one compact table with users as rows, not separate user
  tiles or cards. Derive client counts from the selected saved series rather
  than limiting the table to 1/2/4
- Show users, decode tok/s/user, TTFT (s), DRAM and VRAM in the table. Keep column
  headings on one line, including units; do not insert `<br>` in headings
- Put the input/output token budget below the Short/Long/Max heading
- Put model disk footprint, context, KV quantization, MTP and PLE placement once
  above the three cards. Keep cohort differences in one concise note below them
- Use small padding, tight row spacing, aligned numbers and restrained color to
  emphasize speed. Compact means reducing wasted space, not splitting labels
- Do not add switches to overview cards. Link to the model page for all benchmarks
- Keep an unmeasured workload card with a clear “Not measured” state; do not
  invent measurements or display placeholder user rows as completed results

## Model pages and navigation

- Use full model names in navigation, such as Qwen3.8-27B and Qwen3.8-Flash-Next
- Point the Repository link to the repository's GitHub page, not a local Markdown
  file that the browser downloads
- Keep workload and user filters in detailed benchmark tables; preserve their
  existing order and behavior
- Include DRAM and VRAM in benchmark tables. Keep disk footprint in the model's
  common parameters above the tables, not as a repeated benchmark column

## Measurement labels

- Render values from `evaluation/benchmark-data.json` through the shared report
  code; HTML and CSS must not maintain independent benchmark values
- Label video memory VRAM, not GPU. State whether memory is free or used and
  distinguish host DRAM, engine-reported VRAM and measured workload peaks
- Preserve the existing distinction between sampled free DRAM and engine-reported
  free VRAM; never describe either as measured process peak consumption
- Use GiB for memory and disk, preserve the disk footprint's scope and source,
  and display missing measurements as “—”
- Preserve cohort selection and measurement meaning during layout-only edits

## Visual review

When browser verification is authorized, inspect the rendered overview at the
mobile and wide widths: cards must stack in one column at 700 px or narrower
and share a three-column row above it. Headings must stay unbroken and user
counts must remain readable. Check model-page filters and
navigation when affected. Capture the resulting view for the user. Do not run
benchmarks, change host settings, stage or publish as part of a presentation edit.
