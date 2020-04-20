import io
import json
import os
import socket
import sys

from functools import reduce
from subprocess import check_output, Popen
from tempfile import NamedTemporaryFile

import apt

from PyQt5.QtCore import QObject, pyqtSignal, QTimer


class RelatedPackage:
    def __init__(self, name, relation=None, version=None):
        self.name = name
        self.relation = relation
        self.version = version
        self._installed = None

    @property
    def isInstalled(self):
        if self._installed is None:
            self._installed = isPackageInstalled(self.name)
        return self._installed


class Package:
    def __init__(self, name, summary=None, isInstalled=None):
        self.name = name
        self.summary = summary
        self.isInstalled = isInstalled
        self.version = None
        self.section = None
        self.description = None
        self.homepage = None
        self.depends = []
        self.recommends = []
        self.suggests = []

    @property
    def thumbnailUrl(self):
        return f"http://screenshots.debian.net/thumbnail/{self.name}"

    @property
    def screenshotUrl(self):
        return f"http://screenshots.debian.net/screenshot/{self.name}"

_cache = None


def check_output_lines(cmd):
    out = check_output(cmd).decode().strip()
    if out == '':
        return []
    return out.split('\n')


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
        line = line.strip()
        name, summary = line.split(" - ", 1)
        isInstalled = isPackageInstalled(name)
        lst.append(Package(name, summary=summary, isInstalled=isInstalled))
    lst.sort(key=SortKeyCreator(searchTerms))
    return lst


class PkgcmdRunner(QObject):
    done = pyqtSignal(bool)
    progress = pyqtSignal(dict)

    def __init__(self, args):
        super(PkgcmdRunner, self).__init__()
        self._buffer = ''

        self._socketPath = NamedTemporaryFile(prefix='kapti-', delete=False).name
        self._server = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self._server.setblocking(False)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        os.unlink(self._socketPath)
        self._server.bind(self._socketPath)

        # TODO: use setuptools API to find the path to pkgcmd
        pkgdir = os.path.dirname(sys.argv[0])
        pkgcmd = os.path.join(pkgdir, 'pkgcmd')
        assert os.path.exists(pkgcmd)
        command = [pkgcmd, '--socket', self._socketPath] + args

        self._proc = Popen(['kdesu', '-c', ' '.join(command)])

        self._scheduleUpdate()

    def _update(self):
        self._proc.poll()
        if self._proc.returncode is not None:
            _getCache().open()
            self._server.close()
            os.unlink(self._socketPath)
            self.done.emit(self._proc.returncode == 0)
            self.deleteLater()
            return

        self._scheduleUpdate()

        try:
            chunk = self._server.recv(80)
        except io.BlockingIOError:
            return
        data = self._buffer + chunk.decode()
        lines = data.split('\n')
        self._buffer = lines.pop()
        for line in lines:
            if line.startswith('JSON '):
                dct = json.loads(line[5:])
                self.progress.emit(dct)

    def _scheduleUpdate(self):
        QTimer.singleShot(0, self._update)


def install(name):
    return PkgcmdRunner(['install', name])


def remove(name):
    return PkgcmdRunner(['remove', name])


def _getCache():
    global _cache
    if _cache is None:
        _cache = apt.Cache()
    return _cache


def isPackageInstalled(name):
    cache = _getCache()
    return name in cache and cache[name].is_installed


def _createRelatedPackages(dependencies):
    """Creates a list of RelatedPackage from apt dependencies"""
    return [RelatedPackage(x.name, x.relation, x.version) for x in dependencies]


def getPackage(name):
    aptpkg = _getCache()[name]
    version = aptpkg.versions[0]
    pkg = Package(name, summary=version.summary, isInstalled=aptpkg.is_installed)
    pkg.version = version.version
    pkg.section = aptpkg.section
    pkg.homepage = version.homepage
    pkg.description = version.description
    pkg.depends = [_createRelatedPackages(x) for x in version.dependencies]
    pkg.recommends = [_createRelatedPackages(x) for x in version.recommends]
    pkg.suggests = [_createRelatedPackages(x) for x in version.suggests]
    return pkg

# vi: ts=4 sw=4 et
