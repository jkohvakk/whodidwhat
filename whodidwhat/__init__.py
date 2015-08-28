from svnfilter import SvnFilter
import common_paths


def whodidwhat():
    svnfilter = SvnFilter()
    svnfilter.parse_parameters_and_filter()


def get_common_paths():
    common_paths.get_common_paths()
