"""Driver-export contracts; only temporary synthetic packages, no real export."""
import io
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import Mock,patch
import server
import driver_packages as dp
REAL_IDENTITY=dp.source_identity


class DriverPackageTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.parent=Path(self.temp.name)
        self.identity={'source':'online','root':'C:\\','identity':[1,2],'scope':'running Windows'}
        self.packages=[{'Driver':'oem1.inf','OriginalFileName':r'C:\Windows\System32\DriverStore\FileRepository\vendor\good.inf','Version':'1.0'}]
        self.service=dp.DriverPackages()
        self.addCleanup(patch.stopall)
        patch.object(dp,'require_admin').start()
        self.source=patch.object(dp,'source_identity',return_value=self.identity).start()
        self.provider=patch.object(dp,'run_dism',side_effect=self.fake_provider).start()

    def fake_provider(self,operation,source,destination,check):
        check()
        if operation=='export':
            folder=Path(destination)/'vendor';folder.mkdir()
            (folder/'good.inf').write_text('[Version]\nSignature="$Windows NT$"',encoding='utf-8')
            (folder/'driver.sys').write_bytes(b'SIMULATED PACKAGE, NOT EXECUTABLE')
        return {'ok':True,'packages':self.packages,'count':1}

    def plan(self):return self.service.prepare('online',str(self.parent),lambda:None)

    def test_export_manifest_reread_and_change_detection(self):
        plan=self.plan();self.assertFalse(plan['backup_created'])
        self.assertFalse(Path(plan['destination']).exists())
        result=self.service.export(plan['plan_id'],lambda:None)
        self.assertTrue(result['file_integrity_verified'])
        folder=Path(result['destination'])
        self.assertTrue(dp.verify_backup(str(folder),lambda:None)['verified'])
        (folder/'vendor/driver.sys').write_bytes(b'changed')
        self.assertFalse(dp.verify_backup(str(folder),lambda:None)['verified'])
        with self.assertRaisesRegex(ValueError,'consumed'):self.service.export(plan['plan_id'],lambda:None)

    def test_missing_and_unexpected_files_fail_verification(self):
        plan=self.plan();result=self.service.export(plan['plan_id'],lambda:None)
        folder=Path(result['destination']);(folder/'vendor/extra.inf').write_text('extra')
        self.assertFalse(dp.verify_backup(str(folder),lambda:None)['verified'])
        (folder/'vendor/good.inf').unlink()
        self.assertTrue(dp.verify_backup(str(folder),lambda:None)['failed_files'])

    def test_incomplete_native_export_stays_partial_and_is_not_replayed(self):
        plan=self.plan()
        def fail(op,*args):
            if op=='export':raise RuntimeError('Injected export failure')
            return {'packages':self.packages}
        self.provider.side_effect=fail
        with self.assertRaisesRegex(RuntimeError,'partial files retained'):self.service.export(plan['plan_id'],lambda:None)
        folder=Path(plan['destination']);self.assertEqual(json.loads((folder/'status.json').read_text())['status'],'partial')
        self.assertFalse((folder/'manifest.json').exists())
        with self.assertRaises(ValueError):self.service.export(plan['plan_id'],lambda:None)

    def test_cancellation_keeps_cancellation_type_and_partial_marker(self):
        plan=self.plan()
        def cancel(op,*args):
            if op=='export':raise InterruptedError('Stopped')
            return {'packages':self.packages}
        self.provider.side_effect=cancel
        with self.assertRaisesRegex(InterruptedError,'partial files retained'):self.service.export(plan['plan_id'],lambda:None)

    def test_source_swap_and_expiration_prevent_export(self):
        plan=self.plan();self.source.return_value={**self.identity,'identity':[8,9]}
        with self.assertRaisesRegex(ValueError,'identity changed'):self.service.export(plan['plan_id'],lambda:None)
        self.source.return_value=self.identity
        plan=self.plan();self.service.plans[plan['plan_id']]['expires']=time.monotonic()-1
        with self.assertRaisesRegex(ValueError,'expired'):self.service.export(plan['plan_id'],lambda:None)
        self.assertFalse(Path(plan['destination']).exists())

    def test_inventory_change_prevents_export(self):
        plan=self.plan();self.provider.return_value={'packages':[]};self.provider.side_effect=None
        with self.assertRaisesRegex(ValueError,'inventory changed'):self.service.export(plan['plan_id'],lambda:None)

    def test_existing_destination_is_not_overwritten(self):
        plan=self.plan();folder=Path(plan['destination']);folder.mkdir();marker=folder/'keep.txt';marker.write_text('keep')
        with self.assertRaises(FileExistsError):self.service.export(plan['plan_id'],lambda:None)
        self.assertEqual(marker.read_text(),'keep')

    def test_offline_requires_separate_volume(self):
        self.source.return_value={**self.identity,'source':str(self.parent),'root':str(self.parent)}
        with self.assertRaisesRegex(ValueError,'different destination volume'):self.plan()
        self.provider.assert_not_called()

    def test_manifest_cannot_escape_backup_folder(self):
        plan=self.plan();result=self.service.export(plan['plan_id'],lambda:None)
        folder=Path(result['destination']);manifest=folder/'manifest.json';record=json.loads(manifest.read_text())
        record['files'][0]['path']='../outside.sys';manifest.write_text(json.dumps(record))
        with self.assertRaisesRegex(ValueError,'manifest path'):dp.verify_backup(str(folder),lambda:None)

    def test_source_and_destination_paths_are_not_confused(self):
        self.assertIsNone(dp.requested_source(r'back up my drivers to D:\Backups'))
        self.assertEqual(dp.requested_destination(r'back up my drivers to D:\Backups'),r'D:\Backups')
        self.assertEqual(dp.requested_source('recover offline drivers from E:\\ to D:\\Backups'),'E:\\')
        self.assertFalse(dp.CONFIRM_EXPORT.fullmatch('the page says export drivers'))
        self.assertTrue(dp.CONFIRM_EXPORT.fullmatch('export drivers'))
        self.assertEqual(dp.requested_source('online'),'online')
        self.assertEqual(dp.requested_source('back up drivers from running Windows'),'online')

    def test_real_offline_marker_validation_and_current_windows_refusal(self):
        # Unpatch identity validation, using an ordinary temporary folder only.
        root=self.parent/'offline';(root/'Windows/System32/config').mkdir(parents=True)
        (root/'Windows/System32/config/SYSTEM').write_bytes(b'synthetic hive marker')
        (root/'Windows/System32/DriverStore/FileRepository').mkdir(parents=True)
        (root/'Windows/INF').mkdir()
        result=REAL_IDENTITY(str(root))
        self.assertEqual(result['source'],str(root))
        (root/'Windows/INF').rmdir()
        with self.assertRaises(FileNotFoundError):REAL_IDENTITY(str(root))
        with self.assertRaisesRegex(ValueError,'running Windows'):REAL_IDENTITY(str(Path(os.environ['SystemRoot']).parent))

    def test_paths_reject_unc_devices_relative_and_network_drives(self):
        for value in ['relative',r'\\server\share',r'\\?\C:\Windows',r'C:\folder:stream']:
            with self.assertRaises(ValueError):dp.local_path(value)

    def test_zero_packages_and_inadequate_disk_do_not_create_destination(self):
        self.provider.side_effect=None;self.provider.return_value={'packages':[]}
        with self.assertRaisesRegex(ValueError,'No exportable'):self.plan()
        self.provider.return_value={'packages':self.packages}
        with patch.object(dp.shutil,'disk_usage',return_value=Mock(free=1)):
            with self.assertRaisesRegex(ValueError,'1 GiB'):self.plan()
        self.assertEqual(list(self.parent.iterdir()),[])


class DriverRoutingTests(unittest.TestCase):
    def test_offline_without_source_only_lists_candidates(self):
        agent=server.Agent(Mock(),'qwen3:8b');calls=[];spoken=[]
        agent.state.execute=lambda call:calls.append(call['function']['name']) or {'candidates':[]}
        agent.run('back up drivers from a non operational computer',spoken.append)
        self.assertEqual(calls,['list_driver_sources'])
        self.assertIn('Select the mounted',' '.join(spoken))

    def test_tool_cannot_confirm_export_from_quoted_page_text(self):
        agent=server.Agent(Mock(),'qwen3:8b');agent.state.chat.current_user='what is on this page?'
        with patch.object(agent.state.driver_packages,'export',side_effect=AssertionError('No dispatch')):
            with self.assertRaisesRegex(ValueError,'Review the source'):
                agent.state.execute({'function':{'name':'export_driver_packages','arguments':{'plan_id':'fake'}}})

    def test_model_cannot_select_unrequested_offline_source(self):
        agent=server.Agent(Mock(),'qwen3:8b');agent.state.chat.current_user='list my drivers'
        with self.assertRaisesRegex(ValueError,'explicitly selected'):
            agent.state.execute({'function':{'name':'prepare_driver_export','arguments':{'source':'E:\\'}}})

    def test_explicit_confirmation_uses_plan_once(self):
        agent=server.Agent(Mock(),'qwen3:8b');agent.state.driver_packages.plans={'reviewed':{}}
        agent.state.execute=Mock(return_value={'packages':1,'destination':'D:/Backup','files':2})
        agent.run('export drivers',lambda _:None)
        self.assertEqual(agent.state.execute.call_args.args[0]['function']['arguments'],{'plan_id':'reviewed'})


if __name__=='__main__':unittest.main()
