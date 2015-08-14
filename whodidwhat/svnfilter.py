import xml.etree.cElementTree as ET


class SvnFilter(object):

    def __init__(self):
        pass

    def get_logs_by_users(self, xml_log, users):
        tree = ET.parse(xml_log)
        root = tree.getroot()
        for logentry in root.findall('logentry'):
            if logentry.find('author').text not in users:
                root.remove(logentry)
        return root

    def read_userlist(self, userlist_file):
        userlist = []
        for line in userlist_file:
            if line.strip() and not line.strip().startswith('#'):
                userlist.append(line.strip())
        return sorted(userlist)