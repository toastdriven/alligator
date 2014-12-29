from __future__ import print_function

import os
import time

from alligator.constants import ALL


class Worker(object):
    def __init__(self, gator, max_tasks=0, to_consume=ALL, nap_time=0.1):
        self.gator = gator
        self.max_tasks = int(max_tasks)
        self.to_consume = to_consume
        self.nap_time = nap_time
        self.tasks_complete = 0

    def ident(self):
        return 'Alligator Worker (#{})'.format(os.getpid())

    def starting(self):
        ident = self.ident()
        print('{} starting & consuming "{}".'.format(ident, self.to_consume))

        if self.max_tasks:
            print('{} will die after {} tasks.'.format(ident, self.max_tasks))
        else:
            print('{} will never die.'.format(ident))

    def stopping(self):
        ident = self.ident()
        print('{} for "{}" shutting down. Consumed {} tasks.'.format(
            ident,
            self.to_consume,
            self.tasks_complete
        ))

    def result(self, result):
        print(result)

    def run_forever(self):
        self.starting()

        try:
            while True:
                if self.max_tasks and self.tasks_complete >= self.max_tasks:
                    self.stopping()
                    return 0

                result = self.gator.pop()
                self.tasks_complete += 1
                self.result(result)

                if self.nap_time:
                    time.sleep(self.nap_time)
        except KeyboardInterrupt:
            self.stopping()
            return 1
