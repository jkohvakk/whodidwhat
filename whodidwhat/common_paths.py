import xml.etree.cElementTree as ET
import sys
import os
import argparse


def get_common_paths():
    params = parse_parameters()
    common_paths = set()
    et = ET.parse(params.input_xml)
    root = et.getroot()
    for logentry in root.findall('logentry'):
        paths = logentry.find('paths')
        for path in paths:
            common_paths.add(get_path_with_level(path.text, params.level))
    with open(params.output, 'w') as outfile:
        for path in sorted(common_paths):
            outfile.write(path + '\n')


def get_path_with_level(path, level):
    parts = [path]
    components = []
    while parts and parts[0] != os.path.sep:
        parts = os.path.split(parts[0])
        components.insert(0, parts[1])
    return os.path.join(*components[:level])


def parse_parameters(argv=None):
    argv = argv if argv is not None else sys.argv

    parser = argparse.ArgumentParser('Get common paths to certain level from svn -v --xml logs')
    parser.add_argument('--input-xml', help='path to svn xml log input', type=file)
    parser.add_argument('--output', help='path for writing paths')
    parser.add_argument('-l', '--level', help='Level to find commonness. Root is 1.', type=int)
    return parser.parse_args(argv[1:])
