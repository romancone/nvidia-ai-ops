# Strata on NVIDIA

The selected model is Qwen3.8-Flash-Next NVFP4/GPTQ. The upstream CUDA
profile requests four 262144-token slots with INT8 KV, MTP and GPU vision.
PLE reads directly from SSD. Conversation cache is shared (5120 MiB),
swap is disabled for Strata, and the OS reserve is 10 GiB.

Install using the [recipe](strata.md) or [playbook](strata.yml).
The [report](reports/strata.html) records upstream and historical measurements separately.
Cold prefill can wait for the engine control channel. The load snapshots showed no HTTP queue or slot-admission wait in the completed Long and Max runs at two and four clients.

## Completed work

- Measured Short, Long and Max on upstream. The report records client counts, prefill waiting, TTFT, decode speed and OS memory under load
- Verified independent near-Max conversations with three markers and tool calls, image recognition with history, and recovery after cancellation during decode

- On node3, upstream `146df3c` loaded Qwen3.8-Flash-Next NVFP4/GPTQ with a 262144-token context. The API reported four slots and an enabled four-slot, 5120 MiB conversation cache. The manual process had a 10 GiB OS reserve and swap disabled. Reapplying the role changed zero tasks and preserved the server and engine PIDs
- Prepared the upstream installation recipe and role with native model JSON, bounded RAM, disabled swap and opt-in service startup. The benchmark client in this repository matches HEAD
- On the earlier experimental build, completed Short/Long/Max runs and checked independent Max prompts, tool calls, images, conversation reuse and recovery after cancellation. These checks apply to that build only
- With direct PLE reads, measured full Max requests at 1, 2, 4 and 6 clients. Six clients completed with no observed admission queue; the search stopped at the operator's request. Four slots remain the selected configuration. See the [measurement table and scope](reports/strata.html)

The [session handoff](STRATA-HANDOFF.md) records the selected decode share of 0 and the discarded experiments. At the original decode share of 0.5, Short streamed to four clients at once. Long responses of 256 tokens had no decode overlap. In the four-client Max run, two streams overlapped for 23.786 seconds.

Investigate a speed drop of 50% or more against the same client count, workload and metric using available RAM, swap and disk activity. Direct PLE reads from SSD are part of this profile.
