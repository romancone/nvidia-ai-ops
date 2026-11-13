# Benchmark data

This directory is the single working source for published results.

- `benchmark-data.json`: completed measurements, configurations and saved answers
- `raw/`: losslessly compressed clean source files, grouped by model and hardware cohort
- `raw-manifest.json`: bundle checksums and each original file's path, size and SHA-256

The one-time import includes source files for the published Strata 64/128 GiB
and vLLM 128 GiB results. The excluded vLLM 64 GiB series stays hidden; its
historical summary records are retained unchanged, but its raw history is not
imported. Failed attempts, debug files and experiment history remain on node3.
Original source archives on node3 are archival evidence, not another working copy.

Extract a bundle outside the repository when inspecting native files:

```bash
mkdir -p /tmp/nvidia-results
tar -xzf evaluation/raw/qwen38-flash-next-nvfp4-128g.tar.gz -C /tmp/nvidia-results
```

For new models, retain complete inputs, outputs, native results and the memory,
timing and configuration evidence used by the published measurements. Import only
selected completed cases; do not copy an entire experiment directory. Follow the
[benchmark report skill](../.agents/skills/benchmark-report-review/SKILL.md).

Generate `reports/benchmark-data.js` from the canonical JSON using the
[README command](../README.md#benchmark-reports). Both disk and GitHub Pages
views use that generated copy. Never edit it separately or duplicate raw bundles
under `reports/`. Historical tests are not rerun to complete this migration.
