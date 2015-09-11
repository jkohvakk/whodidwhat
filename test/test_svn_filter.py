import unittest
import os
import StringIO
import filecmp
import subprocess
import xml.etree.cElementTree as ET
from whodidwhat.svnfilter import SvnFilter, SvnLogText, RepositoryUrl, Statistics

from mock import patch, call, Mock, mock_open

MODULE_DIR = os.path.dirname(__file__)


class TestFilterSvn(unittest.TestCase):

    def setUp(self):
        self.svn_xml = os.path.join(MODULE_DIR, 'sample_data', 'sample_svn.xml')
        with open(self.svn_xml) as sample_xml_file:
            self.svn_xml_text = sample_xml_file.read()
        self.usersfile = os.path.join(MODULE_DIR, 'sample_data', 'userlist.txt')
        self.output_xml = os.path.join(MODULE_DIR, 'output.xml')
        self.log_filter = SvnFilter()

    def test_filtering_log_for_one_user(self):
        _, entries = self.log_filter.get_logs_by_users([SvnLogText(self.svn_xml_text)], ['jkohvakk'])
        self.assertEqual(1, len(entries))
        self.assertEqual('213', entries[0].attrib['revision'])
        self.assertEqual('jkohvakk', entries[0].find('author').text)

    def test_filtering_log_for_two_users(self):
        _, entries = self.log_filter.get_logs_by_users([SvnLogText(self.svn_xml_text)], ['kmikajar', 'jkohvakk'])
        self.assertEqual(2, len(entries))
        self.assertEqual('210', entries[0].attrib['revision'])
        self.assertEqual('kmikajar', entries[0].find('author').text)
        self.assertEqual('213', entries[1].attrib['revision'])
        self.assertEqual('jkohvakk', entries[1].find('author').text)

    def test_read_userlist(self):
        userlist = '''
#userlistfile
#jkohvakk to make sure we really do not parse comments
jkohvakk
kmikajar
basvodde

'''
        self.assertEqual(['basvodde', 'jkohvakk', 'kmikajar'],
                         self.log_filter.read_userlist(StringIO.StringIO(userlist)))

    @patch('whodidwhat.svnfilter.sys.stdout')
    def test_parse_parameters_and_filter_one_xml(self, mock_stdout):
        expected_xml = os.path.join(MODULE_DIR, 'expected', 'filtered.xml')
        self.log_filter.parse_parameters_and_filter(['whodidwhat', '--input-xml', self.svn_xml,
                                                     '--users-file', self.usersfile,
                                                     '--output-xml', self.output_xml])
        self.assertTrue(filecmp.cmp(self.output_xml, expected_xml))

    @patch('whodidwhat.svnfilter.sys.stdout')
    @patch('whodidwhat.svnfilter.subprocess.check_output')
    def test_read_log_from_svn_repo_output_xml(self, check_output_mock, mock_stdout):
        check_output_mock.return_value = self.svn_xml_text
        svn_repos = os.path.join(MODULE_DIR, 'sample_data', 'svn_repos.txt')
        self.log_filter.parse_parameters_and_filter(['whodidwhat', '--input-svn-repos', svn_repos,
                                                     '--users-file', self.usersfile,
                                                     '--output-xml', self.output_xml,
                                                     '-r', '1234:HEAD'])
        expected_check_output = [call(['svn', 'log', '-v', '--xml', '-r', '1234:HEAD',
                                       'https://svn.com/isource/svnroot/training/python_intermediate/solutions']),
                                 call(['svn', 'log', '-v', '--xml', '-r', '1234:HEAD',
                                       'https://svn.com/isource/svnroot/training/tdd_in_c'])]
        self.assertEqual(expected_check_output, check_output_mock.mock_calls)

    @patch('whodidwhat.svnfilter.SvnFilter.read_userlist')
    @patch('whodidwhat.svnfilter.SvnFilter.get_logs_by_users')
    def test_if_output_xml_is_not_given_writing_is_skipped(self, get_logs_by_users_mock, read_userlist_mock):
        et_mock = Mock()
        get_logs_by_users_mock.return_value = (et_mock, Mock())
        self.log_filter.filter_logs_by_users('xml_log', 'userlist_file', None)
        self.assertEqual([], et_mock.write.mock_calls)

    def test_filtering_two_logs_for_one_user(self):
        with open(os.path.join(MODULE_DIR, 'sample_data', 'another_sample_svn.xml')) as another_xml:
            another_xml_text = another_xml.read()
        _, entries = self.log_filter.get_logs_by_users([SvnLogText(another_xml_text),
                                                        SvnLogText(self.svn_xml_text)],
                                                       ['kmikajar', 'jkohvakk'])
        self.assertEqual(4, len(entries))
        self.assertEqual('210', entries[0].attrib['revision'])
        self.assertEqual('440', entries[1].attrib['revision'])
        self.assertEqual('441', entries[2].attrib['revision'])
        self.assertEqual('213', entries[3].attrib['revision'])

    def test_prefixing_urls(self):
        repo = RepositoryUrl('https://svn.com', 'foo/bar')
        _, entries = self.log_filter.get_logs_by_users([SvnLogText(self.svn_xml_text, repo)], ['jkohvakk'])
        self.assertEqual('/foo/bar/python_intermediate/exercises/number_guessing_game/tst/test_number_guessing_game.py',
                         entries[0].find('paths')[0].text)

    @unittest.SkipTest
    @patch('whodidwhat.svnfilter.subprocess.check_output')
    def test_creating_blame_files(self, check_output_mock):
        check_output_mock.return_value = self.svn_xml_text
        svn_repos = os.path.join(MODULE_DIR, 'sample_data', 'svn_repos.txt')
        self.log_filter.parse_parameters_and_filter(['whodidwhat', '--input-svn-repos', svn_repos,
                                                     '--users-file', os.path.join(MODULE_DIR, 'sample_data', 'dems1e72_users.txt'),
                                                     '--blame-folder', os.path.join(MODULE_DIR, 'blame'),
                                                     '--blame-limit', '1',
                                                     '-r', '1234:HEAD'])
        expected_check_output = [call(['svn', 'log', '-v', '--xml', '-r', '1234:HEAD',
                                       'https://svn.com/isource/svnroot/training/python_intermediate/solutions']),
                                 call(['svn', 'log', '-v', '--xml', '-r', '1234:HEAD',
                                       'https://svn.com/isource/svnroot/training/tdd_in_c'])]
        # The call below is not very good. Problem is in stupidly put svn_repos.txt
        expected_check_output.append(call(['svn', 'blame', 'https://svn.com/isource/svnroot/training/tdd_in_c/tdd_in_c/dynamic_linker_seam/sut.c']))
        self.assertEqual(expected_check_output, check_output_mock.mock_calls)

    def test_find_active_files(self):
        tree, _ = self.log_filter.get_logs_by_users([SvnLogText(self.svn_xml_text)], ['kmikajar', 'jkohvakk', 'dems1e72'])
        self.assertEqual(['/tdd_in_c/dynamic_linker_seam/sut.c',
                          '/python_intermediate/exercises/number_guessing_game/tst/test_number_guessing_game.py',
                          '/tdd_in_c/exercises/CCS_Refactoring_AaSysTime/CCS_Services/AaSysTime/ut/Fakes.c'],
                         self.log_filter.find_active_files(tree))
        self.assertEqual(1, self.log_filter._statistics.get_commit_counts_by_users()['kmikajar'])
        self.assertEqual(2, self.log_filter._statistics.get_commit_counts_by_users()['dems1e72'])
        self.assertEqual(1, self.log_filter._statistics.get_commit_counts_by_users()['jkohvakk'])

    SMALLEST_XML = '''\
<?xml version="1.0" encoding="UTF-8"?>
<log>
<logentry
   revision="213">
<author>jkohvakk</author>
<date>2015-05-14T07:58:14.727598Z</date>
<paths>
<path
   action="A"
   prop-mods="false"
   text-mods="true"
   kind="file">/python_intermediate/exercises/number_guessing_game/tst/test_number_guessing_game.py</path>
</paths>
<msg>Added starting point of number guessing game exercise</msg>
</logentry>
</log>'''

    @patch('whodidwhat.svnfilter.subprocess.check_output')
    @patch('__builtin__.open', new_callable=mock_open)
    def test_blame_active_files_happy_path(self, open_mock, check_output_mock):
        xml_log_text = [SvnLogText(self.SMALLEST_XML, RepositoryUrl('https://svn.com/', 'python_intermediate'))]
        self.log_filter._input_xmls = xml_log_text
        self.log_filter._userlist = ['kmikajar', 'jkohvakk', 'dems1e72']
        tree, _ = self.log_filter.get_logs_by_users(xml_log_text,
                                                    ['kmikajar', 'jkohvakk', 'dems1e72'])
        check_output_mock.return_value = self.RAW_BLAME_TEXT

        self.log_filter.blame_active_files('blame', tree)

        check_output_mock.assert_called_once_with(['svn', 'blame', 'https://svn.com/exercises/number_guessing_game/tst/test_number_guessing_game.py'])
        open_mock().write.assert_called_with(self.EXPECTED_BLAME_ONLY)
        self.assertEqual(self.log_filter._statistics.get_changed_lines_by_files_text(),
                         'https://svn.com/exercises/number_guessing_game/tst/test_number_guessing_game.py: 6\n')

    @patch('whodidwhat.svnfilter.SvnFilter.blame_only_given_users')
    @patch('whodidwhat.svnfilter.subprocess.check_output')
    @patch('__builtin__.open', new_callable=mock_open)
    def test_blame_active_files_no_blame_written_if_file_deleted_from_svn(self, open_mock, check_output_mock, blame_only_given_users_mock):
        blame_only_given_users_mock.return_value = ('This is blame of 1 line', 1)
        check_output_mock.side_effect = subprocess.CalledProcessError(1, 'Path not found')
        xml_log_text = [SvnLogText(self.SMALLEST_XML, RepositoryUrl('https://svn.com/', 'python_intermediate'))]
        self.log_filter._input_xmls = xml_log_text
        self.log_filter._userlist = ['kmikajar', 'jkohvakk', 'dems1e72']
        tree, _ = self.log_filter.get_logs_by_users(xml_log_text,
                                                    ['kmikajar', 'jkohvakk', 'dems1e72'])
        check_output_mock.return_value = self.RAW_BLAME_TEXT

        self.log_filter.blame_active_files('blame', tree)

        check_output_mock.assert_called_once_with(['svn', 'blame', 'https://svn.com/exercises/number_guessing_game/tst/test_number_guessing_game.py'])
        self.assertEqual([], open_mock().write.mock_calls)


    def test_get_server_name(self):
        log_texts = [SvnLogText('', RepositoryUrl('https://svn.com/foo/bar', 'foobar')),
                     SvnLogText('', RepositoryUrl('https://googlecode.com/statsvn', 'statsvn'))]
        self.assertEqual('https://googlecode.com/statsvn/stats.cpp',
                         self.log_filter.get_server_name('/statsvn/stats.cpp', log_texts))

    RAW_BLAME_TEXT = '''\
308498   jawinter class RammbockCore(object):
308499   jkohvakk 
308499   jkohvakk     ROBOT_LIBRARY_SCOPE = 'GLOBAL'
308499   jkohvakk 
308500   kmikajar     def __init__(self):
308500   kmikajar         self._init_caches()
308500   kmikajar 
308498   jawinter     def _init_caches(self):
308498   jawinter         self._protocol_in_progress = None
308498   jawinter         self._protocols = {}
365453   jawinter         self._servers = _NamedCache('server', "No servers defined!")'''

    EXPECTED_BLAME_ONLY = '''\
308498            class RammbockCore(object):
308499   jkohvakk 
308499   jkohvakk     ROBOT_LIBRARY_SCOPE = 'GLOBAL'
308499   jkohvakk 
308500   kmikajar     def __init__(self):
308500   kmikajar         self._init_caches()
308500   kmikajar 
308498                def _init_caches(self):
308498                    self._protocol_in_progress = None
308498                    self._protocols = {}
365453                    self._servers = _NamedCache('server', "No servers defined!")'''

    def test_blame_only_given_users(self):
        self.log_filter._userlist = ['jkohvakk', 'kmikajar']
        self.assertEqual(self.EXPECTED_BLAME_ONLY,
                         self.log_filter.blame_only_given_users(self.RAW_BLAME_TEXT, 'dummy_server_name'))
        self.assertEqual(3, self.log_filter._statistics.get_changed_lines_by_users()['jkohvakk'])
        self.assertEqual(3, self.log_filter._statistics.get_changed_lines_by_users()['kmikajar'])


class TestStatistics(unittest.TestCase):

    def setUp(self):
        self.statistics = Statistics() 
        self.statistics.add_changed_line('file1', 'jkohvakk')
        self.statistics.add_changed_line('file2', 'jkohvakk')
        self.statistics.add_changed_line('file2', 'kmikajar')
        self.statistics.add_commit_count('file1', 'jkohvakk')
        self.statistics.add_commit_count('file2', 'jkohvakk')
        self.statistics.add_commit_count('file2', 'kmikajar')

    def test_changed_lines_by_files_text(self):
        self.assertEqual('''\
file2: 2
file1: 1
''', self.statistics.get_changed_lines_by_files_text())

    def test_changed_lines_by_users_text(self):
        self.assertEqual('''\
jkohvakk: 2
kmikajar: 1
''', self.statistics.get_changed_lines_by_users_text())

    def test_commit_counts_by_files_text(self):
        self.assertEqual('''\
file2: 2
file1: 1
''', self.statistics.get_commit_counts_by_files_text())

    def test_commit_counts_by_users_text(self):
        self.assertEqual('''\
jkohvakk: 2
kmikajar: 1
''', self.statistics.get_commit_counts_by_users_text())

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
    