import unittest
from window_wait import wait_for_launch


class WindowWait(unittest.TestCase):
    def run_wait(self, handles, identities, before=1):
        ticks=iter(range(100))
        windows=iter(handles)
        return wait_for_launch('taskmgr.exe',before,lambda:next(windows),bool,
            lambda hwnd:identities[hwnd],lambda:None,timeout=8,
            clock=lambda:next(ticks),sleep=lambda _:None)

    def test_transient_missing_window_and_unrelated_window_are_not_success(self):
        result=self.run_wait([None,0,2,3],{2:{'process':'notepad.exe'},3:{'process':'taskmgr.exe'}})
        self.assertEqual(result['process'],'taskmgr.exe')

    def test_existing_requested_window_is_valid(self):
        self.assertEqual(self.run_wait([1],{1:{'process':'taskmgr.exe'}})['process'],'taskmgr.exe')

    def test_missing_window_times_out(self):
        with self.assertRaisesRegex(InterruptedError,'no visual input sent'):
            self.run_wait([None]*10,{})


if __name__=='__main__':unittest.main()
