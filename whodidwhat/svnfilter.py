import xml.etree.cElementTree as ET
import sys
import os
import subprocess
import argparse
import re
from datetime import datetime

import statistics
import path_functions


class SvnFilter(object):

    def __init__(self):
        self._statistics = statistics.Statistics()

    def parse_parameters_and_filter(self, argv=None):
        parameters = self.parse_parameters(argv)
        self._statistics.set_exclude_patterns(parameters.exclude)
        if parameters.input_xml:
            self._input_xmls = [SvnLogText(parameters.input_xml.read())]
        else:
            self._input_xmls = self._get_xml_logs(parameters)
        filtered_element_tree = self.filter_logs_by_users(self._input_xmls, parameters)
        if parameters.blame_folder or parameters.combine_blame:
            self.blame_active_files(parameters, filtered_element_tree)
        self.write_statistics(parameters)

    def write_statistics(self, parameters):
        if parameters.statistics_file:
            if os.path.splitext(parameters.statistics_file)[-1].lower() in ('.htm', '.html'):
                self._statistics.set_printer(statistics.HtmlPrinter(parameters.blame_folder))
            with open(parameters.statistics_file, 'w') as statistics_file:
                statistics_file.write(self._statistics.get_full())
        else:
            print(self._statistics.get_full())

    def blame_active_files(self, parameters, filtered_et):
        active_files = self.find_active_files(filtered_et)
        total_blamed_lines = ''
        for filename in active_files:
            try:
                blame_log = subprocess.check_output(self._blame_command(filename, parameters))
            except subprocess.CalledProcessError:
                continue
            team_blame, blamed_lines = self.blame_only_given_users(blame_log, filename)
            total_blamed_lines += blamed_lines
            self._write_blamefile(team_blame, filename, parameters)
        self._write_combined_blame(total_blamed_lines, parameters)

    def _blame_command(self, server_name, parameters):
        blame_command = ['svn', 'blame']
        if parameters.revision is not None:
            blame_command.extend(['-r', parameters.revision])
        return blame_command + [server_name]

    def _write_blamefile(self, team_blame, server_name, parameters):
        if self._statistics.get_changed_lines_by_files()[server_name]:
            if parameters.blame_folder:
                with open(os.path.join(parameters.blame_folder,
                                       path_functions.get_blame_name(server_name)), 'w') as blamefile:
                    blamefile.write(team_blame)

    def _write_combined_blame(self, total_blamed_lines, parameters):
        if parameters.combine_blame:
            with open(parameters.combine_blame, 'w') as combined_blame_file:
                combined_blame_file.write(total_blamed_lines)

    def get_server_name(self, filename, svnlogtexts):
        for svnlogtext in svnlogtexts:
            if svnlogtext.repository and svnlogtext.repository.prefix in filename:
                filename = filename.replace(svnlogtext.repository.prefix, '')
                filename = filename.lstrip(os.path.sep)
                return self._merge_common_parts(svnlogtext.repository.url, filename)

    def _merge_common_parts(self, repository, filename):
        repository_in_parts = path_functions.split_all(repository)
        filename_in_parts = path_functions.split_all(filename)
        for repo_part in repository_in_parts:
            if repo_part in filename_in_parts:
                filename_in_parts.remove(repo_part)
        filename = os.path.join(*filename_in_parts) if filename_in_parts else ''
        return os.path.join(repository, filename)

    def find_active_files(self, et):
        root = et.getroot()
        for logentry in root.findall('logentry'):
            author = logentry.find('author').text
            self._statistics.add_commit_count(author)
            for path in logentry.find('paths'):
                server_name = self.get_server_name(path.text, self._input_xmls)
                self._statistics.add_commit_count_of_file(server_name)
        return self._statistics.get_committed_files()

    def blame_only_given_users(self, blame_log, server_name):
        blame_file_for_team = ''
        lines_by_team_in_file = ''
        revision_and_user = re.compile(r'\s*\d+\s+\S+')
        for line in blame_log.splitlines(True):
            username = line.split()[1]
            if username in self._userlist:
                blame_file_for_team += line
                lines_by_team_in_file += line[revision_and_user.match(line).end():]
                self._statistics.add_changed_line(server_name, username)
            else:
                blame_file_for_team += self._remove_username(line, username)
        return blame_file_for_team, lines_by_team_in_file

    def _remove_username(self, line, username):
        return line.replace(username, ' ' * len(username), 1)

    def parse_parameters(self, argv):
        argv = argv if argv is not None else sys.argv
        p = argparse.ArgumentParser('Filter svn and git repositories based on list of users')
        p.add_argument('--input-xml', help='path to svn xml log input', type=file)
        p.add_argument('--users-file', help='file of usernames given line-by-line', type=argparse.FileType('r'))
        p.add_argument('--input-svn-repos', help='file of svn repository paths given line-by-line', type=file)
        p.add_argument('--output-xml', help='path for writing filtered xml')
        p.add_argument('--blame-folder', help='folder to store blames of top committed files')
        p.add_argument('-r', '--revision', help='revision info in similar format as svn log uses')
        p.add_argument('--statistics-file', help='file to store statistics on the run instead of printing on screen')
        p.add_argument('--exclude', help='file name pattern to exclude from statistics and blame', action='append')
        p.add_argument('--combine-blame', help='combine all blamed lines by team into one giant file')
        return p.parse_args(argv[1:])

    def _get_xml_logs(self, parameters):
        repositories = self._read_repository_urls(parameters.input_svn_repos)
        return [SvnLogText.from_server(repository, parameters.revision) for repository in repositories]

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

    def filter_logs_by_users(self, xml_log, parameters):
        self._userlist = self.read_userlist(parameters.users_file)
        filtered_et, _ = self.get_logs_by_users(xml_log)
        if parameters.output_xml is not None:
            filtered_et.write(parameters.output_xml, encoding='UTF-8', xml_declaration=True)
        return filtered_et

    def read_userlist(self, userlist_file):
        users = []
        for line in userlist_file:
            if line.strip() and not line.strip().startswith('#'):
                users.append(line.strip())
        return sorted(users)

    def get_logs_by_users(self, xml_logs):
        result_et, result_root = self._combine_logs_from_all_xmls_by_users(xml_logs, self._userlist)
        return self._sort_combined_tree_by_date(result_et, result_root)

    def _combine_logs_from_all_xmls_by_users(self, xml_logs, users):
        source_roots = [ET.fromstring(xml_log.log_text) for xml_log in xml_logs]
        result_root = ET.Element('log')
        result_et = ET.ElementTree(element=result_root)
        for root, xml_log in zip(source_roots, xml_logs):
            for logentry in root.findall('logentry'):
                if logentry.find('author').text in users:
                    self._prefix_paths_by_url_prefix(logentry, xml_log)
                    result_root.append(logentry)
        return result_et, result_root

    def _prefix_paths_by_url_prefix(self, logentry, xml_log):
        for path in logentry.find('paths'):
            if xml_log.repository:
                path.text = os.path.join('/', xml_log.repository.prefix, path.text[1:])

    def _sort_combined_tree_by_date(self, result_et, result_root):
        logentries = result_root.getchildren()

        def get_datetime(logentry):
            return datetime.strptime(logentry.find('date').text, '%Y-%m-%dT%H:%M:%S.%fZ')
        result_root[:] = sorted(logentries, key=get_datetime)
        return result_et, result_root


class RepositoryUrl(object):

    def __init__(self, url, prefix=''):
        self.url = url
        self.prefix = prefix


class SvnLogText(object):

    def __init__(self, log_text, repository=None):
        self.log_text = log_text
        self.repository = repository

    @classmethod
    def from_server(cls, repository, revision):
        svn_command = ['svn', 'log', '-v', '--xml']
        if revision:
            svn_command.extend(['-r', revision])
        svn_command.append('{}'.format(repository.url))
        return cls(subprocess.check_output(svn_command), repository)

