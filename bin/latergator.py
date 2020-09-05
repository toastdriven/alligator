#!/usr/bin/env python
import sys

from alligator import Gator, Worker


def main(dsn):
    gator = Gator(dsn)

    worker = Worker(gator)
    worker.run_forever()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python latergator.py <DSN>")
        sys.exit(1)

    dsn = sys.argv[1]
    main(dsn)
