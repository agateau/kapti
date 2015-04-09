#!/usr/bin/env python3
import sys

from argparse import ArgumentParser

import apt


def main():
    parser = ArgumentParser(description='Kapti root helper')
    parser.add_argument('action', help='Either install or remove')
    parser.add_argument('package', help='Name of the package')
    args = parser.parse_args()

    cache = apt.Cache()
    pkg = cache[args.package]
    if args.action == 'install':
        pkg.mark_install()
    elif args.action == 'remove':
        pkg.mark_delete()
    else:
        return 1
    cache.commit()
    return 0


if __name__ == '__main__':
    sys.exit(main())
