import unittest
import tempfile
import io
import runpy
from pathlib import Path
from unittest.mock import Mock,patch
from conversation import Conversation,reply_issues
from app import State


class ConversationTests(unittest.TestCase):
    def test_interrupted_playback_note_does_not_authorize_tools(self):
        conversation=Conversation()
        conversation.audio_interruption={'completed_spoken_sections':'I was checking.','current_section':'Interrupted; heard portion unknown.'}
        messages,_=conversation.begin('What were you saying?')
        self.assertIn('Do not assume the remaining text was heard',messages[0]['content'])
        self.assertIsNone(conversation.audio_interruption)
        self.assertIsNone(conversation.target)

    def test_saved_chat_restores_history_but_not_target_permission(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'chat.json'
            c=Conversation(path);messages,start=c.begin('This VM keeps freezing')
            messages.append({'role':'assistant','content':'When did this start?'})
            c.finish(messages,start)
            restored=Conversation(path)
            self.assertEqual(restored.transcript[-1]['content'],'When did this start?')
            self.assertIsNone(restored.target)
    def test_configuration_change_advice_is_withheld(self):
        self.assertTrue(reply_issues('Edit the adapter to use a different DNS server.'))
        self.assertTrue(reply_issues('Run ipconfig /all and tell me the output.'))
        self.assertTrue(reply_issues('That will tell us if the VM can reach the internet.'))
        self.assertEqual(reply_issues('Do not change DNS settings. The cause is unknown.'),[])
    def test_remembers_issue_and_previous_answer(self):
        c=Conversation();messages,start=c.begin('Websites fail')
        messages.append({'role':'assistant','content':'When did this start?'})
        c.finish(messages,start)
        following,_=c.begin('This morning')
        self.assertTrue(any(m.get('content')=='When did this start?' for m in following))
        self.assertIn('Websites fail',str(following))

    def test_target_requires_explicit_current_environment(self):
        for text in ['yes','my PC','not this VM','the host, not this VM']:
            c=Conversation();c.begin(text)
            with self.assertRaises(ValueError): c.confirm()
        c=Conversation();c.begin('This VM');self.assertTrue(c.confirm()['confirmed'])
        c.begin('Actually the host needs help')
        with self.assertRaises(ValueError):c.require_target()

    @patch('app.collect_health')
    def test_no_network_check_before_target_confirmation(self,collect):
        state=State();state.mode='chat';state.emit=Mock()
        with self.assertRaises(ValueError):
            state.execute({'function':{'name':'get_network_snapshot','arguments':{}}})
        collect.assert_not_called()

    @patch('app.collect_integrity',return_value={'windows_directory':'C:\\Windows','errors':[],'checks':[]})
    def test_agent_can_choose_file_check_without_tool_activation(self,collect):
        state=State();state.mode='chat';state.emit=Mock();state.chat.begin('This VM keeps crashing')
        state.execute({'function':{'name':'verify_windows_files','arguments':{}}})
        collect.assert_called_once()

    def test_new_app_state_starts_with_empty_dialog(self):
        first=State();first.chat.begin('Old conversation')
        second=State()
        self.assertEqual(second.chat.transcript,[])
        self.assertIsNone(second.chat.storage_path)

    def test_launcher_uses_owned_window_lifecycle(self):
        with patch('window_launcher.launch') as launch:
            runpy.run_path(str(Path(__file__).with_name('launcher.py')),run_name='__main__')
            launch.assert_called_once_with()

    @patch('app.collect_health',return_value={'network_status':{'changes_made':False}})
    def test_chat_can_choose_supported_tool_and_retain_evidence(self,collect):
        state=State();state.mode='chat';state.emit=Mock();state.ensure_runtime=Mock()
        def call(name):return {'role':'assistant','content':'','tool_calls':[{'function':{'name':name,'arguments':{}}}]}
        state.ask=Mock(side_effect=[call('confirm_running_windows'),call('get_network_snapshot'),{'role':'assistant','content':'I checked this VM. What happens when you open a website?'}])
        state.run('Please check this VM')
        collect.assert_called_once()
        self.assertEqual(state.chat.target,'current')
        self.assertIn('What happens',state.chat.transcript[-1]['content'])
        self.assertTrue(any(m['role']=='tool' for m in state.chat.turns[-1]))


if __name__=='__main__':unittest.main()
