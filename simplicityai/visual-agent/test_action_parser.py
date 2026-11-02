"""Reject executable model output and invalid screenshot coordinates."""
import unittest
from probe import parse_click


class ActionBoundary(unittest.TestCase):
    def test_pixel_point(self):
        self.assertEqual(parse_click(
            "Action: click(start_box='<|box_start|>(500,500)<|box_end|>')", 1000, 600),
            (500, 500))

    def test_rejects_executable_and_ambiguous_output(self):
        for text in [
            "Action: __import__('os').system('x')",
            "Action: click(start_box='(1001,2)')",
            "Action: click(start_box=__import__('os'))",
            "Action: click(start_box='(1,2)')\nAction: click(start_box='(2,3)')",
        ]:
            with self.subTest(text=text), self.assertRaises((ValueError, SyntaxError)):
                parse_click(text, 1000, 600)


if __name__ == '__main__':
    unittest.main()
