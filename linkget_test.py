import unittest
from linkget import *

class TestFactorial(unittest.TestCase):
    """
    Our basic test class
    """

    def test_logger(self):
        """
        Test the result from zen.get_quote
        """
        res = logger("test", "test")
        self.assertEqual(res, "test: test")

if __name__ == '__main__':
    unittest.main()
