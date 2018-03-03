#      ____________________________
# ___/  Multiplayer manager class  \_______________________________________________

from zocp import ZOCP
import logging

class Multiplayer(ZOCP):

    def __init__(self, pacman):
        self._pacman = pacman
        super().__init__("pacman-%s" % id(self))

        zl = logging.getLogger("zocp")
        zl.setLevel(logging.DEBUG)

        self._started = False

    def setup(self):
        self.register_int("pi id", self._pacman.piID, 're')
        self.register_int("state", 0, 're')
        self.register_int("current score", 0, 're')
        self.register_int("hi-score", 0, 'rwes')

        self.start()

        self._started = True

    def update(self):
        if self._started:
            self.run_once(0)

    def emitValue(self, key, value):
        self.emit_signal(key, value)

    def on_peer_enter(self, peer, name, *args, **kwargs):
        pass

    def on_modified(self, peer, name, data, *args, **kwargs):
        pass

