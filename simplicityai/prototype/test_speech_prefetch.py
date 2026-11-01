import threading
import unittest
from unittest.mock import Mock
from speech_prefetch import SpeechPrefetch, opening_section


class PrefetchTests(unittest.TestCase):
    def test_stable_boundary_and_cleanup(self):
        self.assertIsNone(opening_section('Short draft.'))
        self.assertIsNone(opening_section('```incomplete code'))
        self.assertEqual(opening_section('Short draft.', True), 'Short draft.')
        text = '**This is a sufficiently long opening sentence.** More words follow.'
        self.assertEqual(opening_section(text), 'This is a sufficiently long opening sentence.')
        self.assertLessEqual(len(opening_section('word ' * 40)), 80)

    def test_unapproved_draft_never_released(self):
        speaker = Mock(); speaker.synthesize.return_value = b'audio'
        cache = SpeechPrefetch(speaker)
        draft = 'This opening sentence is long enough to prepare. More text.'
        cache.offer(draft); cache.thread.join(1)
        section = opening_section(draft)
        self.assertIsNone(cache.take(section))
        cache.approve(draft)
        self.assertEqual(cache.take(section), b'audio')
        self.assertIsNone(cache.take(section))

    def test_rewrite_and_cancellation_discard_late_audio(self):
        entered, release = threading.Event(), threading.Event()
        speaker = Mock()
        def synthesize(text, **kwargs):
            entered.set(); release.wait(2); return b'stale'
        speaker.synthesize.side_effect = synthesize
        speaker.cancel.side_effect = release.set
        cache = SpeechPrefetch(speaker)
        draft = 'This opening sentence is long enough to prepare. More text.'
        cache.offer(draft); self.assertTrue(entered.wait(1))
        cache.approve('A completely different approved answer.')
        self.assertIsNone(cache.take(opening_section(draft)))
        self.assertIsNone(cache.audio)
        speaker.cancel.assert_called_once()

    def test_tool_draft_clear_and_failure_fall_back(self):
        speaker = Mock(); speaker.synthesize.side_effect = ValueError('stopped')
        cache = SpeechPrefetch(speaker)
        draft = 'This opening sentence is long enough to prepare. More text.'
        cache.offer(draft); cache.thread.join(1); cache.approve(draft)
        self.assertIsNone(cache.take(opening_section(draft)))
        cache.clear()
        self.assertIsNone(cache.text)

    def test_cancelled_waiter_cannot_restart_old_synthesis(self):
        entered, release = threading.Event(), threading.Event()
        speaker=Mock()
        def synthesize(text, **kwargs):
            entered.set(); release.wait(2); return b'stale'
        speaker.synthesize.side_effect=synthesize
        speaker.cancel.side_effect=release.set
        cache=SpeechPrefetch(speaker)
        draft='This opening sentence is long enough to prepare. More text.'
        cache.offer(draft);self.assertTrue(entered.wait(1));cache.approve(draft)
        errors=[]
        # Synchronize the waiter entering Event.wait before cancellation.
        waiting=threading.Event();original=cache.ready.wait
        def wait(timeout=None):
            waiting.set();return original(timeout)
        cache.ready.wait=wait
        def take():
            try:cache.take(opening_section(draft))
            except ValueError as error:errors.append(str(error))
        reader=threading.Thread(target=take);reader.start()
        self.assertTrue(waiting.wait(1));cache.clear();reader.join(1)
        self.assertEqual(errors,['Playback stopped'])
        self.assertFalse(reader.is_alive())


if __name__ == '__main__':
    unittest.main()
