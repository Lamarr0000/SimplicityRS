"""One bounded speculative audio section; never release an unapproved draft."""
import re
import threading


def opening_section(text, complete=False):
    # Match the client's cleanup and first-section boundary. An unfinished code
    # fence or short fragment cannot be treated as a stable opening section.
    if text.count('```') % 2:
        return None
    clean = re.sub(r'```[\s\S]*?```', 'The command is shown on screen.', text)
    clean = re.sub(r'[*#`]', '', clean).strip()
    if not clean:
        return None
    head = clean[:81]
    for match in re.finditer(r'[.!?](?=\s)', head):
        if match.start() >= 35:
            return clean[:match.start()+1]
    if len(clean) <= 80:
        return clean if complete else None
    end = head.rfind(' ')
    return clean[:end if end > 0 else 80]


class SpeechPrefetch:
    def __init__(self, speaker):
        self.speaker = speaker
        self.lock = threading.RLock()
        self.thread = None
        self.generation = 0
        self.text = None
        self.audio = None
        self.approved = False
        self.ready = threading.Event()
        self.cancelled = threading.Event()

    def clear(self):
        with self.lock:
            self.generation += 1
            self.text = self.audio = None
            self.approved = False
            self.cancelled.set()
            thread = self.thread
            self.ready.set()
        if thread and thread.is_alive():
            self.speaker.cancel()
            thread.join(timeout=2)

    def offer(self, draft):
        section = opening_section(draft)
        if not section:
            return
        with self.lock:
            if self.text is not None or (self.thread and self.thread.is_alive()):
                return
            self.text = section
            self.ready = ready = threading.Event()
            self.cancelled = cancelled = threading.Event()
            generation = self.generation
            def prepare():
                try:
                    audio = self.speaker.synthesize(section, cancelled=cancelled)
                    with self.lock:
                        if generation == self.generation:
                            self.audio = audio
                except Exception:
                    # Speculation is optional; normal playback can retry.
                    pass
                finally:
                    ready.set()
            self.thread = threading.Thread(target=prepare, daemon=True)
            self.thread.start()

    def approve(self, final):
        with self.lock:
            matches = self.text is not None and self.text == opening_section(final, complete=True)
            if matches:
                self.approved = True
        if not matches:
            self.clear()

    def take(self, text):
        with self.lock:
            if not self.approved or text != self.text:
                return None
            generation, ready = self.generation, self.ready
        if not ready.wait(timeout=90):
            self.clear()
            raise ValueError('Voice preparation timed out')
        with self.lock:
            if generation != self.generation or not self.approved:
                # A playback request already waiting on this generation must
                # not fall back to synthesizing its stale text after a stop.
                raise ValueError('Playback stopped')
            audio = self.audio
            self.audio = self.text = None
            self.approved = False
            return audio
