from whodidwhat.statistics import Statistics
import unittest


class TestStatistics(unittest.TestCase):

    def setUp(self):
        self.statistics = Statistics()
        self.statistics.add_changed_line('trunk/file1', 'jkohvakk')
        self.statistics.add_changed_line('branch/file2', 'jkohvakk')
        self.statistics.add_changed_line('branch/file2', 'jkohvakk')
        self.statistics.add_commit_count_of_file('trunk/file1')
        self.statistics.add_commit_count_of_file('branch/file2')
        self.statistics.add_commit_count('jkohvakk')

        self.statistics.add_changed_line('branch/file2', 'kmikajar')
        self.statistics.add_commit_count('kmikajar')
        self.statistics.add_commit_count_of_file('branch/file2')

        self.statistics.add_changed_line('spike/deep_nesting/file2', 'jkohvakk')
        self.statistics.add_commit_count('jkohvakk')
        self.statistics.add_commit_count_of_file('spike/deep_nesting/file2')

    def test_changed_lines_by_files_text(self):
        self.assertEqual('''\
branch/file2: 3
spike/deep_nesting/file2: 1
trunk/file1: 1
''', self.statistics.get_changed_lines_by_files_text())

    def test_changed_lines_by_folders_text(self):
        self.assertEqual('''\
---------------- level 1 ---------------------------------
branch: 3
spike: 1
trunk: 1
---------------- level 2 ---------------------------------
spike/deep_nesting: 1
''', self.statistics.get_changed_lines_by_folders_text())

    def test_changed_lines_by_users_text(self):
        self.assertEqual('''\
jkohvakk: 4
kmikajar: 1
''', self.statistics.get_changed_lines_by_users_text())

    def test_commit_counts_by_files_text(self):
        self.assertEqual('''\
branch/file2: 2
spike/deep_nesting/file2: 1
trunk/file1: 1
''', self.statistics.get_commit_counts_by_files_text())

    def test_commit_counts_by_users_text(self):
        self.assertEqual('''\
jkohvakk: 2
kmikajar: 1
''', self.statistics.get_commit_counts_by_users_text())

    def test_commit_counts_by_folders_text(self):
        self.assertEqual('''\
---------------- level 1 ---------------------------------
branch: 2
spike: 1
trunk: 1
---------------- level 2 ---------------------------------
spike/deep_nesting: 1
''', self.statistics.get_commit_counts_by_folders_text())

    def test_get_full_text(self):
        self.assertEqual('''\
==========================================================
Top changed lines by user:
jkohvakk: 4
kmikajar: 1
==========================================================
Top commit counts by user:
jkohvakk: 2
kmikajar: 1
==========================================================
Top changed lines in folders:
---------------- level 1 ---------------------------------
branch: 3
spike: 1
trunk: 1
---------------- level 2 ---------------------------------
spike/deep_nesting: 1
==========================================================
Top committed folders:
---------------- level 1 ---------------------------------
branch: 2
spike: 1
trunk: 1
---------------- level 2 ---------------------------------
spike/deep_nesting: 1
==========================================================
Top changed lines in files:
branch/file2: 3
spike/deep_nesting/file2: 1
trunk/file1: 1
==========================================================
Top commit counts in files:
branch/file2: 2
spike/deep_nesting/file2: 1
trunk/file1: 1
''', self.statistics.get_full_text())

    def test_exclude_pattern(self):
        s = Statistics()
        s.set_exclude_patterns(['*.xml', '*.txt'])
        s.add_changed_line('file.xml', 'jkohvakk')
        s.add_changed_line('file.c', 'jkohvakk')
        s.add_changed_line('file.txt', 'kmikajar')
        s.add_commit_count('jkohvakk')
        s.add_commit_count('kmikajar')
        s.add_commit_count_of_file('file.xml')
        s.add_commit_count_of_file('file.c')
        s.add_commit_count_of_file('file.txt')
        self.assertEqual(1, s.get_commit_counts_by_files()['file.c'])
        self.assertEqual(0, s.get_commit_counts_by_files()['file.xml'])
        self.assertEqual(0, s.get_commit_counts_by_files()['file.txt'])
        self.assertEqual(1, s.get_changed_lines_by_files()['file.c'])
        self.assertEqual(0, s.get_changed_lines_by_files()['file.xml'])
        self.assertEqual(0, s.get_changed_lines_by_files()['file.txt'])
        self.assertEqual(1, s.get_changed_lines_by_users()['jkohvakk'])
        self.assertEqual(0, s.get_changed_lines_by_users()['kmikajar'])


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()