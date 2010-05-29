#!/usr/bin/env python
import os
from subprocess import *

def searchPackages(searchTerms):
    out = Popen(["apt-cache", "search"] + searchTerms, stdout=PIPE).stdout
    lst = []
    for line in out.readlines():
        line = unicode(line.strip(), "utf-8")
        lst.append(line.split(" - ", 1))
    lst.sort(cmp=lambda x,y: cmp(x[0], y[0]))
    return lst

def installCommand(name):
    return "apt-get install %s" % name

def removeCommand(name):
    return "apt-get remove %s" % name

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
    lstFile = "/var/lib/dpkg/info/%s.list" % name
    return os.path.exists(lstFile)

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
