from collections import namedtuple
from subprocess import check_output, call

Package = namedtuple("Package", ["name", "description", "isInstalled"])


def check_output_lines(cmd):
    return check_output(cmd).strip().split('\n')


class SortKeyCreator(object):
    def __init__(self, searchTerms):
        self.searchTerms = searchTerms

    def __call__(self, pkg):
        scores = [self._score(x, pkg.name) for x in self.searchTerms]
        score = reduce(lambda x, y: x * y, scores)
        return (score, pkg.name)

    def _score(self, searchTerm, name):
        # The lowest the better
        # 1 == exact match
        # 2 == matches start
        # 3 == matches end
        # 4 == name matches
        # 5 == description matches

        if searchTerm == name:
            return 1
        if name.startswith(searchTerm):
            return 2
        if name.endswith(searchTerm):
            return 3
        if searchTerm in name:
            return 4
        else:
            return 5


def searchPackages(searchTerms):
    lst = []
    for line in check_output_lines(["apt-cache", "search"] + searchTerms):
        line = unicode(line.strip(), "utf-8")
        name, description = line.split(" - ", 1)
        isInstalled = isPackageInstalled(name)
        lst.append(Package(name, description, isInstalled))
    lst.sort(key=SortKeyCreator(searchTerms))
    return lst

def install(name, cb):
    call(["qapt-batch", "--install", name])
    updateInstalledPackageList()
    cb()

def remove(name, cb):
    call(["qapt-batch", "--uninstall", name])
    updateInstalledPackageList()
    cb()

_installedPackages = None
def updateInstalledPackageList():
    global _installedPackages
    _installedPackages = []
    for line in check_output_lines(["dpkg", "--get-selections"]):
        line = line.strip()
        if not line.endswith("deinstall"):
            name = line.split("\t", 1)[0]
            # Strip architecture, if present
            colonIdx = name.find(":")
            if colonIdx != -1:
                name = name[:colonIdx]
            _installedPackages.append(name)

def isPackageInstalled(name):
    global _installedPackages
    if _installedPackages is None:
        updateInstalledPackageList()
    return name in _installedPackages

def getPackageInfo(name):
    info = {}
    lastKey = None
    for line in check_output_lines(["apt-cache", "show", name]):
        line = unicode(line, "utf-8")
        if line[0] == " ":
            line = line.strip()
            if line == ".":
                line = ""
            info[lastKey] = info[lastKey] + '\n' + line
        elif ":" in line:
            key, value = [x.strip() for x in line.split(":", 1)]
            info[key] = value
            lastKey = key
    return info

# vi: ts=4 sw=4 et
