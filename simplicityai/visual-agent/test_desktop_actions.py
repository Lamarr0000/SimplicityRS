import unittest
from desktop_actions import decode,to_screen,requested_app


class DesktopActions(unittest.TestCase):
    def test_catalog_launch_request_is_explicit_and_not_negated(self):
        apps=['task_manager','device_manager','notepad']
        self.assertEqual(requested_app('Open Task Manager and select Performance.',apps),'task_manager')
        self.assertEqual(requested_app('Could you please launch the device manager?',apps),'device_manager')
        self.assertIsNone(requested_app('Do not open Task Manager.',apps))
        self.assertIsNone(requested_app('What is Task Manager?',apps))
        self.assertIsNone(requested_app('Open task managers backup.exe',apps))
        self.assertIsNone(requested_app('Open task manager backup.exe',apps))
        self.assertEqual(requested_app('Can you open up Task Manager?',apps),'task_manager')

    def test_actions_and_pixel_mapping(self):
        self.assertEqual(decode("Action: hotkey(key='ctrl shift esc')",1344,756)['shortcut'],'ctrl+shift+esc')
        self.assertEqual(decode("Action: type(content='hello\\n')",1344,756),
            {'kind':'type','content':'hello','submit':True})
        self.assertEqual(to_screen((672,378),(1344,756),(3840,2160)),[1920,1080])
        self.assertEqual(to_screen((644,336),(1288,672),(2880,1484),(255,538)),[1695,1280])
        self.assertEqual(decode("Action: finished(content='Visible report')",1344,756)['kind'],'finished')
        self.assertEqual(decode("Action: open_app(name='task_manager')",1344,756,apps=['task_manager']),
                         {'kind':'open_app','name':'task_manager'})

    def test_rejects_code_expansion_invalid_keys_and_outside_points(self):
        for action in ["click(start_box=__import__('os'))", "click(**{'start_box':'(1,2)'})",
                       "hotkey(key='win r')", "click(start_box='(1344,200)')",
                       "type(content='a\\tb')", "click(start_box='(1,2)',start_box='(3,4)')",
                       "open_app(name='cmd')"]:
            with self.subTest(action=action),self.assertRaises((ValueError,SyntaxError)):
                decode(action,1344,756)


if __name__=='__main__':unittest.main()
