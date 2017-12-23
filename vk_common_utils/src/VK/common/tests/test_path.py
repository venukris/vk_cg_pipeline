import unittest
from VK.common.path import Path


class PathTestCases(unittest.TestCase):
    def setUp(self):
        self._path = Path("/Users/venuk/develop/scratch/presets")

    def test_get_files1(self):
        self.assertEqual(len(self._path.get_files()), 3)

    def test_get_files2(self):
        self.assertEqual(len(self._path.get_files(recursive=True)), 5)

    def test_get_files3(self):
        self.assertEqual(len(self._path.get_files(ext='json', recursive=True)), 3)


if __name__ == '__main__':
    unittest.main()
