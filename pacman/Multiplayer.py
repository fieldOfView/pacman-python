#      ____________________________
# ___/  Multiplayer manager class  \_______________________________________________

from zocp import ZOCP

class Multiplayer(ZOCP):

    def __init__(self, pacman):
        self._pacman = pacman
        super().__init__("pacman#%s" % id(self))

        self._started = False

    def setup(self):
        self.register_int("version", self._pacman.version, 'r')
        self.register_int("pi id", self._pacman.piID + 1, 'r')
        self.register_int("state", 0, 're')
        self.register_int("score", 0, 're')
        self.register_int("level", 0, 're')
        self.register_int("lives", 0, 're')
        self.register_int("hi-score", self._pacman.game.hiScore, 're')

        self.start()

        self._started = True

    def update(self):
        if self._started:
            self.run_once(0)

    def emitValue(self, key, value):
        self.emit_signal(key, value)

    def on_peer_enter(self, peer, name, *args, **kwargs):
        split_name = name.split("#",1)
        if(split_name[0] == 'pacman'):
            # Subscribe to all hi-score updates
            self.signal_subscribe(self.uuid(), None, peer, "hi-score")

    def on_peer_signaled(self, peer, name, data, *args, **kwargs):
        if data[0] == "hi-score":
            self._updateHiScore(data[1])

    def on_peer_modified(self, peer, name, data, *args, **kwargs):
        split_name = name.split("#",1)
        if(split_name[0] == 'pacman') and "hi-score" in data and "value"  in data["hi-score"]:
            self._updateHiScore(data["hi-score"]["value"])

    def _updateHiScore(self, score):
        if score > self._pacman.game.hiScore:
            self._pacman.game.setHiScore(score)
            self.emitValue("hi-score", score)