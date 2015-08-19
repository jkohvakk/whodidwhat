import sys
from svnfilter import SvnFilter

def whodidwhat():
    xml_filename = sys.argv[1]
    userlist_filename = sys.argv[2]
    output_filename = sys.argv[3]
    svnfilter = SvnFilter()
    svnfilter.filter_logs_by_users(xml_filename, userlist_filename, output_filename)