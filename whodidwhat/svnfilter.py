import xml.etree.cElementTree as ET
import sys
import os
import subprocess
import argparse
import fnmatch
from datetime import datetime
from collections import defaultdict


class SvnFilter(object):

    def __init__(self):
        self._statistics = Statistics()

    def parse_parameters_and_filter(self, argv=None):
        parameters = self.parse_parameters(argv)
        self._statistics.set_exclude_patterns(parameters.exclude)
        if parameters.input_xml:
            self._input_xmls = [SvnLogText(parameters.input_xml.read())]
        else:
            self._input_xmls = self._get_xml_logs(parameters)
        filtered_element_tree = self.filter_logs_by_users(self._input_xmls,
                                                          parameters.users_file,
                                                          parameters.output_xml)
        if parameters.blame_folder:
            self.blame_active_files(parameters.blame_folder,
                                    filtered_element_tree)
        self.write_statistics(parameters.statistics_file)

    def write_statistics(self, statistics_filename):
        if statistics_filename:
            with open(statistics_filename, 'w') as statistics_file:
                statistics_file.write(self._statistics.get_full_text())
        else:
            print(self._statistics.get_full_text())

    def blame_active_files(self, blame_folder, filtered_et):
        active_files = self.find_active_files(filtered_et)
        for filename in active_files:
            server_name = self.get_server_name(filename, self._input_xmls)
            try:
                blame_log = subprocess.check_output(['svn', 'blame', server_name])
            except subprocess.CalledProcessError:
                continue
            team_blame = self.blame_only_given_users(blame_log, server_name)
            if self._statistics.get_changed_lines_by_files()[server_name]:
                with open(os.path.join(blame_folder, self._get_blame_name(server_name)), 'w') as blamefile:
                    blamefile.write(team_blame)

    def get_server_name(self, filename, svnlogtexts):
        for svnlogtext in svnlogtexts:
            if svnlogtext.repository and svnlogtext.repository.prefix in filename:
                filename = filename.replace(svnlogtext.repository.prefix, '')
                filename = filename.lstrip(os.path.sep)
                return self._merge_common_parts(svnlogtext.repository.url, filename)
    
    def _merge_common_parts(self, repository, filename):
        repository_in_parts = self.split_all(repository)
        filename_in_parts = self.split_all(filename)
        for repo_part in repository_in_parts:
            if repo_part in filename_in_parts:
                filename_in_parts.remove(repo_part)
        filename = os.path.join(*filename_in_parts) if filename_in_parts else ''
        return os.path.join(repository, filename)

    def split_all(self, path):
        parts = []
        while True:
            path, last = os.path.split(path)
            parts.insert(0, last)
            if not path or path == os.path.sep:
                return parts

    def _get_blame_name(self, server_name):
        blame_name = server_name.replace('://', '.')
        return blame_name.replace('/', '.')

    def find_active_files(self, et):
        root = et.getroot()
        for logentry in root.findall('logentry'):
            author = logentry.find('author').text
            self._statistics.add_commit_count(author)
            for path in logentry.find('paths'):
                self._statistics.add_commit_count_of_file(path.text)
        return self._statistics.get_committed_files()

    def blame_only_given_users(self, blame_log, server_name):
        blame_only_given = ''
        for line in blame_log.splitlines(True):
            username = line.split()[1]
            if username in self._userlist:
                blame_only_given += line
                self._statistics.add_changed_line(server_name, username)
            else:
                blame_only_given += self._remove_username(line, username)
        return blame_only_given

    def _remove_username(self, line, username):
        return line.replace(username, ' ' * len(username), 1)

    def parse_parameters(self, argv):
        argv = argv if argv is not None else sys.argv
        parser = argparse.ArgumentParser('Filter svn and git repositories based on list of users')
        parser.add_argument('--input-xml', help='path to svn xml log input', type=file)
        parser.add_argument('--users-file', help='file of usernames given line-by-line', type=argparse.FileType('r'))
        parser.add_argument('--input-svn-repos', help='file of svn repository paths given line-by-line', type=file)
        parser.add_argument('--output-xml', help='path for writing filtered xml')
        parser.add_argument('--blame-folder', help='folder to store blames of top committed files')
        parser.add_argument('-r', '--revision', help='revision info in similar format as svn log uses')
        parser.add_argument('--statistics-file', help='file to store statistics on the run instead of printing on screen')
        parser.add_argument('--exclude', help='file name pattern to exclude from statistics and blame', action='append')
        return parser.parse_args(argv[1:])

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

    def filter_logs_by_users(self, xml_log, userlist_file, outfile):
        self._userlist = self.read_userlist(userlist_file)
        filtered_et, _ = self.get_logs_by_users(xml_log)
        if outfile is not None:
            filtered_et.write(outfile, encoding='UTF-8', xml_declaration=True)
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


class Statistics(object):

    def __init__(self):
        self._blamed_lines_by_file = defaultdict(lambda: 0)
        self._blamed_lines_by_user = defaultdict(lambda: 0)
        self._commit_counts_by_file = defaultdict(lambda: 0)
        self._commit_counts_by_user = defaultdict(lambda: 0)
        self.exclude_patterns = None

    def set_exclude_patterns(self, patterns):
        self.exclude_patterns = patterns

    def add_changed_line(self, server_name, author):
        if not self._is_excluded_file(server_name):
            self._blamed_lines_by_file[server_name] += 1
            self._blamed_lines_by_user[author] += 1

    def add_commit_count(self, author):
        self._commit_counts_by_user[author] += 1

    def add_commit_count_of_file(self, filename):
        if not self._is_excluded_file(filename):
            self._commit_counts_by_file[filename] += 1

    def _is_excluded_file(self, filename):
        if self.exclude_patterns is None:
            return False
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(filename, pattern):
                return True
        return False

    def get_changed_lines_by_files(self):
        return self._blamed_lines_by_file

    def get_changed_lines_by_files_text(self):
        return self._to_text(self._blamed_lines_by_file)

    def _to_text(self, statistic):
        text = ''
        for k in sorted(statistic, key=statistic.get, reverse=True):
            text += '{}: {}\n'.format(k, statistic[k])
        return text

    def get_committed_files(self):
        return sorted(self._commit_counts_by_file, key=self._commit_counts_by_file.get, reverse=True)

    def get_commit_counts_by_files_text(self):
        return self._to_text(self._commit_counts_by_file)

    def get_commit_counts_by_files(self):
        return self._commit_counts_by_file

    def get_commit_counts_by_users(self):
        return self._commit_counts_by_user

    def get_commit_counts_by_users_text(self):
        return self._to_text(self._commit_counts_by_user)

    def get_changed_lines_by_users(self):
        return self._blamed_lines_by_user

    def get_changed_lines_by_users_text(self):
        return self._to_text(self._blamed_lines_by_user)

    def get_full_text(self):
        statistics_txt = 'Top changed lines by user\n'
        statistics_txt += self.get_changed_lines_by_users_text()
        statistics_txt += 'Top commit counts by user\n'
        statistics_txt += self.get_commit_counts_by_users_text()
        statistics_txt += 'Top changed lines:\n'
        statistics_txt += self.get_changed_lines_by_files_text()
        statistics_txt += 'Top commit counts:\n'
        statistics_txt += self.get_commit_counts_by_files_text()
        return statistics_txt