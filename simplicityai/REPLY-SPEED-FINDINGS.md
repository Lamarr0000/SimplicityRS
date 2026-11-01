# Reply speed and role correction — November 1

User clarified reply speed is the biggest concern. Evidence supports multiple
contributors rather than attributing all delay to either architecture or CPU.

1. Live fast transcription was0.41s; opening audio could start22ms after text.
2. A first model turn took28.1s, including12.95s model load,5.73s prompt processing
   and9.37s generation. A following warm turn took12.5s (2.08s prompt,10.38s generation).
3. Replaying one existing bounded chat request locally without executing tools or
   speech produced first text3.24s, complete reply5.92s. It had a warm model and
   cached prompt (0.48s prompt processing); this is not a representative average.
   Source log:20261101-131737-f9eeaf.conversation.json. Metrics are saved outside Git in
   C:/SimplicityAI-Lab/ThemHands/logs/real-chat-first-content-benchmark.json.
4. The app buffers the full chat reply until its reporting checks finish, so the
   replay demonstrates an additional~2.68s between first available text and full
   completion. Early text delivery is a relevant architectural direction, not a
   demonstrated end-to-end fix. Current speech prefetch already overlaps part of
   synthesis without publishing rejected drafts.

The current20B model is partly GPU-resident on an8GB GPU and generates around8–9
tokens/s in measured tests. That identifies the model/runtime stage; it does NOT
isolate CPU compute vs memory bandwidth vs offload as the precise hardware limit.
Automatic/4/8 model-thread comparison did not produce useful improvement.

Added first_content_seconds to model timing metrics for future live comparisons.
It measures first content received, not first text displayed or tool readiness.
No partial-text delivery or prewarming implementation is claimed by this change.

Separately finished the already-started Calculator emphasis correction: primary
purpose now leads with nontechnical troubleshooting/recovery; Calculator guidance
is secondary. Casual greetings should not advertise arithmetic. A synthetic
greeting returned "Hey there! How can I help you with your Windows today?", no
tool calls. This is one check, not guaranteed wording. Also fixed a sticky old
Calculator flag hijacking later outside-host recovery questions; bare host
clarification returns a generic unsupported-target explanation without tool/model.

30 conversation/boundary/Calculator component tests pass. Source/checkpoint saved
and pushed, host modules staged with backup; manual reopen loads changes. Runtime
remains0.6.3. Existing unrelated BRS edits and VM package preserved. No mic, live
desktop input, diagnostic tools, repair or cloud calls used for these checks.
