import unittest
from desktop_actions import decode,to_screen


class DesktopActions(unittest.TestCase):
    def test_actions_and_pixel_mapping(self):
        self.assertEqual(decode("Action: hotkey(key='ctrl shift esc')",1344,756)['shortcut'],'ctrl+shift+esc')
        self.assertEqual(decode("Action: type(content='hello\\n')",1344,756),
            {'kind':'type','content':'hello','submit':True})
        self.assertEqual(to_screen((672,378),(1344,756),(3840,2160)),[1920,1080])
        self.assertEqual(decode("Action: finished(content='Visible report')",1344,756)['kind'],'finished')

    def test_rejects_code_expansion_invalid_keys_and_outside_points(self):
        for action in ["click(start_box=__import__('os'))", "click(**{'start_box':'(1,2)'})",
                       "hotkey(key='win r')", "click(start_box='(1344,200)')",
                       "type(content='a\\tb')", "click(start_box='(1,2)',start_box='(3,4)')"]:
            with self.subTest(action=action),self.assertRaises((ValueError,SyntaxError)):
                decode(action,1344,756)


if __name__=='__main__':unittest.main()
