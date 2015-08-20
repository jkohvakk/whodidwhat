import unittest
import os
import StringIO
import filecmp
from whodidwhat.svnfilter import SvnFilter

MODULE_DIR = os.path.dirname(__file__)


class TestFilterSvn(unittest.TestCase):

    def setUp(self):
        self.svn_xml = os.path.join(MODULE_DIR, 'sample_svn.xml')
        self.log_filter = SvnFilter()

    def test_filtering_log_for_one_user(self):
        _, entries = self.log_filter.get_logs_by_users(self.svn_xml, ['jkohvakk'])
        self.assertEqual(1, len(entries))
        self.assertEqual('213', entries[0].attrib['revision'])
        self.assertEqual('jkohvakk', entries[0].find('author').text)

    def test_filtering_log_for_two_users(self):
        _, entries = self.log_filter.get_logs_by_users(self.svn_xml, ['kmikajar', 'jkohvakk'])
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
        usersfile = os.path.join(MODULE_DIR, 'userlist.txt')
        output_xml = os.path.join(MODULE_DIR, 'output.xml')
        expected_xml = os.path.join(MODULE_DIR, 'expected', 'filtered.xml')
        self.log_filter.parse_parameters_and_filter(['whodidwhat', '--input-xml', self.svn_xml,
                                                     '--users-file', usersfile,
                                                     '--output-xml', output_xml])
        self.assertTrue(filecmp.cmp(output_xml, expected_xml))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()