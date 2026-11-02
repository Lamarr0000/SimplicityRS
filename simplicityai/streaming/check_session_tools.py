"""Session export coverage and CPU sampling semantics; no GUI action."""
import io
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch
import server
from session_tools import export_conversation,sample_cpu
from desktop_tools import create_text


class SessionToolTests(unittest.TestCase):
    def test_export_uses_full_app_transcript_and_both_speakers(self):
        transcript=[{'id':i,'role':'user' if i%2==0 else 'assistant','content':f'Recorded message {i}'} for i in range(24)]
        with tempfile.TemporaryDirectory() as folder:
            result=export_conversation(transcript,'Conversation.txt',Path(folder))
            text=Path(result['path']).read_text(encoding='utf-8')
            self.assertEqual(result['message_count'],24);self.assertEqual(result['assistant_messages'],12)
            self.assertIn('Recorded message 0',text);self.assertIn('Assistant:\nRecorded message 23',text)
            self.assertFalse(result['includes_export_confirmation'])
            with self.assertRaises(FileExistsError):export_conversation(transcript,'Conversation.txt',Path(folder))

    def test_export_request_bypasses_model_reconstruction(self):
        agent=server.Agent(lambda *a,**kw:None,'qwen3:8b')
        agent.state.chat.transcript=[{'id':0,'role':'user','content':'Earlier issue'}, {'id':1,'role':'assistant','content':'Earlier answer'}]
        with tempfile.TemporaryDirectory() as folder,patch('session_tools.create_text',side_effect=lambda name,content,unused=None,**kw:create_text(name,content,Path(folder),**kw)),patch.object(agent.connection,'open',side_effect=AssertionError('No model call')):
            spoken=[];agent.run('Create a document of this entire conversation on my desktop.',spoken.append)
            files=list(Path(folder).glob('*.txt'));self.assertEqual(len(files),1)
            text=files[0].read_text(encoding='utf-8');self.assertIn('Earlier answer',text);self.assertIn('Earlier issue',text)
            self.assertIn('3 recorded messages',' '.join(spoken))

    def test_cpu_sample_is_delta_normalized_to_machine(self):
        process=Mock(pid=5,info={'pid':5,'name':'Sample.exe','create_time':10})
        process.cpu_times.side_effect=[SimpleNamespace(user=0,system=0),SimpleNamespace(user=1,system=0)]
        process.create_time.return_value=10
        with patch('session_tools.psutil.process_iter',return_value=[process]),patch('session_tools.psutil.cpu_count',return_value=4),patch('session_tools.time.monotonic',side_effect=[0,0,0,.1,1,1]),patch('session_tools.time.sleep'):
            result=sample_cpu(lambda:None)
        self.assertEqual(result['highest_sampled_process']['cpu_percent_of_machine'],25)
        self.assertFalse(result['changes_made']);process.kill.assert_not_called();process.terminate.assert_not_called()

    def test_cpu_cancel_prevents_sampling(self):
        with patch('session_tools.psutil.process_iter') as processes:
            with self.assertRaises(InterruptedError):sample_cpu(Mock(side_effect=InterruptedError))
            processes.assert_not_called()


if __name__=='__main__':unittest.main()
