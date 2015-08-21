import xml.etree.cElementTree as ET
import sys
import subprocess
import argparse
from datetime import datetime


class SvnFilter(object):

    def parse_parameters_and_filter(self, argv=None):
        parameters = self.parse_parameters(argv)
        if parameters.input_xml:
            input_xmls = [parameters.input_xml.read()]
        else:
            input_xmls = self._get_xml_logs(parameters)
        self.filter_logs_by_users(input_xmls,
                                  parameters.users_file,
                                  parameters.output_xml)

    def parse_parameters(self, argv):
        argv = argv if argv is not None else sys.argv

        parser = argparse.ArgumentParser('Filter svn and git repositories based on list of users')
        parser.add_argument('--input-xml', help='path to svn xml log input', type=file)
        parser.add_argument('--users-file', help='file of usernames given line-by-line', type=argparse.FileType('r'))
        parser.add_argument('--input-svn-repos', help='file of svn repository paths given line-by-line', type=file)
        parser.add_argument('--output-xml', help='path for writing filtered xml')
        parser.add_argument('-r', '--revision', help='revision info in similar format as svn log uses')
        return parser.parse_args(argv[1:])

    def get_logs_by_users(self, xml_logs, users):
        result_et, result_root = self._combine_logs_from_all_xmls_by_users(xml_logs, users)
        return self._sort_combined_tree_by_date(result_et, result_root)

    def _combine_logs_from_all_xmls_by_users(self, xml_logs, users):
        source_roots = [ET.fromstring(xml_log) for xml_log in xml_logs]
        result_root = ET.Element('log')
        result_et = ET.ElementTree(element=result_root)
        for root in source_roots:
            for logentry in root.findall('logentry'):
                if logentry.find('author').text in users:
                    result_root.append(logentry)
        return result_et, result_root

    def _sort_combined_tree_by_date(self, result_et, result_root):
        logentries = result_root.getchildren()
        def get_datetime(logentry):
            return datetime.strptime(logentry.find('date').text, '%Y-%m-%dT%H:%M:%S.%fZ')
        result_root[:] = sorted(logentries, key=get_datetime)
        return result_et, result_root

    def filter_logs_by_users(self, xml_log, userlist_file, outfile):
        userlist = self.read_userlist(userlist_file)
        filtered_et, _ = self.get_logs_by_users(xml_log, userlist)
        filtered_et.write(outfile, encoding='UTF-8', xml_declaration=True)

    def read_userlist(self, userlist_file):
        users = []
        for line in userlist_file:
            if line.strip() and not line.strip().startswith('#'):
                users.append(line.strip())
        return sorted(users)


    def _get_xml_logs(self, parameters):
        repositories = self._read_repository_urls(parameters.input_svn_repos)
        svn_log_texts = []
        svn_command = ['svn', 'log', '-v', '--xml']
        if parameters.revision:
            svn_command.extend(['-r', parameters.revision])
        for repository in repositories:
            svn_command_with_repo = list(svn_command)
            svn_command_with_repo.append('{}'.format(repository.url))
            svn_log_texts.append(subprocess.check_output(svn_command_with_repo))
        return svn_log_texts

    def _read_repository_urls(self, fileobj):
        repos = []
        for line in fileobj:
            if line.strip() and not line.strip().startswith('#'):
                components = line.strip().split()
                if len(components) == 1:
                    repos.append(RepositoryUrl(components[0]))
                else:
                    repos.append(RepositoryUrl(components[0], components[1]))
        return repos


class RepositoryUrl(object):

    def __init__(self, url, prefix=''):
        self.url = url
        self.prefix = prefix