# Model/runtime comparison — November 1, 2026

## Decision

Do not change the production model yet. Investigate the observed host GPU power/
thermal restriction before drawing normal-speed conclusions or running another
voice pilot. Qwen3 8B, thinking disabled, is a candidate for a later controlled
pilot; Granite4 3B did not meet the limited quality checks. No cloud model was used.

## Hardware observation changes the interpretation

During local inference, NVIDIA reported GPU utilization99%, SM clock300MHz,
memory clock810MHz, P5, SW Power Cap Active and SW Thermal Slowdown Active.
Current power limit30W; requested/default80W. Reported maximum clocks were1560MHz
SM and6001MHz memory. GPU temperature was56°C; reported slowdown threshold95°C.
These are observations, **not proof of a particular thermal or electrical fault**.
The meaning of the gap between current and requested limits needs investigation.

System: Lenovo20QNCTO1WW (ThinkPad P53 family), i9-9880H8cores/16threads, about
72GiB RAM, Quadro RTX4000 8GiB, driver597.30. Windows base scheme Balanced, effective
overlay query returned zero GUID. LITSSVC is running. BIOS/thermal WMI queries were
denied: those settings remain unknown. User reports the original Lenovo adapter
connected directly. This does not establish its recognized wattage or health.

No Windows power scheme, thermal service, GPU limit, driver or firmware was changed.
No thermal protection was disabled. Next useful action: check the user-visible
Windows/Lenovo power mode and perform a short test using the supported performance
mode, with normal cooling/thermal protections retained. A controlled before/after
measurement is needed before claiming how much this restriction explains.

References:

- NVIDIA's [clock-event definitions](https://docs.nvidia.com/deploy/nvml-api/latest/api/group__nvmlClocksEventReasons.html)
- Lenovo's [P53 Intelligent Cooling modes](https://download.lenovo.com/pccbbs/pubs/p53/html_en/en/Use_the_Lenovo_Intelligent_Cooling_feature_%28topic%29_T0000709464.html)
- Microsoft's [performance power slider/overlay documentation](https://learn.microsoft.com/en-us/windows-hardware/customize/desktop/customize-power-slider)

## Bounded comparison

Seven synthetic cases: greeting, unknown-target freeze, confirmed running-VM
network check, outside-host Calculator request, DNS-timeout uncertainty,
historical security events with current status unknown, and recent-context recall.
Existing State.execute target/argument guards were used. Health collectors were
replaced by fixtures; Calculator construction and integrity collection were blocked.
No model-requested Windows diagnostic, app control or repair actually ran.

| Model/profile | Allocation observed | Generation rate observed |
|---|---|---:|
| gpt-oss20B automatic | ~6.07GB VRAM of14.05GB allocation, rest system memory | ~8.3–9.0 tokens/s |
| Granite4 3B automatic | ~2.93GB, entirely VRAM | ~13.5–14.1 tokens/s |
| Granite4 3B CPU-only,4threads | zero VRAM | ~8.6–8.8 tokens/s |
| Qwen3 8B non-thinking automatic | ~6.19GB, entirely VRAM | ~6.9–7.1 tokens/s |
| Qwen3 8B non-thinking CPU-only,4threads | zero VRAM | ~4.2 tokens/s |

Rates are backend evaluation-token counters, not useful-speech latency or a
cross-model measure of equal work. Tokenizers/answer lengths differ. Cold prompt
evaluation was large: Qwen GPU greeting21.1s including18.0s prefill; CPU warmup61.9s.
A later CPU-only short RAM answer took8.62s, first segment5.16s, without TTS/ASR.
These host-specific profiles do not predict performance on every standard PC.

This compared Ollama automatic placement and CPU-only request options. It did not
install or compare an independent serving product such as standalone llama.cpp.
Reported automatic backends were llama.cpp for GPT/Qwen and ggml for Granite;
model and backend effects were not independently controlled.

## Quality review, not a certification

- GPT answered uncertainty/scope questions cautiously. Its security-event answer
  hit the narrow unsupported-advice filter, leaving a partial response. The
  repaired confirmed-network workflow completed using fixture evidence, but its
  wording also described the adapter as “up” although the fixture had no link-state
  field. It is not a ground-truth diagnostic engine.
- Granite still overstated “basic connectivity” from DNS/configuration alone,
  tried unnecessary tools with unconfirmed scope, looped on the historical-event
  case despite no-check instructions, and produced no usable memory answer.
  Hard guards rejected unsupported target attempts. Rejection does not itself
  demonstrate good model judgment.
- Qwen produced complete answers in all seven cases, invoked the fixture network
  tool appropriately, refused outside-host control, did not treat a DNS timeout or
  historical events as proof, and recalled the missing recovery key explicitly.
  Its responses still included unnecessary offers and speculative next steps.
  Seven cases are far too few to establish general troubleshooting reliability.

An activity-callback keyword collision was found in the prototype, fixed, and
covered by a regression check. Initial tool-event failures from that bug are
excluded from the model-quality conclusion. The affected GPT workflow and Granite
cases were rerun. The GPT rerun overlapped the candidate weight download, so its
latency is not used for a clean speed ranking. The candidate run followed download
completion and ran sequentially. The GPU restriction invalidates a normal-speed
ranking regardless.

Qwen3:8b Q4_K_M was downloaded through Ollama with digest verification, about5.2GB,
digest500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41.
Its [model listing](https://ollama.com/library/qwen3:8b) and local /api/show identify
tool and thinking support. Thinking was explicitly false; internal reasoning was
not logged. The prototype's default remains gpt-oss20B. No working installation
was replaced or restarted. No candidate voice/microphone pilot was run.

The comparison restored the original automatic gpt-oss20B allocation and verified
it as the only loaded model afterward. Extra model files remain available on disk.
Seven automated prototype checks now pass, including actual adapter confirmation
and its activity events. The capture worklet is included in source control.

Local evidence under `C:\SimplicityAI-Lab\StreamingPrototype\logs\`:

- `model-runtime-comparison.json` (initial, with excluded tool-event bug)
- `model-runtime-repaired.json` (affected cases rerun)
- `model-runtime-candidate.json` (candidate GPU/CPU-only profiles)
- `gpu-throttling-summary.json` and `gpu-throttling-observation.txt`

These results are saved. No comparison remains running; the next speed test depends
on checking the laptop's normal power/cooling profile.
