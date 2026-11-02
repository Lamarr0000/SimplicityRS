"""Recovery scope, interrupted evidence, display and permission-error regressions."""
import unittest
from unittest.mock import Mock,patch
import server
from target_scope import TargetConversation
from tool_state import ToolState
from findings import clean_reply,table_view,table_text
from troubleshooting import diagnostic_report_issue

RECOVERY='I put this recovery image into my computer and booted from it because Windows will not start.'
STORAGE={'area':'storage','checked_utc':'synthetic fixture','sections':[{'name':'Volumes','status':'available','data':[{'DeviceID':'C:','SizeGiB':100,'FreeGiB':12.5,'FreePercent':12.5}]}]}


class RecoveryTests(unittest.TestCase):
    def test_recovery_boot_does_not_bind_broken_windows_to_current_collectors(self):
        chat=TargetConversation();chat.begin('Good evening');self.assertFalse(chat.original_issue)
        chat.begin(RECOVERY);self.assertEqual(chat.target,'other')
        chat.begin('Check my drivers.');self.assertEqual(chat.target,'other')
        with self.assertRaises(ValueError):chat.require_target()
        chat.begin('Check the Windows running SimplicityAI.');self.assertEqual(chat.target,'current')

    def test_local_desktop_viewer_is_separate_from_offline_diagnostic_target(self):
        state=ToolState();state.chat=TargetConversation();state.chat.begin(RECOVERY);state.chat.begin('Open Device Manager here.');state.emit=Mock()
        state.desktop.execute=Mock(return_value={'launch_requested':True,'completion_verified':False})
        state.execute({'function':{'name':'open_desktop_app','arguments':{'app':'device_manager'}}})
        state.desktop.execute.assert_called_once()
        with patch('tool_state.inspect_windows') as collect:
            with self.assertRaises(ValueError):state.execute({'function':{'name':'inspect_windows','arguments':{'area':'drivers'}}})
            collect.assert_not_called()

    def test_findings_survive_cancelled_delivery_and_table_needs_no_model(self):
        agent=server.Agent(Mock(),'qwen3:8b');state=agent.state;state.chat.begin('Check current storage.')
        def interrupt(kind,*args,**kwargs):
            if kind=='findings':raise InterruptedError('New voice request')
        with patch('tool_state.inspect_windows',return_value=STORAGE),patch.object(state,'emit',side_effect=interrupt):
            with self.assertRaises(InterruptedError):state.execute({'function':{'name':'inspect_windows','arguments':{'area':'storage'}}})
        self.assertIn('storage',state.recent_findings)
        with patch.object(agent.connection,'open',side_effect=AssertionError('No model or recollection needed')):
            agent.run('Show that disk drive information in a table.',lambda text:None)
        self.assertIn('12.5',state.chat.transcript[-1]['content'])

    def test_emoji_removed_without_changing_math(self):
        self.assertEqual(clean_reply('4 × 8 = 32 😊'),'4 × 8 = 32 ')

    def test_driver_inventory_does_not_establish_update_availability(self):
        self.assertIsNotNone(diagnostic_report_issue('Your drivers are mostly up to date and properly signed.',{'drivers'}))
        self.assertIsNone(diagnostic_report_issue('Driver update availability was not checked.',{'drivers'}))

    def test_error_740_uses_normal_windows_viewer_launch_not_silent_elevation(self):
        from desktop_tools import launch_app
        error=OSError('Elevation required');error.winerror=740
        with patch('desktop_tools.subprocess.Popen',side_effect=error),patch('desktop_tools.shell_open_viewer',return_value={'launch_requested':True}) as shell:
            launch_app('device_manager')
        self.assertEqual(shell.call_args.args[1],['devmgmt.msc'])

    def test_table_is_scoped_and_synthetic_data_is_labelled(self):
        view=table_view({**STORAGE,'simulation':True})
        self.assertIn('SIMULATION ONLY',view['note']);self.assertIn('C:',table_text(view))
        self.assertIn('offline',view['note'])


if __name__=='__main__':unittest.main()
