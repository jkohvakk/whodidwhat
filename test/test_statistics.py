from whodidwhat.statistics import Statistics, HtmlPrinter
from whodidwhat.path_functions import get_blame_name
import unittest
import xml.etree.ElementTree as ET
import mock

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
''', self.statistics.printer.write(self.statistics.get_changed_lines_by_files()))

    def test_changed_lines_by_folders_text(self):
        self.assertEqual('''\
---------------- level 1 ---------------------------------
branch: 3
spike: 1
trunk: 1
---------------- level 2 ---------------------------------
spike/deep_nesting: 1
''', self.statistics.printer.write_folders(self.statistics.get_changed_lines_by_folders()))

    def test_changed_lines_by_users_text(self):
        self.assertEqual('''\
jkohvakk: 4
kmikajar: 1
''', self.statistics.printer.write(self.statistics.get_changed_lines_by_users()))

    def test_commit_counts_by_files_text(self):
        self.assertEqual('''\
branch/file2: 2
spike/deep_nesting/file2: 1
trunk/file1: 1
''', self.statistics.printer.write(self.statistics.get_commit_counts_by_files()))

    def test_commit_counts_by_users_text(self):
        self.assertEqual('''\
jkohvakk: 2
kmikajar: 1
''', self.statistics.printer.write(self.statistics.get_commit_counts_by_users()))

    def test_commit_counts_by_folders_text(self):
        self.assertEqual('''\
---------------- level 1 ---------------------------------
branch: 2
spike: 1
trunk: 1
---------------- level 2 ---------------------------------
spike/deep_nesting: 1
''', self.statistics.printer.write_folders(self.statistics.get_commit_counts_by_folders()))

    def test_get_full(self):
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
''', self.statistics.get_full())

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

    def test_limit_in_to_text(self):
        s = Statistics()
        data = {'foo': 4, 'bar': 10, 'daa': 5, 'dii': 2}
        self.assertEqual('''\
bar: 10
daa: 5
foo: 4
''', s.printer.write(data, 3))


class TestHtmlStatistics(unittest.TestCase):

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
        self.statistics.set_printer(HtmlPrinter(None))

    def test_changed_lines_by_users(self):
        self.assertEqual('''\
<table>\
<tr><td>jkohvakk</td><td>4</td></tr>\
<tr><td>kmikajar</td><td>1</td></tr>\
</table>''', ET.tostring(self.statistics.printer.write(self.statistics.get_changed_lines_by_users()),
                         method='html'))

    def test_changed_lines_by_files_no_blame(self):
        self.assertEqual('''\
<table>\
<tr><td><a href="branch/file2">branch/file2</a></td><td>3</td></tr>\
<tr><td><a href="spike/deep_nesting/file2">spike/deep_nesting/file2</a></td><td>1</td></tr>\
<tr><td><a href="trunk/file1">trunk/file1</a></td><td>1</td></tr>\
</table>''', ET.tostring(self.statistics.printer.write_links(self.statistics.get_changed_lines_by_files()),
                         method='html'))

    @mock.patch('whodidwhat.statistics.os.path.exists')
    def test_changed_lines_by_files_with_blames(self, os_path_exists):
        os_path_exists.return_value = True
        self.statistics.set_printer(HtmlPrinter('blame'))
        self.assertEqual('''\
<table>\
<tr><td><a href="branch/file2">branch/file2</a></td><td><a href="blame/branch.file2">blame</a></td><td>3</td></tr>\
<tr><td><a href="spike/deep_nesting/file2">spike/deep_nesting/file2</a></td><td><a href="blame/spike.deep_nesting.file2">blame</a></td><td>1</td></tr>\
<tr><td><a href="trunk/file1">trunk/file1</a></td><td><a href="blame/trunk.file1">blame</a></td><td>1</td></tr>\
</table>''', ET.tostring(self.statistics.printer.write_links(self.statistics.get_changed_lines_by_files()),
                         method='html'))

    def test_commit_counts_by_folders(self):
        self.assertEqual('''\
<table>\
<tr>\
<td>level</td><td>1</td>\
<td><table>\
<tr><td><a href="branch">branch</a></td><td>2</td></tr>\
<tr><td><a href="spike">spike</a></td><td>1</td></tr>\
<tr><td><a href="trunk">trunk</a></td><td>1</td></tr>\
</table></td>\
</tr>\
<tr>\
<td>level</td><td>2</td>\
<td><table>\
<tr><td><a href="spike/deep_nesting">spike/deep_nesting</a></td><td>1</td></tr>\
</table></td>\
</tr>\
</table>\
''', ET.tostring(self.statistics.printer.write_folders(self.statistics.get_commit_counts_by_folders()),
                 method='html'))

    def test_top_changed_lines_by_user_header(self):
        self.assertEqual('<h2>Top changed lines by user</h2>',
                         ET.tostring(self.statistics.printer.top_changed_lines_by_user_header()))

    def test_top_commit_counts_by_user_header(self):
        self.assertEqual('<h2>Top commit counts by user</h2>',
                         ET.tostring(self.statistics.printer.top_commit_counts_by_user_header()))

    def test_top_changed_lines_in_folders_header(self):
        self.assertEqual('<h2>Top changed lines in folders</h2>',
                         ET.tostring(self.statistics.printer.top_changed_lines_in_folders_header()))

    def test_top_commit_counts_in_folders_header(self):
        self.assertEqual('<h2>Top commit counts in folders</h2>',
                         ET.tostring(self.statistics.printer.top_commit_counts_in_folders_header()))

    def test_top_changed_lines_in_files_header(self):
        self.assertEqual('<h2>Top changed lines in files</h2>',
                         ET.tostring(self.statistics.printer.top_changed_lines_in_files_header()))

    def test_top_commit_counts_in_files_header(self):
        self.assertEqual('<h2>Top commit counts in files</h2>',
                         ET.tostring(self.statistics.printer.top_commit_counts_in_files_header()))

    @mock.patch('whodidwhat.statistics.os.path.exists')
    def test_write_full_html(self, os_path_exists):
        os_path_exists.return_value = True
        self.statistics.set_printer(HtmlPrinter('blame'))
        open('test.html', 'w').write(self.statistics.get_full())


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()