import unittest
from windows_integrity import may_inject


class IntegrityBoundary(unittest.TestCase):
    def test_lower_integrity_cannot_inject_into_elevated_target(self):
        medium={'integrity_rid':0x2000,'ui_access':False}
        high={'integrity_rid':0x3000,'ui_access':False}
        self.assertFalse(may_inject(medium,high))
        self.assertTrue(may_inject(high,high))
        self.assertTrue(may_inject(high,medium))

    def test_uiaccess_does_not_grant_system_target_access(self):
        uiaccess={'integrity_rid':0x2000,'ui_access':True}
        self.assertTrue(may_inject(uiaccess,{'integrity_rid':0x3000}))
        self.assertFalse(may_inject(uiaccess,{'integrity_rid':0x4000}))


if __name__=='__main__':unittest.main()
