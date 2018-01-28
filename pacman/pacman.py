#! /usr/bin/python

# pacman.pyw
# By David Reilly

# Modified by Andy Sommerville, 8 October 2007:
# - Changed hard-coded DOS paths to os.path calls
# - Added constant SCRIPT_PATH (so you don't need to have pacman.pyw and res in your cwd, as long
# -   as those two are in the same directory)
# - Changed text-file reading to accomodate any known EOLn method (\n, \r, or \r\n)
# - I (happily) don't have a Windows box to test this. Blocks marked "WIN???"
# -   should be examined if this doesn't run in Windows
# - Added joystick support (configure by changing JS_* constants)
# - Added a high-score list. Depends on wx for querying the user's name

# Modified by Andy Sommerville, 11 October 2007:
# - Mom's eyes aren't what they used to be, so I'm switching 16x16 tiles to 24x24
#   Added constants self.TILE_WIDTH,self.TILE_HEIGHT to make this easier to change later.

# Modified by Aldo Hoeben, January 2016:
# - Python 3 compatibility
# - Refactor classes to separate files
# - Fix crash when finishing all levels

import pygame, sys, os, random
from pygame.locals import *

from PathFinder import PathFinder
from Graphics import Graphics
from Sounds import Sounds
from Game import Game
from Level import Level
from Player import Player
from Ghost import Ghost
from Fruit import Fruit

# NO_GIF_TILES -- tile numbers which do not correspond to a GIF file
# currently only "23" for the high-score list
NO_GIF_TILES = [23]

HS_XOFFSET = 48
HS_YOFFSET = 384

# Joystick defaults - maybe add a Preferences dialog in the future?
JS_DEVNUM = 0 # device 0 (pygame joysticks always start at 0). if JS_DEVNUM is not a valid device, will use 0
JS_XAXIS = 0 # axis 0 for left/right (default for most joysticks)
JS_YAXIS = 1 # axis 1 for up/down (default for most joysticks)
JS_STARTBUTTON = 9 # button number to start the game. this is a matter of personal preference, and will vary from device to device

# See getCrossRef() -- where these colors occur in a GIF, they are replaced according to the level file
IMG_EDGE_LIGHT_COLOR = (0xff,0xce,0xff,0xff)
IMG_FILL_COLOR = (0x84,0x00,0x84,0xff)
IMG_EDGE_SHADOW_COLOR = (0xff,0x00,0xff,0xff)
IMG_PELLET_COLOR = (0x80,0x00,0x80,0xff)

#      __________________
# ___/  main game class  \_____________________________________________________

class Pacman():
    TILE_WIDTH = TILE_HEIGHT = 24

    def __init__(self):
        # Must come before pygame.init()
        self.sounds = Sounds()

        self._clock = pygame.time.Clock()
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.OPENGL) # temporarily initialise display so bitmaps can be loaded
        pygame.display.set_caption("Pacman")

        self.graphics = Graphics(self)

        # create the pacman
        self.player = Player(self)

        # create a path_finder object
        self.path = PathFinder()

        # create ghost objects
        self.ghosts = {}
        for i in range(0, 6, 1):
            # remember, ghost[4] is the blue, vulnerable ghost
            self.ghosts[i] = Ghost(self, i)

        # create piece of fruit
        self.fruit = Fruit(self)

        self.tileID = {} # gives tile ID (when the name is known)
        self.tileIDImage = {} # gives tile image (when the ID# is known)

        # create game and level objects and load first level
        self.game = Game(self)
        self.level = Level(self)

        self.graphics.initDisplay()

        self.level.loadLevel( self.game.getLevelNum() )

        # initialise the joystick
        if pygame.joystick.get_count() > 0:
            if JS_DEVNUM < pygame.joystick.get_count():
                self._js = pygame.joystick.Joystick(JS_DEVNUM)
            else:
                self._js = pygame.joystick.Joystick(0)
            self._js.init()
        else: self._js = None

    def run(self):
        while True:

            events = pygame.event.get()
            self.checkIfCloseButton( events )
            self.checkResizeEvent( events )

            if self.game.state == Game.STATE_PLAYING:
                # normal gameplay state
                self.checkInputs()

                self.game.stateTimer += 1
                self.player.move()
                for i in range(0, 4, 1):
                    self.ghosts[i].move()
                self.fruit.move()

            elif self.game.state == Game.STATE_HIT_GHOST:
                # waiting after getting hit by a ghost
                self.game.stateTimer += 1

                if self.game.stateTimer == 90:
                    self.level.restart()

                    self.game.lives -= 1
                    if self.game.lives == -1:
                        self.game.updateHiScores(self.game.score)
                        self.game.setState( Game.STATE_GAME_OVER )
                        self.game.drawMidGameHiScores()
                    else:
                        self.game.setState( Game.STATE_WAIT_START )

            elif self.game.state == Game.STATE_GAME_OVER:
                # game over
                self.checkInputs()

            elif self.game.state == Game.STATE_WAIT_START:
                # waiting to start
                self.game.stateTimer += 1

                if self.game.stateTimer == 90:
                    self.game.setState( Game.STATE_PLAYING )
                    self.player.velX = self.player.speed

            elif self.game.state == Game.STATE_WAIT_ATE_GHOST:
                # brief pause after munching a vulnerable ghost
                self.game.stateTimer += 1

                if self.game.stateTimer == 30:
                    self.game.setState( Game.STATE_PLAYING )

            elif self.game.state == Game.STATE_WAIT_LEVEL_CLEAR:
                # pause after eating all the pellets
                self.game.stateTimer += 1

                if self.game.stateTimer == 60:
                    self.game.setState( Game.STATE_FLASH_LEVEL )
                    oldEdgeLightColor = self.level.edgeLightColor
                    oldEdgeShadowColor = self.level.edgeShadowColor
                    oldFillColor = self.level.fillColor

            elif self.game.state == Game.STATE_FLASH_LEVEL:
                # flashing maze after finishing level
                self.game.stateTimer += 1

                whiteSet = [10, 30, 50, 70]
                normalSet = [20, 40, 60, 80]

                if not whiteSet.count(self.game.stateTimer) == 0:
                    # member of white set
                    self.level.edgeLightColor = (255, 255, 255, 255)
                    self.level.edgeShadowColor = (255, 255, 255, 255)
                    self.level.fillColor = (0, 0, 0, 255)
                    self.getCrossRef()
                elif not normalSet.count(self.game.stateTimer) == 0:
                    # member of normal set
                    self.level.edgeLightColor = oldEdgeLightColor
                    self.level.edgeShadowColor = oldEdgeShadowColor
                    self.level.fillColor = oldFillColor
                    self.getCrossRef()
                elif self.game.stateTimer == 150:
                    self.game.setState( Game.STATE_WAIT_LEVEL_SWITCH )

            elif self.game.state == Game.STATE_WAIT_LEVEL_SWITCH:
                # blank screen before changing levels
                self.game.stateTimer += 1
                if self.game.stateTimer == 10:
                    self.game.setNextLevel()

            self.graphics.clear()

            if not self.game.state == Game.STATE_WAIT_LEVEL_SWITCH:
                self.graphics.drawBuffer()
                self.level.drawMap(drawPellets = True)

                if self.game.fruitScoreTimer > 0:
                    if self.game.stateTimer % 2 == 0:
                        self.game.drawNumber (2500, (self.fruit.x - 16, self.fruit.y + 4))

                for i in range(0, 4, 1):
                    self.ghosts[i].draw()
                self.fruit.draw()
                self.player.draw()

                #if self.game.state == Game.STATE_GAME_OVER:
                #    self.graphics.blit(self.game.imHiscores,(HS_XOFFSET,HS_YOFFSET))

            if self.game.state == Game.STATE_WAIT_ATE_GHOST:
                self.game.drawNumber (self.game.ghostValue / 2, (self.player.x - 4, self.player.y + 6))

            self.game.drawScore()

            pygame.display.flip()

            self._clock.tick (60)


    def checkIfCloseButton(self, events):
        for event in events:
            if event.type == QUIT:
                sys.exit(0)

    def checkResizeEvent(self, events):
        for event in events:
            if event.type == VIDEORESIZE:
                self.graphics.resizeDisplay(event.dict['size'])

    def checkInputs(self):
        if self.game.state == Game.STATE_PLAYING:
            if pygame.key.get_pressed()[ pygame.K_RIGHT ] or (self._js != None and self._js.get_axis(JS_XAXIS) > 0):
                if not self.level.checkIfHitWall((self.player.x + self.player.speed, self.player.y), (self.player.nearestRow, self.player.nearestCol)):
                    self.player.velX = self.player.speed
                    self.player.velY = 0

            elif pygame.key.get_pressed()[ pygame.K_LEFT ] or (self._js != None and self._js.get_axis(JS_XAXIS) < 0):
                if not self.level.checkIfHitWall((self.player.x - self.player.speed, self.player.y), (self.player.nearestRow, self.player.nearestCol)):
                    self.player.velX = -self.player.speed
                    self.player.velY = 0

            elif pygame.key.get_pressed()[ pygame.K_DOWN ] or (self._js != None and self._js.get_axis(JS_YAXIS) > 0):
                if not self.level.checkIfHitWall((self.player.x, self.player.y + self.player.speed), (self.player.nearestRow, self.player.nearestCol)):
                    self.player.velX = 0
                    self.player.velY = self.player.speed

            elif pygame.key.get_pressed()[ pygame.K_UP ] or (self._js != None and self._js.get_axis(JS_YAXIS) < 0):
                if not self.level.checkIfHitWall((self.player.x, self.player.y - self.player.speed), (self.player.nearestRow, self.player.nearestCol)):
                    self.player.velX = 0
                    self.player.velY = -self.player.speed

        if pygame.key.get_pressed()[ pygame.K_ESCAPE ]:
            sys.exit(0)

        elif self.game.state == Game.STATE_GAME_OVER:
            if pygame.key.get_pressed()[ pygame.K_RETURN ] or (self._js != None and self._js.get_button(JS_STARTBUTTON)):
                self.game.startNewGame()



    #      _____________________________________________
    # ___/  function: Get ID-Tilename Cross References  \______________________________________

    def getCrossRef(self):

        f = open(os.path.join(sys.path[0], "res", "crossref.txt"), 'r')

        lineNum = 0
        useLine = False

        for i in f.readlines():
            # print " ========= Line " + str(lineNum) + " ============ "
            while len(i)>0 and (i[-1]=='\n' or i[-1]=='\r'): i=i[:-1]
            while len(i)>0 and (i[0]=='\n' or i[0]=='\r'): i=i[1:]
            str_splitBySpace = i.split(' ')

            j = str_splitBySpace[0]

            if (j == "'" or j == "" or j == "#"):
                # comment / whitespace line
                # print " ignoring comment line.. "
                useLine = False
            else:
                # print str(wordNum) + ". " + j
                useLine = True

            if useLine == True:
                self.tileID[ str_splitBySpace[1] ] = int(str_splitBySpace[0])

                thisID = int(str_splitBySpace[0])
                if not thisID in NO_GIF_TILES:
                    self.tileIDImage[ thisID ] = self.graphics.loadImage("tiles",str_splitBySpace[1] + ".gif")
                else:
                    self.tileIDImage[ thisID ] = self.graphics.emptyImage()

                # change colors in tileIDImage to match maze colors
                for y in range(0, self.TILE_WIDTH, 1):
                    for x in range(0, self.TILE_HEIGHT, 1):

                        if self.tileIDImage[ thisID ].get_at( (x, y) ) == IMG_EDGE_LIGHT_COLOR:
                            # wall edge
                            self.tileIDImage[ thisID ].set_at( (x, y), self.level.edgeLightColor )

                        elif self.tileIDImage[ thisID ].get_at( (x, y) ) == IMG_FILL_COLOR:
                            # wall fill
                            self.tileIDImage[ thisID ].set_at( (x, y), self.level.fillColor )

                        elif self.tileIDImage[ thisID ].get_at( (x, y) ) == IMG_EDGE_SHADOW_COLOR:
                            # pellet color
                            self.tileIDImage[ thisID ].set_at( (x, y), self.level.edgeShadowColor )

                        elif self.tileIDImage[ thisID ].get_at( (x, y) ) == IMG_PELLET_COLOR:
                            # pellet color
                            self.tileIDImage[ thisID ].set_at( (x, y), self.level.pelletColor )

                # print str_splitBySpace[0] + " is married to " + str_splitBySpace[1]
            lineNum += 1

#      __________________
# ___/  main code block  \_____________________________________________________

if __name__ == '__main__':
    pacman = Pacman()
    pacman.run()