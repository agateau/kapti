#!/usr/bin/env python3
import sys

import apt


def main():
    cmd = sys.argv[1]
    name = sys.argv[2]

    cache = apt.Cache()
    pkg = cache[name]
    if cmd == 'install':
        pkg.mark_install()
    elif cmd == 'remove':
        pkg.mark_delete()
    else:
        return 1
    cache.commit()
    return 0


if __name__ == '__main__':
    sys.exit(main())
