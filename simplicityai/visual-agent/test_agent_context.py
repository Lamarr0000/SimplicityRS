import unittest
from agent_context import AgentContext


class ContextContract(unittest.TestCase):
    def test_preserves_system_active_task_and_two_recent_images(self):
        context=AgentContext('Type the test. Do not close the app.')
        for index in range(10):
            messages=context.observation(f'data:image/png;base64,image{index}',f'result{index}','Notepad')
            self.assertEqual(messages[0]['role'],'system')
            self.assertIn('finished()',messages[0]['content'])
            self.assertIn('Do not close the app.',messages[-1]['content'][0]['text'])
            self.assertIn(f'result{index}',messages[-1]['content'][0]['text'])
            images=[item['image_url']['url'] for message in messages
                if isinstance(message['content'],list) for item in message['content'] if item['type']=='image_url']
            self.assertLessEqual(len(images),2)
            self.assertEqual(images[-1],f'data:image/png;base64,image{index}')
            self.assertLessEqual(len(messages),12)
            self.assertEqual(messages[1]['role'],'user')
            context.action('Action: wait()')

    def test_returned_payload_is_immutable_snapshot(self):
        context=AgentContext('test')
        old=context.observation('data:image/png;base64,first')
        context.action('Action: wait()')
        context.observation('data:image/png;base64,second')
        self.assertIn('test',old[-1]['content'][0]['text'])

    def test_injects_only_supplied_app_catalog(self):
        context=AgentContext('test',['task_manager','notepad'])
        self.assertIn('task_manager, notepad',context.messages[0]['content'])
        self.assertIn('open_app',context.messages[0]['content'])


if __name__=='__main__':unittest.main()
