#!/usr/bin/python3

import pygame
from pygame.locals import *

import os
import sys
import re
from collections import OrderedDict

from zocp import ZOCP
import socket

import logging

class PacmanMonitorNode(ZOCP):
    STATE_PLAYING = 1            # normal
    STATE_HIT_GHOST = 2          # hit ghost
    STATE_GAME_OVER = 3          # game over
    STATE_WAIT_START = 4         # wait to start
    STATE_WAIT_ATE_GHOST = 5     # wait after eating ghost
    STATE_WAIT_LEVEL_CLEAR = 6   # wait after eating all pellets
    STATE_FLASH_LEVEL = 7        # flash level when complete
    STATE_WAIT_LEVEL_SWITCH = 8  # wait after finishing level
    STATE_WAIT_HI_SCORE = 9      # wait after game over with new hi score
    STATE_WAIT_GAME_OVER = 10    # wait after game over without hi score

    STATE_COLORS = [
        (64, 64, 64),
        (0, 255, 0),      # STATE_PLAYING             # normal
        (255, 128, 0),    # STATE_HIT_GHOST           # hit ghost
        (0, 128, 255),    # STATE_GAME_OVER           # game over
        (0, 128, 0),      # STATE_WAIT_START          # wait to start
        (0, 128, 128),    # STATE_WAIT_ATE_GHOST      # wait after eating ghost
        (0, 255, 128),    # STATE_WAIT_LEVEL_CLEAR    # wait after eating all pellets
        (0, 255, 128),    # STATE_FLASH_LEVEL         # flash level when complete
        (0, 255, 128),    # STATE_WAIT_LEVEL_SWITCH   # wait after finishing level
        (255, 255, 0),    # STATE_WAIT_HI_SCORE       # wait after game over with new hi score
        (255, 64, 64)     # STATE_WAIT_GAME_OVER      # wait after game over without hi score
    ]


    # Constructor
    def __init__(self, nodename):
        super(PacmanMonitorNode, self).__init__(nodename)

        self.version = "0.0.0"
        with open(os.path.join(sys.path[0], "res", "version.txt")) as f:
            self.version = f.read()

        self.clients = OrderedDict()
        self.hiScore = 0
        self.hiScorePeer = None
        self.closing = False

        self.screenSize = (800,480)
        self.screen = None
        self.initDisplay()
        pygame.display.set_caption("Pacman monitor")

        pygame.font.init()
        self.default_font = pygame.font.Font(os.path.join(sys.path[0],"res", "fonts", "VeraMoBd.ttf"), 18)
        self.huge_font = pygame.font.Font(os.path.join(sys.path[0],"res", "fonts", "VeraMoBd.ttf"), 96)
        self.small_font = pygame.font.Font(os.path.join(sys.path[0],"res", "fonts", "VeraMoBd.ttf"), 16)

        pygame.mouse.set_visible(False)

        pygame.mixer.pre_init(22050, 16, 2, 512)
        pygame.mixer.init()
        self.hiScoreSound = pygame.mixer.Sound(os.path.join(sys.path[0], "res", "sounds", "monitor_hiscore.wav"))
        self.gameOverSound = pygame.mixer.Sound(os.path.join(sys.path[0], "res", "sounds", "gameover.wav"))

        self.address = ""

        self._dblclick = None

    def run(self):
        self.register_int("hi-score", self.hiScore, 're')
        self.start()
        self.address = self.endPointToAddress(self.endpoint())

        clock = pygame.time.Clock()

        while True:
            events = pygame.event.get()
            self.checkIfCloseButton( events )
            self.checkInputs()

            self.run_once(0)

            if self.closing:
                break
            self.draw()
            clock.tick (60)
        pygame.quit()
        self.stop()

    def exit(self):
        self.closing = True

    def initDisplay(self):
        (width, height) = self.screenSize
        flags = pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.RESIZABLE
        try:
            if os.uname().machine == "armv7l":
                flags |= pygame.FULLSCREEN
        except:
            pass
        self.screen = pygame.display.set_mode( (width, height), flags )

    def draw(self):
        # draw clients
        self.screen.fill((0,0,0))
        cellSize = (self.screenSize[0] / 4)
        for i in range(4):
            x = i * (self.screenSize[0] / 4)

            color = self.STATE_COLORS[0]
            if i < len(self.clients):
                state = -1
                client = self.clients[list(self.clients)[i]]
                if "state" in client:
                    color = self.STATE_COLORS[client["state"]]
                pygame.draw.rect(self.screen, color, (x,0, cellSize, cellSize))
                self.drawText((x + cellSize * 0.65, cellSize * 0.4), self.huge_font, (0,0,0), str(client.get("pi id", -1)) )
                self.drawText((x + 10, 10), self.default_font, (0,0,0),  "Score: " + str(client.get("score", 0)) )
                self.drawText((x + 10, 40), self.default_font, (0,0,0),  "Level: " + str(client.get("level", 0)) )
                self.drawText((x + 10, 70), self.default_font, (0,0,0),  "Lives: " + str(client.get("lives", 0)) )
                self.drawText((x + 10, cellSize * 0.9), self.small_font, (0,0,0),  client.get("version", "?"))
                self.drawText((x + cellSize * 0.4, cellSize * 0.9), self.small_font, (0,0,0),  client.get("address", "?"))
            else:
                pygame.draw.rect(self.screen, color, (x,0, cellSize, cellSize))

        # draw highscore
        color = self.STATE_COLORS[0]
        hiScoreClientId = -1
        if self.hiScorePeer != None:
            if self.hiScorePeer in self.clients:
                hiScoreClientId = self.clients[self.hiScorePeer].get("pi id", -1)
                if self.clients[self.hiScorePeer]["state"] == self.STATE_WAIT_HI_SCORE:
                    color = self.STATE_COLORS[self.STATE_WAIT_HI_SCORE]
                else:
                    color = self.STATE_COLORS[self.STATE_GAME_OVER]
        y = cellSize * 1.2
        pygame.draw.rect(self.screen, color, (0, y, self.screenSize[0], cellSize))
        self.drawText((30, y + cellSize * 0.25), self.huge_font, (0,0,0), str(self.hiScore) )
        self.drawText((self.screenSize[0] * 0.85, y + cellSize * 0.25), self.huge_font, (0,0,0), str(hiScoreClientId) if hiScoreClientId != -1 else "?" )

        self.drawText((10, cellSize * 2.1), self.small_font, (0,0,0),  self.version)
        self.drawText((cellSize * 0.4, cellSize * 2.1), self.small_font, (0,0,0),  self.address)

        pygame.display.update()

    def drawText(self, position, font, color, text):
        text_surface = font.render(text, True, color)
        self.screen.blit(text_surface, position)

    def checkIfCloseButton(self, events):
        for event in events:
            if event.type == QUIT:
                self.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if not self._dblclick:
                    self._dblclick = pygame.time.get_ticks()
                elif pygame.time.get_ticks() - self._dblclick < 1000:
                    self.exit()
                else:
                    self._dblclick = None

    def checkInputs(self):
        if pygame.key.get_pressed()[ pygame.K_ESCAPE ]:
            self.exit()

    def sortClients(self):
        self.clients = OrderedDict(sorted(self.clients.items(), key = lambda c: (c[1].get("id", sys.maxsize), c[0]) ))

    def endPointToAddress(self, endpoint):
        pattern = re.compile(".*\/\/(\d+\.\d+\.\d+\.\d+):(\d+)")
        result = pattern.match(endpoint)
        if result:
            return result.group(1)
        else:
            return "0.0.0.0"

    def on_peer_enter(self, peer, name, *args, **kwargs):
        split_name = name.split("#",1)
        if(split_name[0] == 'pacman'):
            # Subscribe to any and all value changes
            self.clients[peer.hex] = {"address": self.endPointToAddress(self.peer_address(peer))}
            self.signal_subscribe(self.uuid(), None, peer, None)

    def on_peer_exit(self, peer, name, *args, **kwargs):
        if peer.hex in self.clients:
            del(self.clients[peer.hex])
            self.sortClients()

    def on_peer_modified(self, peer, name, data, *args, **kwargs):
        split_name = name.split("#",1)
        if(split_name[0] == 'pacman'):
            if peer.hex in self.clients:
                client = self.clients[peer.hex]
            else:
                client = {}
            for key in data:
                if "value" in data[key]:
                    client[key] = data[key]["value"]
            if "hi-score" in client and client["hi-score"] > self.hiScore:
                # peer knows of a higher hiscore, but it may not be its own
                self.hiScore = client["hi-score"]
                self.emit_signal("hi-score", self.hiScore)
            self.clients[peer.hex] = client
            self.sortClients()

    def on_peer_signaled(self, peer, name, data, *args, **kwargs):
        if data[0] == "state":
            if data[1] == self.STATE_WAIT_HI_SCORE and self.clients[peer.hex].get("state", 0) != self.STATE_WAIT_HI_SCORE:
                # peer went into STATE_WAIT_HI_SCORE state
                self.hiScorePeer = peer.hex
                self.hiScoreSound.play()
            if data[1] == self.STATE_WAIT_GAME_OVER and self.clients[peer.hex].get("state", 0) != self.STATE_WAIT_GAME_OVER:
                self.gameOverSound.play()

        self.clients[peer.hex][data[0]] = data[1]
        if data[0] == "hi-score" and data[1] > self.hiScore:
            # peer knows of a higher hiscore, but it may not be its own
            self.hiScore = data[1]
            self.emit_signal("hi-score", self.hiScore)

if __name__ == '__main__':
    zl = logging.getLogger("zocp")
    #zl.setLevel(logging.DEBUG)

    z = PacmanMonitorNode("pacman#monitor@%s" % socket.gethostname())
    z.run()
    del z
    print("FINISH")

