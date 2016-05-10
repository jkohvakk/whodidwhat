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
        for item in sorted(statistic.items(), key=lambda it: (-it[1], it[0])):
            text += '{}: {}\n'.format(item[0], item[1])
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

    def get_changed_lines_by_folders_text(self):
        total_text = ''
        for i, folder_level in enumerate(self.get_changed_lines_by_folders()):
            total_text += '---------------- level {} ---------------------------------\n'.format(i + 1)
            total_text += self._to_text(folder_level)
        return total_text

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

    def get_commit_counts_by_folders_text(self):
        total_text = ''
        for i, folder_level in enumerate(self.get_commit_counts_by_folders()):
            total_text += '---------------- level {} ---------------------------------\n'.format(i + 1)
            total_text += self._to_text(folder_level)
        return total_text

    def get_commit_counts_by_folders(self):
        return self._get_changes_by_folders(self._commit_counts_by_file)

    def get_full_text(self):
        statistics_txt = '==========================================================\n'
        statistics_txt += 'Top changed lines by user:\n'
        statistics_txt += self.get_changed_lines_by_users_text()
        statistics_txt += '==========================================================\n'
        statistics_txt += 'Top commit counts by user:\n'
        statistics_txt += self.get_commit_counts_by_users_text()
        statistics_txt += '==========================================================\n'
        statistics_txt += 'Top changed lines in folders:\n'
        statistics_txt += self.get_changed_lines_by_folders_text()
        statistics_txt += '==========================================================\n'
        statistics_txt += 'Top committed folders:\n'
        statistics_txt += self.get_commit_counts_by_folders_text()
        statistics_txt += '==========================================================\n'
        statistics_txt += 'Top changed lines in files:\n'
        statistics_txt += self.get_changed_lines_by_files_text()
        statistics_txt += '==========================================================\n'
        statistics_txt += 'Top commit counts in files:\n'
        statistics_txt += self.get_commit_counts_by_files_text()
        return statistics_txt