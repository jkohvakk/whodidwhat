import os


def split_all(path):
    parts = []
    while True:
        path, last = os.path.split(path)
        parts.insert(0, last)
        if not path or path == os.path.sep:
            return parts


def get_all_folder_levels(path):
    folders = split_all(path)[:-1]
    folder_levels = []
    for i in range(1, len(folders) + 1):
        folder_levels.append(os.path.sep.join(folders[:i]))
    return folder_levels


def get_blame_name(server_name):
        blame_name = server_name.replace('://', '.')
        return blame_name.replace('/', '.')
