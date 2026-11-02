import unittest
from outcome_verifier import evaluate, TEST_TEXT, verify


class OutcomeVerifier(unittest.TestCase):
    def test_notepad_requires_exact_document_text(self):
        for text, expected in [(TEST_TEXT, True), (TEST_TEXT+'\r\n', True),
                               ('', False), ('prefix '+TEST_TEXT, False)]:
            self.assertEqual(evaluate('notepad-text', 'notepad.exe',
                [{'type':'DocumentControl','text':text}])['verified'], expected)
        self.assertFalse(evaluate('notepad-text', 'notepad.exe',
            [{'type':'TextControl','text':TEST_TEXT}])['verified'])

    def test_task_manager_requires_selected_view_and_metrics(self):
        nodes=[{'name':'Performance','selected':True},{'name':'CPU'},{'name':'Memory'}]
        self.assertTrue(evaluate('task-manager-performance','taskmgr.exe',nodes)['verified'])
        self.assertFalse(evaluate('task-manager-performance','taskmgr.exe',nodes[1:])['verified'])
        nodes[0]['selected']=False
        self.assertFalse(evaluate('task-manager-performance','taskmgr.exe',nodes)['verified'])

    def test_wrong_app_incomplete_and_unknown_cannot_pass(self):
        nodes=[{'type':'DocumentControl','text':TEST_TEXT}]
        for case, app, complete in [('notepad-text','msedge.exe',True),
                                    ('notepad-text','notepad.exe',False),
                                    (None,'notepad.exe',True)]:
            self.assertFalse(evaluate(case, app, nodes, complete)['verified'])

    def test_foreground_change_prevents_collection(self):
        result=verify('notepad-text',{'hwnd':1},lambda _: {'hwnd':2},lambda:2,lambda:None)
        self.assertFalse(result['verified'])


if __name__=='__main__':unittest.main()
