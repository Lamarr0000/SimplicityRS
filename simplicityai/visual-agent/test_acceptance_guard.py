import copy
import unittest
from acceptance_guard import bind_document, check_document, require_document_action, require_calculator_action
from outcome_verifier import TEST_TEXT


class DocumentBoundary(unittest.TestCase):
    def test_calculator_blocks_memory_history_keys_and_unknown_modes(self):
        nodes=[{'name':'Standard'}, {'type':'ButtonControl','automation_id':'num1Button','rect':[10,20,30,40]}]
        require_calculator_action({'kind':'click'},nodes,True,[[15,25]])
        nodes[0]['name']='Standard Calculator mode'
        require_calculator_action({'kind':'click'},nodes,True,[[15,25]])
        for action,complete,point in [({'kind':'click'},True,[[100,100]]),
                                      ({'kind':'hotkey','shortcut':'ctrl+m'},True,[]),
                                      ({'kind':'type','content':'137+29'},True,[]),
                                      ({'kind':'click'},False,[[15,25]])]:
            with self.assertRaises((InterruptedError,ValueError)):require_calculator_action(action,nodes,complete,point)
        nodes[0]['name']='Scientific'
        with self.assertRaises(InterruptedError):require_calculator_action({'kind':'click'},nodes,True,[[15,25]])

    def setUp(self):
        self.identity={'hwnd':1,'pid':2,'created':3,'process':'notepad.exe','title':'Untitled - Notepad'}
        self.nodes=[{'type':'TabItemControl','name':'Untitled','selected':True,'runtime_id':[1]},
                    {'type':'DocumentControl','text':'','runtime_id':[2],'rect':[10,20,100,200]}]

    def test_observed_notepad_accessibility_label(self):
        self.nodes[0]['name']='Untitled. Unmodified.'
        self.assertEqual(bind_document(self.identity,self.nodes,True)['tab'],[1])
        for name in ('Untitled.txt. Unmodified.','Untitled. Modified.','Other Untitled'):
            self.nodes[0]['name']=name
            with self.assertRaises(InterruptedError):bind_document(self.identity,self.nodes,True)

    def test_rejects_actual_named_document_regression(self):
        self.identity['title']='New Text Document.txt - Notepad'
        with self.assertRaises(InterruptedError):bind_document(self.identity,self.nodes,True)

    def test_refuses_nonblank_ambiguous_or_incomplete_document(self):
        for mutation in ('text','duplicate','incomplete'):
            nodes=copy.deepcopy(self.nodes)
            if mutation=='text':nodes[1]['text']='existing user text'
            if mutation=='duplicate':nodes.append(dict(nodes[1]))
            with self.assertRaises(InterruptedError):
                bind_document(self.identity,nodes,mutation!='incomplete')

    def test_bound_identity_survives_auto_title_change_but_not_tab_switch(self):
        binding=bind_document(self.identity,self.nodes,True)
        self.identity['title']='*Offline visual control test - Notepad'
        self.nodes[0]['name']=TEST_TEXT
        self.nodes[1]['text']=TEST_TEXT
        self.assertEqual(check_document(binding,self.identity,self.nodes,True)['text'],TEST_TEXT)
        self.nodes[0]['runtime_id']=[9]
        with self.assertRaises(InterruptedError):check_document(binding,self.identity,self.nodes,True)

    def test_blocks_tab_click_close_save_and_duplicate_typing(self):
        doc=self.nodes[1]
        require_document_action({'kind':'click'},doc,[[20,30]])
        require_document_action({'kind':'type','content':TEST_TEXT,'submit':False},doc,[])
        for action,points in [({'kind':'click'},[[20,5]]),
                              ({'kind':'hotkey','shortcut':'ctrl+s'},[]),
                              ({'kind':'open_app','name':'notepad'},[]),
                              ({'kind':'type','content':'wrong','submit':False},[])]:
            with self.assertRaises(InterruptedError):require_document_action(action,doc,points)
        doc['text']=TEST_TEXT
        with self.assertRaises(InterruptedError):
            require_document_action({'kind':'type','content':TEST_TEXT,'submit':False},doc,[])


if __name__=='__main__':unittest.main()
