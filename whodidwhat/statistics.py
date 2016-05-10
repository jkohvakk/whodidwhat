from collections import defaultdict
import fnmatch
import path_functions


class Statistics(object):

    def __init__(self):
        self._blamed_lines_by_file = defaultdict(lambda: 0)
        self._blamed_lines_by_user = defaultdict(lambda: 0)
        self._commit_counts_by_file = defaultdict(lambda: 0)
        self._commit_counts_by_user = defaultdict(lambda: 0)
        self.exclude_patterns = None
        self.printer = TextPrinter()

    def set_printer(self, printer):
        self.printer = printer

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

    def get_committed_files(self):
        return sorted(self._commit_counts_by_file, key=self._commit_counts_by_file.get, reverse=True)

    def get_commit_counts_by_files(self):
        return self._commit_counts_by_file

    def get_commit_counts_by_users(self):
        return self._commit_counts_by_user

    def get_changed_lines_by_users(self):
        return self._blamed_lines_by_user

    def get_changed_lines_by_folders(self):
        return self._get_changes_by_folders(self._blamed_lines_by_file)

    def _get_changes_by_folders(self, changes):
        folder_changes = []
        for f in changes:
            folders = path_functions.get_all_folder_levels(f)
            for level, folder in enumerate(folders):
                if len(folder_changes) <= level:
                    folder_changes.append(defaultdict(lambda: 0))
                folder_changes[level][folder] += changes[f]
        return folder_changes

    def get_commit_counts_by_folders(self):
        return self._get_changes_by_folders(self._commit_counts_by_file)

    def get_full(self):
        statistics = self.printer.top_changed_lines_by_user_header()
        statistics += self.printer.write(self.get_changed_lines_by_users())
        statistics += self.printer.top_commit_counts_by_user_header()
        statistics += self.printer.write(self.get_commit_counts_by_users())
        statistics += self.printer.top_changed_lines_in_folders_header()
        statistics += self.printer.write_folders(self.get_changed_lines_by_folders())
        statistics += self.printer.top_commit_counts_in_folders_header()
        statistics += self.printer.write_folders(self.get_commit_counts_by_folders())
        statistics += self.printer.top_changed_lines_in_files_header()
        statistics += self.printer.write(self.get_changed_lines_by_files())
        statistics += self.printer.top_commit_counts_in_files_header()
        statistics += self.printer.write(self.get_commit_counts_by_files())
        return statistics


class HtmlPrinter(object):

    def __init__(self, blame_folder):
        self._blame_folder = blame_folder


class TextPrinter(object):

    def write(self, statistic, limit=None):
        text = ''
        limit = limit if limit is not None else len(statistic)
        for item in sorted(statistic.items(), key=lambda it: (-it[1], it[0]))[:limit]:
            text += '{}: {}\n'.format(item[0], item[1])
        return text

    def write_folders(self, level_list):
        total_text = ''
        for i, folder_level in enumerate(level_list):
            total_text += '---------------- level {} ---------------------------------\n'.format(i + 1)
            total_text += self.write(folder_level, 7)
        return total_text

    def top_changed_lines_by_user_header(self):
        return '''\
==========================================================
Top changed lines by user:
'''

    def top_commit_counts_by_user_header(self):
        return '''\
==========================================================
Top commit counts by user:
'''

    def top_changed_lines_in_folders_header(self):
        return '''\
==========================================================
Top changed lines in folders:
'''

    def top_commit_counts_in_folders_header(self):
        return '''\
==========================================================
Top committed folders:
'''

    def top_changed_lines_in_files_header(self):
        return '''\
==========================================================
Top changed lines in files:
'''

    def top_commit_counts_in_files_header(self):
        return '''\
==========================================================
Top commit counts in files:
'''
