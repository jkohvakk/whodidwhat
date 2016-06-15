import unittest
import os
import StringIO
import filecmp
import subprocess
import argparse
import xml.etree.cElementTree as ET
from mock import patch, call, Mock, MagicMock, mock_open
from whodidwhat.svnfilter import SvnFilter, SvnLogText, RepositoryUrl


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
        self.log_filter._userlist = ['jkohvakk']
        _, entries = self.log_filter.get_logs_by_users([SvnLogText(self.svn_xml_text)])
        self.assertEqual(1, len(entries))
        self.assertEqual('213', entries[0].attrib['revision'])
        self.assertEqual('jkohvakk', entries[0].find('author').text)

    def test_filtering_log_for_two_users(self):
        self.log_filter._userlist = ['kmikajar', 'jkohvakk']
        _, entries = self.log_filter.get_logs_by_users([SvnLogText(self.svn_xml_text)])
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

    @unittest.SkipTest
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

    @patch('whodidwhat.svnfilter.subprocess.check_output')
    @patch('whodidwhat.svnfilter.sys.stdout')
    @patch('whodidwhat.svnfilter.SvnFilter.filter_logs_by_users')
    def test_reading_exclude_pattern(self, filter_logs_by_users_mock, mock_stdout, mock_check_output):
        svn_repos = os.path.join(MODULE_DIR, 'sample_data', 'svn_repos.txt')
        self.log_filter.parse_parameters_and_filter(['whodidwhat', '--input-svn-repos', svn_repos,
                                                     '--users-file', self.usersfile,
                                                     '--output-xml', self.output_xml,
                                                     '--exclude', '*.xml',
                                                     '--exclude', '*.qc',
                                                     '-r', '1234:HEAD'])
        self.assertEqual(['*.xml', '*.qc'], self.log_filter._statistics.exclude_patterns) 

    @patch('whodidwhat.svnfilter.sys.stdout')
    @patch('whodidwhat.svnfilter.SvnFilter.filter_logs_by_users')
    @patch('whodidwhat.svnfilter.SvnFilter.blame_active_files')
    def test_reading_collect_blame(self, blame_active_files_mock, filter_logs_by_users_mock, stdout_mock):
        mock_et = MagicMock()
        filter_logs_by_users_mock.return_value = mock_et

        self.log_filter.parse_parameters_and_filter(['whodidwhat',
                                                     '--input-xml', self.svn_xml,
                                                     '--users-file', self.usersfile,
                                                     '--combine-blame', 'combined_blame.cpp',
                                                     '--blame-folder', 'blame'])

        call_params = blame_active_files_mock.mock_calls[0][1][0]
        call_et = blame_active_files_mock.mock_calls[0][1][1]
        self.assertEqual('blame', call_params.blame_folder)
        self.assertEqual('combined_blame.cpp', call_params.combine_blame)
        self.assertEqual(None, call_params.revision)
        self.assertEqual(mock_et, call_et)

    @patch('whodidwhat.svnfilter.SvnFilter.read_userlist')
    @patch('whodidwhat.svnfilter.SvnFilter.get_logs_by_users')
    def test_if_output_xml_is_not_given_writing_is_skipped(self, get_logs_by_users_mock, read_userlist_mock):
        et_mock = Mock()
        get_logs_by_users_mock.return_value = (et_mock, Mock())
        params = argparse.Namespace(users_file='userlist_file', output_xml=None)
        self.log_filter.filter_logs_by_users('xml_log', params)
        self.assertEqual([], et_mock.write.mock_calls)

    def test_filtering_two_logs_for_one_user(self):
        with open(os.path.join(MODULE_DIR, 'sample_data', 'another_sample_svn.xml')) as another_xml:
            another_xml_text = another_xml.read()
        self.log_filter._userlist = ['kmikajar', 'jkohvakk']
        _, entries = self.log_filter.get_logs_by_users([SvnLogText(another_xml_text),
                                                        SvnLogText(self.svn_xml_text)])
        self.assertEqual(4, len(entries))
        self.assertEqual('210', entries[0].attrib['revision'])
        self.assertEqual('440', entries[1].attrib['revision'])
        self.assertEqual('441', entries[2].attrib['revision'])
        self.assertEqual('213', entries[3].attrib['revision'])

    def test_prefixing_urls(self):
        repo = RepositoryUrl('https://svn.com', 'foo/bar')
        self.log_filter._userlist = ['jkohvakk']
        _, entries = self.log_filter.get_logs_by_users([SvnLogText(self.svn_xml_text, repo)])
        self.assertEqual('/foo/bar/python_intermediate/exercises/number_guessing_game/tst/test_number_guessing_game.py',
                         entries[0].find('paths')[1].text)

    def test_find_active_files(self):
        xml_log_text = [SvnLogText(self.svn_xml_text, RepositoryUrl('https://svn.com/'))]
        self.log_filter._input_xmls = xml_log_text
        self.log_filter._userlist = ['kmikajar', 'jkohvakk', 'dems1e72']

        tree, _ = self.log_filter.get_logs_by_users(xml_log_text)

        self.assertEqual(['https://svn.com/tdd_in_c/dynamic_linker_seam/sut.c',
                          'https://svn.com/tdd_in_c/exercises/CCS_Refactoring_AaSysTime/CCS_Services/AaSysTime/ut/Fakes.c',
                          'https://svn.com/python_intermediate/exercises/number_guessing_game/tst/test_number_guessing_game.py',
                          'https://svn.com/python_intermediate/exercises/number_guessing_game/src/number_guessing_game.py'],
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
    def test_combine_blame(self, open_mock, check_output_mock):
        xml_log_text = [SvnLogText(self.SMALLEST_XML, RepositoryUrl('https://svn.com/', 'python_intermediate'))]
        self.log_filter._input_xmls = xml_log_text
        self.log_filter._userlist = ['kmikajar', 'jkohvakk', 'dems1e72']
        tree, _ = self.log_filter.get_logs_by_users(xml_log_text)
        check_output_mock.return_value = self.RAW_BLAME_TEXT
        params = argparse.Namespace(blame_folder=None, combine_blame='combine.cpp', revision='{2015-08-01}:HEAD')

        self.log_filter.blame_active_files(params, tree)

        check_output_mock.assert_called_once_with(['svn', 'blame', '-r', '{2015-08-01}:HEAD',
                                                   'https://svn.com/exercises/number_guessing_game/tst/test_number_guessing_game.py'])
        open_mock.assert_called_once_with('combine.cpp', 'w')
        open_mock().write.assert_called_with(self.LINES_BY_TEAM)

    @patch('whodidwhat.svnfilter.os')
    def test_blame_active_files_creates_blame_folder_if_it_does_not_exits(self, os_mock):
        tree = MagicMock()
        params = argparse.Namespace(blame_folder='blame', combine_blame=None, revision=None)
        os_mock.path.isdir.return_value = False

        self.log_filter.blame_active_files(params, tree)

        os_mock.path.isdir.assert_called_once_with('blame')
        os_mock.mkdir.assert_called_once_with('blame')

    @patch('whodidwhat.svnfilter.os.mkdir')
    @patch('whodidwhat.svnfilter.subprocess.check_output')
    @patch('__builtin__.open', new_callable=mock_open)
    def test_blame_active_files_happy_path(self, open_mock, check_output_mock, ignore_mkdir):
        xml_log_text = [SvnLogText(self.SMALLEST_XML, RepositoryUrl('https://svn.com/', 'python_intermediate'))]
        self.log_filter._input_xmls = xml_log_text
        self.log_filter._userlist = ['kmikajar', 'jkohvakk', 'dems1e72']
        tree, _ = self.log_filter.get_logs_by_users(xml_log_text)
        check_output_mock.return_value = self.RAW_BLAME_TEXT
        params = argparse.Namespace(blame_folder='blame', combine_blame=None, revision=None)

        self.log_filter.blame_active_files(params, tree)

        check_output_mock.assert_called_once_with(['svn', 'blame', 'https://svn.com/exercises/number_guessing_game/tst/test_number_guessing_game.py'])
        open_mock.assert_called_once_with('blame' + os.path.sep + 'https.svn.com.exercises.number_guessing_game.tst.test_number_guessing_game.py', 'w')
        open_mock().write.assert_called_with(self.EXPECTED_BLAME_ONLY)
        self.assertEqual(self.log_filter._statistics.printer.write(self.log_filter._statistics.get_changed_lines_by_files()),
                         'https://svn.com/exercises/number_guessing_game/tst/test_number_guessing_game.py: 6\n')

    @patch('whodidwhat.svnfilter.os.mkdir')
    @patch('whodidwhat.svnfilter.SvnFilter.blame_only_given_users')
    @patch('whodidwhat.svnfilter.subprocess.check_output')
    @patch('__builtin__.open', new_callable=mock_open)
    def test_blame_active_files_no_blame_written_if_file_deleted_from_svn(self, open_mock, check_output_mock,
                                                                          blame_only_given_users_mock, ignore_mkdir):
        blame_only_given_users_mock.return_value = ('This is blame of 1 line', 1)
        check_output_mock.side_effect = subprocess.CalledProcessError(1, 'Path not found')
        xml_log_text = [SvnLogText(self.SMALLEST_XML, RepositoryUrl('https://svn.com/', 'python_intermediate'))]
        self.log_filter._input_xmls = xml_log_text
        self.log_filter._userlist = ['kmikajar', 'jkohvakk', 'dems1e72']
        tree, _ = self.log_filter.get_logs_by_users(xml_log_text)
        check_output_mock.return_value = self.RAW_BLAME_TEXT
        params = argparse.Namespace(blame_folder='blame', combine_blame=None, revision=None)

        self.log_filter.blame_active_files(params, tree)

        check_output_mock.assert_called_once_with(['svn', 'blame', 'https://svn.com/exercises/number_guessing_game/tst/test_number_guessing_game.py'])
        self.assertEqual([], open_mock().write.mock_calls)

    @patch('whodidwhat.svnfilter.os.mkdir')
    @patch('whodidwhat.svnfilter.subprocess.check_output')
    @patch('__builtin__.open', new_callable=mock_open)
    def test_blame_active_files_no_blame_written_if_no_more_blamed_lines_by_team(self, open_mock, check_output_mock,
                                                                                 ignore_mkdir):
        xml_log_text = [SvnLogText(self.SMALLEST_XML, RepositoryUrl('https://svn.com/', 'python_intermediate'))]
        self.log_filter._input_xmls = xml_log_text
        self.log_filter._userlist = ['happydude']
        tree, _ = self.log_filter.get_logs_by_users(xml_log_text)
        check_output_mock.return_value = self.RAW_BLAME_TEXT
        params = argparse.Namespace(blame_folder='blame', combine_blame=None, revision=None)

        self.log_filter.blame_active_files(params, tree)

        self.assertEqual([], open_mock().write.mock_calls)

    def test_get_server_name(self):
        log_texts = [SvnLogText('', RepositoryUrl('https://svn.com/foo/bar/dadadii', 'foobar')),
                     SvnLogText('', RepositoryUrl('https://googlecode.com/statsvn', 'statsvn'))]
        self.assertEqual('https://googlecode.com/statsvn/stats.cpp',
                         self.log_filter.get_server_name('/statsvn/stats.cpp', log_texts))
        self.assertEqual('https://svn.com/foo/bar/dadadii/stats.cpp',
                         self.log_filter.get_server_name('/foobar/bar/dadadii/stats.cpp', log_texts))

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

    LINES_BY_TEAM = '''\

     ROBOT_LIBRARY_SCOPE = 'GLOBAL'

     def __init__(self):
         self._init_caches()

'''

    def test_blame_only_given_users(self):
        self.log_filter._userlist = ['jkohvakk', 'kmikajar']
        self.assertEqual((self.EXPECTED_BLAME_ONLY, self.LINES_BY_TEAM),
                         self.log_filter.blame_only_given_users(self.RAW_BLAME_TEXT, 'dummy_server_name'))
        self.assertEqual(3, self.log_filter._statistics.get_changed_lines_by_users()['jkohvakk'])
        self.assertEqual(3, self.log_filter._statistics.get_changed_lines_by_users()['kmikajar'])


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
