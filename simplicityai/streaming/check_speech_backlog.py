"""Speech review boundary, no microphone or recognition model needed."""
import asyncio
import io
import unittest
from unittest.mock import AsyncMock,Mock
import server
from voice_worker import final_event


class SpeechBacklogTests(unittest.IsolatedAsyncioTestCase):
    def test_ambiguous_one_word_requires_review_and_known_stop_stays_immediate(self):
        self.assertTrue(final_event('SETTING')['review'])
        self.assertFalse(final_event('CANCEL')['review'])
        self.assertFalse(final_event('STOP')['review'])
        self.assertFalse(final_event('OPEN CALCULATOR')['review'])
        self.assertTrue(final_event('OPEN CALCULATOR',limited=True)['limited'])

    async def test_review_resumes_playback_without_submitting_an_action(self):
        ws=Mock();ws.send_json=AsyncMock()
        session=server.Session(ws,'qwen3:8b',io.StringIO())
        session.worker.request=Mock(return_value=[final_event('SETTING')])
        session.submit=AsyncMock();session.paused=True
        await session.frames.put((session.capture,b'x'))
        task=asyncio.create_task(session.audio_loop())
        try:
            for _ in range(50):
                if any(call.args[0]['type']=='review' for call in ws.send_json.call_args_list):break
                await asyncio.sleep(.01)
            self.assertFalse(session.paused)
            session.submit.assert_not_called()
            self.assertIn('voice.resume',[call.args[0]['type'] for call in ws.send_json.call_args_list])
            self.assertIn('review',[call.args[0]['type'] for call in ws.send_json.call_args_list])
        finally:
            task.cancel();await task


if __name__=='__main__':unittest.main()
