import xml.etree.cElementTree as ET


class SvnFilter(object):

    def __init__(self, xml_log):
        tree = ET.parse(xml_log)
        self._root = tree.getroot()

    def get_logs_by_users(self, users):
        for logentry in self._root.findall('logentry'):
            if logentry.find('author').text not in users:
                self._root.remove(logentry)
        return self._root