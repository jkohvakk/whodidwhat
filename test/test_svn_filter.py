import unittest
import os
import StringIO
from whodidwhat.svnfilter import SvnFilter

MODULE_DIR = os.path.dirname(__file__)


class TestFilterSvn(unittest.TestCase):

    def test_filtering_log_for_one_user(self):
        sample_file = os.path.join(MODULE_DIR, 'sample_svn.xml')
        log_filter = SvnFilter()
        entries = log_filter.get_logs_by_users(sample_file, ['jkohvakk'])
        self.assertEqual(1, len(entries))
        self.assertEqual('213', entries[0].attrib['revision'])
        self.assertEqual('jkohvakk', entries[0].find('author').text)

    def test_filtering_log_for_two_users(self):
        sample_file = os.path.join(MODULE_DIR, 'sample_svn.xml')
        log_filter = SvnFilter()
        entries = log_filter.get_logs_by_users(sample_file, ['kmikajar', 'jkohvakk'])
        self.assertEqual(2, len(entries))
        self.assertEqual('210', entries[0].attrib['revision'])
        self.assertEqual('kmikajar', entries[0].find('author').text)
        self.assertEqual('213', entries[1].attrib['revision'])
        self.assertEqual('jkohvakk', entries[1].find('author').text)

    def test_read_userlist(self):
        userlist = '''
#userlistfile
jkohvakk
kmikajar
basvodde

'''
        self.assertEqual(['basvodde', 'jkohvakk', 'kmikajar'],
                         SvnFilter().read_userlist(StringIO.StringIO(userlist)))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()