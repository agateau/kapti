import io
import json
import os
import socket
from collections import namedtuple
from functools import reduce
from subprocess import check_output, Popen
from tempfile import NamedTemporaryFile

import apt

from PyQt4.QtCore import QObject, pyqtSignal, QTimer

Package = namedtuple("Package", ["name", "description", "isInstalled"])


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
        name, description = line.split(" - ", 1)
        isInstalled = isPackageInstalled(name)
        lst.append(Package(name, description, isInstalled))
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

        pkgdir = os.path.dirname(__file__)
        pkgcmd = os.path.join(pkgdir, 'pkgcmd.py')
        command = [pkgcmd, '--socket', self._socketPath] + args

        self._proc = Popen(['kdesudo', '-c', ' '.join(command)])

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


def _formatBaseDependency(dependency):
    if dependency.relation:
        return dependency.name + ' ' + dependency.relation + ' ' + dependency.version
    else:
        return dependency.name


def _formatDependencyList(dependencyList):
    lst = []
    for dependency in dependencyList:
        name = ' | '.join([_formatBaseDependency(x) for x in dependency])
        lst.append(name)
    return ', '.join(lst)


def getPackageInfo(name):
    pkg = _getCache()[name]
    version = pkg.versions[0]
    info = dict(
        Section=pkg.section,
        Homepage=version.homepage,
        Recommends=_formatDependencyList(version.recommends),
        Summary=version.summary,
        Description=version.description,
        Suggests=_formatDependencyList(version.suggests),
        Depends=_formatDependencyList(version.dependencies),
        Version=version.version,
    )
    return info

# vi: ts=4 sw=4 et
