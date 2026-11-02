import unittest
from page_status import blocker


class PageStatus(unittest.TestCase):
    def test_google_verification_is_not_search_success(self):
        self.assertEqual(blocker('https://www.google.com/sorry/index?q=token')['kind'],'human_verification')
        self.assertIsNone(blocker('https://www.google.com/search?q=speed'))
        self.assertIsNone(blocker('https://www.google.evil.com/sorry/index'))


if __name__=='__main__':unittest.main()
