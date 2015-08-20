import xml.etree.cElementTree as ET
import sys
import argparse

class SvnFilter(object):

    def __init__(self):
        pass

    def get_logs_by_users(self, xml_log, users):
        tree = ET.parse(xml_log)
        root = tree.getroot()
        for logentry in root.findall('logentry'):
            if logentry.find('author').text not in users:
                root.remove(logentry)
        return tree, root

    def filter_logs_by_users(self, xml_log, userlist_file, outfile):
        userlist = self.read_userlist(userlist_file)
        filtered_et, _ = self.get_logs_by_users(xml_log, userlist)
        filtered_et.write(outfile, encoding='UTF-8', xml_declaration=True)

    def read_userlist(self, userlist_file):
        userlist = []
        for line in userlist_file:
            if line.strip() and not line.strip().startswith('#'):
                userlist.append(line.strip())
        return sorted(userlist)

    def parse_parameters_and_filter(self, argv=None):
        parameters = self.parse_parameters(argv)
        self.filter_logs_by_users(parameters.input_xml,
                                  parameters.users_file,
                                  parameters.output_xml)

    def parse_parameters(self, argv):
        argv = argv if argv is not None else sys.argv

        parser = argparse.ArgumentParser('Filter svn and git repositories based on list of users'   )
        parser.add_argument('--input-xml', help='path to svn xml log input', type=file)
        parser.add_argument('--users-file', help='file of usernames given line-by-line', type=argparse.FileType('r'))
        parser.add_argument('--output-xml', help='path for writing filtered xml')
        return parser.parse_args(argv[1:])