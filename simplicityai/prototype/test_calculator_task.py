import unittest
from unittest.mock import Mock,patch
from calculator_task import calculate,validate
from app import State


class FakeCalculator:
    def __init__(self):self.observation=0;self.calls=[]
    def call(self,name,args):
        if name=='press_calculator_button':
            assert args['observation']==self.observation
        self.calls.append((name,args));self.observation+=1
        return {'usable':True,'observation':self.observation,'display':'7'}


class CalculatorTaskTests(unittest.TestCase):
    def test_buttons_and_separate_final_read_use_current_observations(self):
        calc=FakeCalculator();result=calculate(calc,'1+1',Mock(),Mock())
        self.assertEqual([args['button_id'] for name,args in calc.calls if name=='press_calculator_button'],['clearButton','num1Button','plusButton','num1Button','equalButton'])
        self.assertEqual(calc.calls[-1],('observe_calculator',{}))
        self.assertEqual(result['display'],'7')  # Actual tool value, not invented arithmetic.
        self.assertTrue(result['final_display_reread'])

    def test_no_commands_or_multi_step_expressions(self):
        for expression in ['1+1;anything','1+2+3','-1+1','12345+1']:
            with self.assertRaises(ValueError):validate(expression)

    def test_explicit_calculator_task_uses_no_model_round_trip(self):
        state=State();state.mode='chat';state.calc=FakeCalculator();state.emit=Mock();state.ensure_runtime=Mock()
        state.ask=Mock(side_effect=AssertionError('No model request needed'))
        state.run('Open Calculator and add 1+1')
        state.ask.assert_not_called();self.assertIn('shows 7',state.chat.transcript[-1]['content'])

    def test_host_reply_is_explicit_and_never_controls_local_app(self):
        state=State();state.mode='chat';state.chat.calculator_requested=True;state.calc=Mock();state.emit=Mock();state.ensure_runtime=Mock()
        state.run('host')
        state.calc.call.assert_not_called();state.ensure_runtime.assert_not_called()
        self.assertIn('physical host',state.chat.transcript[-1]['content'])

    def test_agent_can_choose_calculator_without_user_activation(self):
        state=State();state.mode='chat';state.calc=FakeCalculator();state.emit=Mock()
        result=state.execute({'function':{'name':'calculate_in_calculator','arguments':{'expression':'1+1'}}})
        self.assertTrue(result['final_display_reread'])


if __name__=='__main__':unittest.main()
