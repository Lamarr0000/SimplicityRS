# Active-chat memory and interruption explanation — November 1

User screenshot showed model claiming each reply starts fresh and denying prior
conversation memory. The matching request log130946-1a910c.conversation.json
contained five user-role messages and prior assistant messages, so context was
supplied. This was an inaccurate model self-description, not evidence that history
was absent. Conversation.begin retains up to five completed exchanges within an
18000-character history budget plus the original reported issue. New chat/reopen
starts fresh; stored evidence logs do not automatically become resumed chats.

Added explicit application facts to the system instructions: bounded active-chat
context, new-session reset, real interruption behavior and cooperative tool stop.
A narrow reporting check rejects the positive claim each/every reply starts fresh;
it is not a general semantic verifier. A synthetic model trial with a misleading
prior assistant statement improved but still described memory vaguely; do not
claim generic model self-description is fully reliable.

Two narrow application-help question forms now return a factual application-owned
explanation directly, without model inference or Windows tools: how do you handle
interruptions (including the screenshot's speech wording), and do/can you remember
earlier/previous messages [in this chat]. Questions about actual Windows/network
interruptions or additional requests are NOT intercepted. Transcript/history still
retain the exchange. Activity explicitly labels the scripted application behavior
explanation; this is not an AI diagnosis/reasoning result.

24 conversation/boundary tests pass, including supplied history, fresh-session
distinction, specific intent boundaries, and no model/tools for application help.
Host source staged with backups; loaded server remains0.6.3 and user must reopen
to load the module changes. No microphone or live desktop input was used. The
previous speech/transcription fixes remain included. Saved/pushed checkpoint.
