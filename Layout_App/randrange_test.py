import unittest
from randrange import randrange

class RandomRangeTest(unittest.TestCase):

    def test_random_range(self):
        value = randrange(7, 8, 10)
        self.assertEqual(7 <= value <= 8, True)

        value = randrange(0.5, 0.6, 100)
        self.assertEqual(0.5 <= value <= 0.6, True)

        value = randrange(5, 7, 20)
        self.assertEqual(5 <= value <= 7, True)
        return

if __name__ == '__main__':
    unittest.main()