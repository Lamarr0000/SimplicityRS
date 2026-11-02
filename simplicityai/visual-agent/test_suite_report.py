import unittest
from suite_report import summarize
from window_wait import wait_for_launch


class SuiteReport(unittest.TestCase):
    def test_summary_retains_partial_status_and_stop_without_claiming_pass(self):
        records=[{'model_seconds':1.25,'driver':'clicked'},
                 {'outcome_verification':{'verified':False,'status':'partially_verified'}},
                 {'stopped':True,'reason':'user takeover'}]
        result=summarize('test',records,'case.json')
        self.assertFalse(result['verified'])
        self.assertEqual(result['status'],'partially_verified')
        self.assertEqual(result['actions'],1)
        self.assertEqual(result['stop_reason'],'user takeover')

    def test_alias_window_launch_accepts_calculator_actual_process(self):
        result=wait_for_launch(('calculatorapp.exe','calculator.exe'),1,lambda:2,bool,
                              lambda _: {'process':'calculatorapp.exe'},lambda:None)
        self.assertEqual(result['process'],'calculatorapp.exe')

    def test_launch_recovery_is_bounded_and_does_not_accept_other_windows(self):
        clock=iter(range(100))
        active=[1]
        activations=[]
        def identify(hwnd):
            if hwnd==1:raise InterruptedError('Protected foreground')
            return {'process':'calculatorapp.exe'}
        def activate():
            activations.append(True)
            active[0]=2
        result=wait_for_launch(('calculatorapp.exe','calculator.exe'),1,lambda:active[0],bool,
            identify,lambda:None,clock=lambda:next(clock),sleep=lambda _:None,activate=activate,timeout=20)
        self.assertEqual(result['process'],'calculatorapp.exe')
        self.assertEqual(len(activations),1)


if __name__=='__main__':unittest.main()
