# Strata on NVIDIA

The default [profile](profiles/strata-qwen38-iq3s-64g.yml) is Qwen3.8-Flash-Next
IQ3_S: four 262144-token slots, INT8 KV, MTP, GPU vision and PLE in RAM.
The shared cache is 8960 MiB, cgroup limit 52 GiB, OS reserve 10 GiB and
process swap disabled. Max C=4 retained two parked RAM histories and both
were restored. See the [IQ3_S results](reports/qwen38-flash-next.html#cache-8960).

The [catalog](README.md#inference-profiles) also preserves the previous NVFP4
profile with direct PLE reads and records the unverified 128 GiB plan.

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
