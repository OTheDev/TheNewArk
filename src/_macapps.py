###############################################################################
#   Imports
###############################################################################
import platform
import time

from inspect import cleandoc
from subprocess import Popen, TimeoutExpired


###############################################################################
#   MacApps
###############################################################################
class MacApps:
    ACTIVATE = cleandoc("""
        tell application "%s" to activate
        """)
    OPEN = cleandoc("""
        tell application "%s" to open "%s"
        """)
    QUIT = cleandoc("""
        if application "%s" is running then
            tell application "%s" to quit
        end if
        """)

    def __init__(self, apps):
        if platform.system() != "Darwin":
            raise NotImplementedError("Supported OS/System(s): Darwin.")

        self.is_open = False
        self.apps = apps

        self._close()
        time.sleep(3)

    def open(self):
        if not self.is_open:
            self._open()
            self.is_open = True

    def close(self):
        if self.is_open:
            self._close()
            self.is_open = False

    def _open(self):
        for app in self.apps:
            if len(app) == 2:
                proc = Popen(["osascript", "-e",
                              self.__class__.OPEN % (app[0], app[1])])
            else:
                proc = Popen(["osascript", "-e",
                              self.__class__.ACTIVATE % app])

        try:
            outs, errs = proc.communicate(timeout=15)
        except TimeoutExpired:
            proc.kill()
            outs, errs = proc.communicate()

    def _close(self):
        for app in self.apps:
            if len(app) == 2:
                proc = Popen(['osascript', '-e',
                              self.__class__.QUIT % (app[0], app[0])])
            else:
                proc = Popen(['osascript', '-e',
                              self.__class__.QUIT % (app, app)])

        try:
            outs, errs = proc.communicate(timeout=15)
        except TimeoutExpired:
            proc.kill()
            outs, errs = proc.communicate()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


###############################################################################
#   Test
###############################################################################
if __name__ == '__main__':
    c = ["OBS"]
    try:
        with MacApps(c):
            print("Hello")
            time.sleep(10)
    except Exception as e:
        print(e)
