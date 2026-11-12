# Qwen3.8-27B NVFP4 · missing measurements

## Deferred — do not run without a separate request

All tests and updates below are deferred. Existing Short/Long results remain
valid; they do not need reruns just to fill memory fields. Keep the cards and
missing values as they are. If work resumes, limit concurrency to 16 users
and preserve the model and sampling settings.

- [ ] Short, 512 input / 256 output tokens: capture DRAM and VRAM under load
  for C=1,2,4,8,16 alongside timings from the same runs
- [ ] Long, 32768 input / 256 output tokens: capture DRAM and VRAM under load
  for C=1,2,4,8 alongside timings from the same runs
- [ ] Max: agree on the exact budget within the 262144-token window; the card
  targets approximately 245752 input tokens and at most 16384 output tokens,
  allowing for the chat template. Then measure speed, TTFT, common decode
  window and DRAM/VRAM at C=1,2,4,8,16, stopping at the first memory or queue limit
- [ ] Import only completed matching results into the canonical JSON and update
  the cards; keep memory and timing measurements tied to the same run

## Archive findings

- `vllm-c1-validation.7oakPa`: Short C=1,2,4,8,16 and Long C=1 have timings,
  but `gpu.csv` records only VRAM capacity; no free DRAM snapshots were saved
- `vllm-long-scheduler.mhesfq17`: Long C=2,4,8 completed; `metrics.jsonl`
  contains running/waiting/preemptions, not memory measurements
- The latter series' `gpu.after.csv` records 97887 MiB total, 90322 MiB occupied
  and 7565 MiB free after the series. This is neither minimum free VRAM under
  load nor a separate result for C=2/4/8
- `metrics.after.prom`: post-series process RSS is not host free DRAM;
  startup estimates of KV and available RAM cannot replace load measurements
- Long C=9,10,12,16 are marked `excluded: queue` in `continuation.log`;
  do not rerun automatically or classify them as missing completed tests
- `nvidia-long-max-20261107.WWigCc/max/c1`: 999744 input / 256 output tokens,
  temperature=0, thinking=false — obsolete configuration; do not import into
  the current 256K Max results

Sources were inspected in the local archive copy at
`/private/tmp/nvidia-all-evidence-import-20261111/manifest.json`;
original run directories remain under `/var/tmp` on node3.
Completed public results and the evidence archive reference are in
[evaluation/benchmark-data.json](evaluation/benchmark-data.json).
