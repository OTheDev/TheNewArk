###############################################################################
#   Imports
###############################################################################
from time import perf_counter


###############################################################################
#   Scheduler Class
###############################################################################
class Scheduler:
    """
    Simple utility to schedule jobs periodically.

    Appropriate for synchronous code where high precision is not needed.
    """
    timer = perf_counter

    def __init__(self, *, every, callbacks, args, debug=False):
        self.every = every
        self.callbacks = callbacks
        self.args = args
        self.debug = debug

        ctime = self.timer()

        if self.debug:
            self.start_time = ctime

        self.next_events = [x if callable(x) else ctime + x for x in
                            self.every]

    def check(self):
        time = self.__class__.timer()
        for idx, event_time in enumerate(self.next_events):
            if callable(self.every[idx]):
                if self.every[idx]():

                    if self.debug:
                        self.print_debug()

                    self.callbacks[idx](*self.args[idx])
            else:
                if time >= event_time:

                    if self.debug:
                        self.print_debug()

                    self.callbacks[idx](*self.args[idx])
                    self.next_events[idx] = time + self.every[idx]

    def print_debug(self):
        print(f"Elapsed: {self.timer() - self.start_time}")


###############################################################################
#   Test
#
#   Status: successful.
###############################################################################
def foo(name):
    print(f"\t{name}")


def bar():
    print("\tBar")


class Test_1:
    timer = perf_counter
    last_update = timer()

    def __init__(self):
        pass

    @classmethod
    def is_time(cls, seconds) -> bool:
        return cls.timer() - cls.last_update >= seconds

    @classmethod
    def callback(cls, message):
        print(f"\t{message}")
        cls.last_update = cls.timer()


class Test_2:
    timer = perf_counter

    def __init__(self):
        self.last_update = self.timer()

    def is_time(self, seconds) -> bool:
        return self.timer() - self.last_update >= seconds

    def callback(self, message):
        print(f"\t{message}")
        self.last_update = self.timer()


if __name__ == '__main__':
    from functools import partial
    t1 = Test_1()
    t2 = Test_2()
    scheduler = Scheduler(every=[5, 10, partial(t1.is_time, 15),
                                 partial(t2.is_time, 20)],
                          callbacks=[foo, bar, t1.callback,
                                     t2.callback],
                          args=[["Foo"], [], ["Cool"], ["Phew"]],
                          debug=True)

    while True:
        scheduler.check()
