#!/usr/bin/env python
import os
from subprocess import *

def searchPackages(searchTerms):
    out = Popen(["apt-cache", "search"] + searchTerms, stdout=PIPE).stdout
    lst = []
    for line in out.readlines():
        line = line.strip()
        lst.append(line.split(" - ", 1))
    lst.sort(cmp=lambda x,y: cmp(x[0], y[0]))
    return lst

def installCommand(name):
    return "apt-get install %s" % name

def removeCommand(name):
    return "apt-get remove %s" % name

def isPackagedInstalled(name):
    lstFile = "/var/lib/dpkg/info/%s.list" % name
    return os.path.exists(lstFile)

def getPackageInfo(name):
    out = Popen(["apt-cache", "show", name], stdout=PIPE).stdout
    info = {}
    lastKey = None
    for line in out.readlines():
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
