import unittest
import os
import StringIO
import filecmp
import xml.etree.cElementTree as ET
from whodidwhat.svnfilter import SvnFilter, SvnLogText, RepositoryUrl

from mock import patch, call

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

    def test_parse_parameters_and_filter_one_xml(self):
        expected_xml = os.path.join(MODULE_DIR, 'expected', 'filtered.xml')
        self.log_filter.parse_parameters_and_filter(['whodidwhat', '--input-xml', self.svn_xml,
                                                     '--users-file', self.usersfile,
                                                     '--output-xml', self.output_xml])
        self.assertTrue(filecmp.cmp(self.output_xml, expected_xml))

    @patch('whodidwhat.svnfilter.subprocess.check_output')
    def test_read_log_from_svn_repo_output_xml(self, check_output_mock):
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


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()