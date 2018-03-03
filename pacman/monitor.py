#!/usr/bin/python3

from zocp import ZOCP
import socket
import logging

class PacmanMonitorNode(ZOCP):
    # Constructor
    def __init__(self, nodename):
        super(PacmanMonitorNode, self).__init__(nodename)
        self.clients = {}
        self.hiScore = 15

    def run(self):
        self.register_int("hi-score", self.hiScore, 're')
        self.start()
        super(PacmanMonitorNode, self).run()

    def on_peer_enter(self, peer, name, *args, **kwargs):
        split_name = name.split("#",1)
        if(split_name[0] == 'pacman'):
            # Subscribe to any and all value changes
            self.clients[peer.hex] = {}
            self.signal_subscribe(self.uuid(), None, peer, None)

    def on_peer_exit(self, peer, name, *args, **kwargs):
        if peer.hex in self.clients:
            del(self.clients[peer.hex])

    def on_peer_modified(self, peer, name, data, *args, **kwargs):
        split_name = name.split("#",1)
        if(split_name[0] == 'pacman'):
            client = {}
            for key in data:
                if "value" in data[key]:
                    client[key] = data[key]["value"]
            if "hi-score" in client and client["hi-score"] > self.hiScore:
                self.hiScore = client["hi-score"]
                self.emit_signal("hi-score", self.hiScore)
            self.clients[peer.hex] = client

            print(self.clients)

    def on_peer_signaled(self, peer, name, data, *args, **kwargs):
        self.clients[peer.hex][data[0]] = data[1]
        if data[0] == "hi-score" and data[1] > self.hiScore:
            self.hiScore = data[1]
            self.emit_signal("hi-score", self.hiScore)

        print(self.clients)

if __name__ == '__main__':
    zl = logging.getLogger("zocp")
    #zl.setLevel(logging.DEBUG)

    z = PacmanMonitorNode("pacman#monitor@%s" % socket.gethostname())
    z.run()
    del z
    print("FINISH")

