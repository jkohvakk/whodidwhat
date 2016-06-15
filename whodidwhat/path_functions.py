MAX_LINUX_FILENAME_LEN = 255


def split_all(path):
    return path.split('/')


def get_all_folder_levels(path):
    folders = split_all(path)[:-1]
    folder_levels = []
    for i in range(1, len(folders) + 1):
        folder_levels.append('/'.join(folders[:i]))
    return folder_levels


def get_blame_name(server_name):
    blame_name = server_name.replace('://', '.')
    blame_name = blame_name.replace('/', '.')
    return blame_name[-MAX_LINUX_FILENAME_LEN:]
