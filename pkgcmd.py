#!/usr/bin/env python3
import json
import os
import socket
import sys

from argparse import ArgumentParser

import apt


_client = None


def json_dump(step, **kwargs):
    dct = dict(step=step)
    dct.update(kwargs)
    text = 'JSON ' + json.dumps(dct) + '\n'
    if _client:
        _client.send(text.encode())
    else:
        sys.stdout.write(text)
        sys.stdout.flush()


class JSONAcquireProgress(apt.progress.base.AcquireProgress):
    def done(self, item):
        super(JSONAcquireProgress, self).done(item=item)
        json_dump('acquire.done')

    def fail(self, item):
        super(JSONAcquireProgress, self).fail(item=item)
        json_dump('acquire.fail')

    def fetch(self, item):
        super(JSONAcquireProgress, self).fetch(item=item)
        json_dump('acquire.fetch', fetched_bytes=self.fetched_bytes, total_bytes=self.total_bytes)


class JSONInstallProgress(apt.progress.base.InstallProgress):
    def status_change(self, pkg, percent, status):
        super(JSONInstallProgress, self).status_change(pkg, percent, status)
        json_dump('install.progress', percent=percent)

    def finish_update(self):
        super(JSONInstallProgress, self).finish_update()
        json_dump('install.finish_update')

    def fork(self):
        pid = os.fork()
        if pid == 0:
            out_fd = sys.stdout.fileno()
            null = open(os.devnull, 'wb')
            os.dup2(null.fileno(), out_fd)
        return pid


def main():
    global _client

    parser = ArgumentParser(description='Kapti root helper')
    parser.add_argument('--socket', help='Where to write progress information')
    parser.add_argument('action', help='Either install or remove')
    parser.add_argument('package', help='Name of the package')
    args = parser.parse_args()

    if args.socket:
        _client = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        _client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        _client.connect(args.socket)

    try:
        json_dump('starting')
        cache = apt.Cache()
        pkg = cache[args.package]
        if args.action == 'install':
            pkg.mark_install()
        elif args.action == 'remove':
            pkg.mark_delete()
        else:
            return 1
        pkg.commit(fprogress=JSONAcquireProgress(), iprogress=JSONInstallProgress())
        return 0
    finally:
        if _client:
            _client.close()


if __name__ == '__main__':
    sys.exit(main())
