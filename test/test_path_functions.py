import unittest
import whodidwhat.path_functions


class TestFileNameFunctions(unittest.TestCase):

    def test_split_all(self):
        parts = whodidwhat.path_functions.split_all('foo/bar/daa.cpp')
        self.assertEqual(['foo', 'bar', 'daa.cpp'], parts)

    def test_get_all_folder_levels(self):
        self.assertEqual(['first'], whodidwhat.path_functions.get_all_folder_levels('first/foo.cpp'))
        self.assertEqual(['first', 'first/second'], whodidwhat.path_functions.get_all_folder_levels('first/second/foo.cpp'))


if __name__ == '__main__':
    unittest.main()
