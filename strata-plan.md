# Strata on NVIDIA

The default [profile](profiles/strata-qwen38-iq3s-64g.yml) is Qwen3.8-Flash-Next
IQ3_S: four 262144-token slots, INT8 KV, MTP, GPU vision and PLE in RAM.
The shared cache is 8960 MiB, cgroup limit 52 GiB, OS reserve 10 GiB and
process swap disabled. Max C=4 retained two parked RAM histories and both
were restored. See the [IQ3_S results](reports/qwen38-flash-next.html#cache-8960).

The [catalog](README.md#inference-profiles) also preserves the previous NVFP4
profile with direct PLE reads and the 128 GiB profile with PLE in RAM.

Install using the [recipe](strata.md) or [playbook](strata.yml).
The [report](reports/qwen38-flash-next.html) shows completed stock-engine benchmarks.
Cold prefill can wait for the engine control channel. The load snapshots showed no HTTP queue or slot-admission wait in the completed Long and Max runs at two and four clients.

## Previous NVFP4 work

- Measured Short, Long and Max on upstream. The report records client counts, prefill waiting, TTFT, decode speed and OS memory under load
- Verified independent near-Max conversations with three markers and tool calls, image recognition with history, and recovery after cancellation during decode
- On node3, upstream `146df3c` loaded Qwen3.8-Flash-Next NVFP4/GPTQ with a 262144-token context. The API reported four slots and an enabled four-slot, 5120 MiB conversation cache. The manual process had a 10 GiB OS reserve and swap disabled. Reapplying the role changed zero tasks and preserved the server and engine PIDs
- Prepared the upstream installation recipe and role with native model JSON, bounded RAM, disabled swap and opt-in service startup. The benchmark client is unchanged

The selected decode share is 0. At the original decode share of 0.5, Short streamed to four clients at once. Long responses of 256 tokens had no decode overlap. In the four-client Max run, two streams overlapped for 23.786 seconds.

Investigate a speed drop of 50% or more against the same client count, workload and metric using available RAM, swap and disk activity. Direct PLE reads from SSD are part of the previous NVFP4 profile only.

## NVFP4/GPTQ on 128 GiB DRAM

**Validated on node3 on 12 November 2026.** Four 32 GiB DIMMs run at
DDR4-2400. The [128 GiB report](reports/qwen38-flash-next.html#strata-nvfp4-128g)
covers Short, Long and Max at 1, 2 and 4 clients. The four-client Max batch
had 18.11 s of common decode and a 71.92 s longest pause. Max C=1 direct
free-memory snapshots bracketed the request. Native telemetry sampled
available memory during the run.

- The original four-slot cache parked short conversations and displaced two near-Max histories by entry count
- The stock 1024-token parking threshold preserved all four near-Max histories after GPU-slot replacement. The four snapshots totaled 15.08 GiB and restored 246845–254710 tokens each, with all markers correct
- The measured histories, largest replacement and 10% margin require 20.81 GiB. The profile retains the 24 GiB budget and 114521 MiB cgroup ceiling. Corrected workload snapshots reached minima of 45.09 GiB free and 52.17 GiB available, with zero process swap and OOM events
- Eight slots project to 38.05 GiB of cache and approximately 15.83 GiB of extra RAM for displaced GPU experts, leaving 9.76 GiB free before transient allocations. The requested eight-slot run stopped before launch at the 10 GiB reserve check
- Tool-result continuation, cancellation with recovery and RAM history restoration, and independent image histories at 1, 2 and 4 clients passed
- The corrected four-slot profile serves on loopback. The role rerun changed zero tasks and preserved both PIDs

## Limits and evidence

- Four slots are validated; eight were rejected by the projected memory budget, not a measured failure
- Performance runs used a zero-token cache parking threshold; the deployed 1024-token threshold was verified separately for history retention and functional behavior
- Max stopped at EOS within a hard 16384-token output ceiling; different answer lengths are not equal-work throughput comparisons
- Sparse memory and queue snapshots do not establish continuous bounds; Max C=1 free-memory samples bracketed the request
- Results, configuration identity, source paths and archive checksums are in [the canonical dataset](evaluation/benchmark-data.json); clean originals are in `evaluation/raw/`; experiment history remains on node3
- Use [benchmark.md](benchmark.md) for future authorized measurements; no further runs are pending
