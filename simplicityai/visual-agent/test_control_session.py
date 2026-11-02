import unittest
from control_session import ControlSession, Locator, Condition, AmbiguousControl, ActionOutcomeUnknown
from windows_adapter import WindowsAdapter
from desktop_actions import decode


class Controls(unittest.TestCase):
    def test_post_action_verifier_error_is_not_a_safe_to_repeat_lookup_error(self):
        calls=[]
        class Adapter:
            backend='test'
            capabilities={'click'}
            def find(self,locator):
                if calls:return [{},{}]
                return [{'token':1,'rect':[1,2,3,4],'visible':True,'enabled':True}]
            def perform(self,*args):calls.append(True)
        session=ControlSession(Adapter(),sleep=lambda _:None)
        with self.assertRaises(ActionOutcomeUnknown):
            session.act('click',Locator('Button'),expected=Condition(Locator('Result'),'text','Done'))
        self.assertEqual(len(calls),1)

    def setup_session(self,nodes,perform=None):
        class Adapter:
            backend='test'
            capabilities={'click'}
            def find(self,locator):return nodes
            def perform(self,*args):return perform() if perform else 'clicked'
        return ControlSession(Adapter(),sleep=lambda _:None)

    def test_unique_stable_ready_target_and_independent_condition(self):
        nodes=[{'token':1,'rect':[1,2,3,4],'visible':True,'enabled':True,'name':'Ready'}]
        result=self.setup_session(nodes).act('click',Locator('Ready'),expected=Condition(Locator('Ready'),'name','Ready'))
        self.assertTrue(result['outcome_verified'])

    def test_ambiguous_and_hidden_controls_do_not_pass(self):
        with self.assertRaises(AmbiguousControl):self.setup_session([{},{}]).act('click',Locator('Duplicate'))
        session=self.setup_session([{'visible':False,'name':'Done'}])
        self.assertFalse(session.verify(Condition(Locator('Done'),'name','Done'),timeout=.001))

    def test_sent_failure_is_never_replayed(self):
        calls=[]
        def failure():
            calls.append(True)
            raise TimeoutError('Possible side effect')
        nodes=[{'token':1,'rect':[1,2,3,4],'visible':True,'enabled':True}]
        with self.assertRaises(ActionOutcomeUnknown):self.setup_session(nodes,failure).act('click',Locator('Button'))
        self.assertEqual(len(calls),1)

    def test_windows_reacquires_id_and_refuses_replaced_control(self):
        old={'name':'One','type':'ButtonControl','automation_id':'num1Button','runtime_id':[1],
             'rect':[10,10,20,20],'enabled':True}
        current=dict(old,runtime_id=[2])
        clicks=[]
        adapter=WindowsAdapter(lambda:([current],True),lambda:None,clicks.append)
        with self.assertRaises(ValueError):adapter.perform('click',Locator('One','button'),dict(old,token=[1]),None)
        self.assertEqual(clicks,[])

    def test_literal_model_control_action(self):
        self.assertEqual(decode("Action: click_control(name='Seven', role='button', id='num7Button')",100,100)['id'],'num7Button')
        for text in ("click_control()","click_control(name=__import__('os'))","click_control(name='One', unknown='x')"):
            with self.assertRaises((ValueError,SyntaxError)):decode(text,100,100)


if __name__=='__main__':unittest.main()
