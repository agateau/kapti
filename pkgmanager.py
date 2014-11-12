#!/usr/bin/env python
from subprocess import *

from collections import namedtuple

Package = namedtuple("Package", ["name", "description", "isInstalled"])


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
    out = Popen(["apt-cache", "search"] + searchTerms, stdout=PIPE).stdout
    lst = []
    for line in out.readlines():
        line = unicode(line.strip(), "utf-8")
        name, description = line.split(" - ", 1)
        isInstalled = isPackageInstalled(name)
        lst.append(Package(name, description, isInstalled))
    lst.sort(key=SortKeyCreator(searchTerms))
    return lst

def installCommand(name):
    return ["qapt-batch", "--install", name]

def removeCommand(name):
    return ["qapt-batch", "--uninstall", name]

_installedPackages = None
def updateInstalledPackageList():
    global _installedPackages
    out = Popen(["dpkg", "--get-selections"], stdout=PIPE).stdout
    _installedPackages = []
    for line in out.readlines():
        line = line.strip()
        if not line.endswith("deinstall"):
            name = line.split("\t", 1)[0]
            _installedPackages.append(name)

def isPackageInstalled(name):
    global _installedPackages
    if _installedPackages is None:
        updateInstalledPackageList()
    return name in _installedPackages

def getPackageInfo(name):
    out = Popen(["apt-cache", "show", name], stdout=PIPE).stdout
    info = {}
    lastKey = None
    for line in out.readlines():
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
