from collections import defaultdict
import xml.etree.ElementTree as ET
import fnmatch
import os
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
        return self.printer.get_full(self)


class HtmlPrinter(object):

    def __init__(self, blame_folder):
        self._blame_folder = blame_folder

    def get_full(self, statistics):
        html = ET.Element('html')
        head = ET.SubElement(html, 'head')
        style = ET.SubElement(head, 'style')
        style.text = '''\
table {
    border-collapse: collapse;
}

table, td, th {
    border: 1px solid black;
}'''
        body = ET.SubElement(html, 'body')
        body.append(self.top_changed_lines_by_user_header())
        body.append(self.write(statistics.get_changed_lines_by_users()))
        body.append(self.top_commit_counts_by_user_header())
        body.append(self.write(statistics.get_commit_counts_by_users()))
        body.append(self.top_changed_lines_in_folders_header())
        body.append(self.write_folders(statistics.get_changed_lines_by_folders()))
        body.append(self.top_commit_counts_in_folders_header())
        body.append(self.write_folders(statistics.get_commit_counts_by_folders()))
        body.append(self.top_changed_lines_in_files_header())
        body.append(self.write_links(statistics.get_changed_lines_by_files()))
        body.append(self.top_commit_counts_in_files_header())
        body.append(self.write_links(statistics.get_commit_counts_by_files()))
        return ET.tostring(html, method='html')

    def write(self, statistic, limit=None):
        table = ET.Element('table')
        for item in sorted(statistic.items(), key=lambda it: (-it[1], it[0]))[:limit]:
            row = ET.SubElement(table, 'tr')
            row.append(self._create_element('td', text=str(item[0])))
            row.append(self._create_element('td', text=str(item[1])))
        return table

    def write_links(self, statistic, limit=None):
        table = ET.Element('table')
        for item in sorted(statistic.items(), key=lambda it: (-it[1], it[0]))[:limit]:
            row = ET.SubElement(table, 'tr')
            file_element = ET.SubElement(row, 'td')
            file_element.append(self._create_element('a', text=item[0], href=item[0]))
            if self._blame_folder is not None:
                blame_file = os.path.join(self._blame_folder, path_functions.get_blame_name(item[0]))
                if os.path.exists(blame_file):
                    blame_element = ET.SubElement(row, 'td')
                    blame_element.append(self._create_element('a', text='blame', href=blame_file))
            row.append(self._create_element('td', text=str(item[1])))
        return table

    def write_folders(self, level_list):
        table = ET.Element('table')
        for i, folder_level in enumerate(level_list):
            row = ET.SubElement(table, 'tr')
            row.append(self._create_element('td', text='level'))
            row.append(self._create_element('td', text=str(i + 1)))
            subtable = ET.SubElement(row, 'td')
            subtable.append(self.write_links(folder_level, 7))
        return table

    def top_changed_lines_by_user_header(self):
        return self._create_element('h2', text='Top changed lines by user')

    def top_commit_counts_by_user_header(self):
        return self._create_element('h2', text='Top commit counts by user')

    def top_changed_lines_in_folders_header(self):
        return self._create_element('h2', text='Top changed lines in folders')

    def top_commit_counts_in_folders_header(self):
        return self._create_element('h2', text='Top commit counts in folders')

    def top_changed_lines_in_files_header(self):
        return self._create_element('h2', text='Top changed lines in files')

    def top_commit_counts_in_files_header(self):
        return self._create_element('h2', text='Top commit counts in files')

    def _create_element(self, tag, text='', **attribs):
        e = ET.Element(tag)
        if text:
            e.text = text
        for attrib in attribs:
            e.set(attrib, attribs[attrib])
        return e


class TextPrinter(object):

    def get_full(self, statistics):
        full = self.top_changed_lines_by_user_header()
        full += self.write(statistics.get_changed_lines_by_users())
        full += self.top_commit_counts_by_user_header()
        full += self.write(statistics.get_commit_counts_by_users())
        full += self.top_changed_lines_in_folders_header()
        full += self.write_folders(statistics.get_changed_lines_by_folders())
        full += self.top_commit_counts_in_folders_header()
        full += self.write_folders(statistics.get_commit_counts_by_folders())
        full += self.top_changed_lines_in_files_header()
        full += self.write(statistics.get_changed_lines_by_files())
        full += self.top_commit_counts_in_files_header()
        full += self.write(statistics.get_commit_counts_by_files())
        return full

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
