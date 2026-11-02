"""Driver boundary checks without creating a window or sending any input."""
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import desktop_lab


class LabBoundary(unittest.TestCase):
    def setUp(self):
        self.lab = desktop_lab.Lab.__new__(desktop_lab.Lab)
        self.lab.cancel = threading.Event()
        self.lab.hwnd = 123
        self.lab.revision = 7
        self.lab.canvas = SimpleNamespace(winfo_rootx=lambda:100,winfo_rooty=lambda:200,
            winfo_width=lambda:1120,winfo_height=lambda:784)
        self.rect = (100,200,1120,784)
        self.native = SimpleNamespace(GetForegroundWindow=lambda:123,
            WindowFromPoint=lambda p:123,GetAncestor=lambda h,f:h)

    def test_maps_only_observed_canvas_pixels(self):
        with patch.object(desktop_lab,'user32',self.native):
            self.assertEqual(self.lab.validate_click((400,300),self.rect,7),[500,500])

    def test_rejects_outside_cancelled_stale_and_covered_targets(self):
        with patch.object(desktop_lab,'user32',self.native):
            with self.assertRaises(ValueError): self.lab.validate_click((1200,300),self.rect,7)
            with self.assertRaises(InterruptedError): self.lab.validate_click((400,300),self.rect,6)
            self.native.GetForegroundWindow=lambda:999
            with self.assertRaises(InterruptedError): self.lab.validate_click((400,300),self.rect,7)
            self.native.GetForegroundWindow=lambda:123
            self.native.WindowFromPoint=lambda p:999
            with self.assertRaises(InterruptedError): self.lab.validate_click((400,300),self.rect,7)
            self.lab.cancel.set()
            with self.assertRaises(InterruptedError): self.lab.validate_click((400,300),self.rect,7)


if __name__=='__main__': unittest.main()
