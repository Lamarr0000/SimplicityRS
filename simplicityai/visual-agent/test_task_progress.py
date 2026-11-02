import unittest
from task_progress import observed_calculator, ProgressHistory, observed_action


class ProgressTests(unittest.TestCase):
    def test_jitter_uses_observed_control_identity_not_similar_coordinates(self):
        nodes=[{'type':'ButtonControl','automation_id':'num1Button','rect':[10,10,50,50]}]
        a=observed_action({'kind':'click','point':[1,2]},[[20,20]],nodes)
        b=observed_action({'kind':'click','point':[2,3]},[[21,22]],nodes)
        self.assertEqual(a,b)
        action={'kind':'click','point':[50,50]}
        self.assertEqual(observed_action(action,[[50,50]],nodes),action)

    def test_measures_display_and_expression_without_selecting_next_action(self):
        nodes=[{'automation_id':'CalculatorResults','name':'Display is 13'}]
        self.assertEqual(observed_calculator(nodes,True),{'display':'Display is 13','expression':''})
        self.assertIsNone(observed_calculator(nodes,False))
        self.assertIsNone(observed_calculator(nodes+nodes,True))

    def test_repeated_multiaction_cycle_gets_one_recovery_then_stops(self):
        progress=ProgressHistory()
        cycle=[({'display':'0'},{'kind':'click','point':[1,1]}),
               ({'display':'1'},{'kind':'click','point':[3,3]}),
               ({'display':'13'},{'kind':'click','point':[0,0]})]
        for _ in range(2):
            for state,action in cycle:
                self.assertEqual(progress.review(state,action),'')
                progress.record(state,action)
        state,action=cycle[0]
        self.assertIn('No input was sent',progress.review(state,action))
        with self.assertRaises(RuntimeError):progress.review(state,action)

    def test_repeated_action_with_progress_does_not_trigger_loop(self):
        progress=ProgressHistory()
        action={'kind':'click','point':[1,1]}
        for number in ('0','1','11','111','1111'):
            state={'display':number}
            self.assertEqual(progress.review(state,action),'')
            progress.record(state,action)
        self.assertEqual(progress.review(None,action),'')


if __name__=='__main__':unittest.main()
