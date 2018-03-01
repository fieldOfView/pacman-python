#      ______________________
# ___/  score manager class  \_______________________________________________

import pygame, sys, os

# WIN???
SCRIPT_PATH = sys.path[0]

# constants for the high-score display
HS_FONT_SIZE = 14
HS_LINE_HEIGHT = 16
HS_WIDTH = 408
HS_HEIGHT = 120
HS_ALPHA = 200

# new constants for the score's position
SCORE_XOFFSET = 50 # pixels from left edge
SCORE_YOFFSET = 0 # pixels from bottom edge (to top of score)
SCORE_COLWIDTH = 13 # width of each character

NO_WX = 0 # if set, the high-score code will not attempt to ask the user his name
USER_NAME = "User" # USER_NAME=os.getlogin() # the default user name if wx fails to load or NO_WX
                 # Oops! os.getlogin() only works if you launch from a terminal

class Game():
    STATE_PLAYING = 1            # normal
    STATE_HIT_GHOST = 2          # hit ghost
    STATE_GAME_OVER = 3          # game over
    STATE_WAIT_START = 4         # wait to start
    STATE_WAIT_ATE_GHOST = 5     # wait after eating ghost
    STATE_WAIT_LEVEL_CLEAR = 6   # wait after eating all pellets
    STATE_FLASH_LEVEL = 7        # flash level when complete
    STATE_WAIT_LEVEL_SWITCH = 8  # wait after finishing level

    def __init__(self, pacman):
        self._pacman = pacman

        self._levelNum = 0
        self.score = 0
        self.lives = 3

        # game "state" variable
        self.state = self.STATE_GAME_OVER
        self.stateTimer = 0
        self.ghostTimer = 0
        self.ghostValue = 0
        self.fruitTimer = 0
        self.fruitScoreTimer = 0
        self.fruitScorePos = (0, 0)

        self.setState( self.STATE_GAME_OVER )

        # numerical display digits
        self._digit = {}
        for i in range(0, 10, 1):
            self._digit[i] = self._pacman.graphics.loadImage("text",str(i) + ".gif")
        self._imLife = self._pacman.graphics.loadImage("text","life.gif")
        self._imGameOver = self._pacman.graphics.loadImage("text","gameover.gif")
        self._imReady = self._pacman.graphics.loadImage("text","ready.gif")

        self._pacman.sounds.register("extralife", "extralife.wav")
        self._pacman.sounds.register("start", "start.wav")

    def startNewGame(self):
        self._levelNum = 1
        self.score = 0
        self.lives = 3

        self.setState( self.STATE_WAIT_START )
        self._pacman.level.loadLevel( self._levelNum )
        self._pacman.sounds.play("start")

    def addToScore(self, amount):
        extraLifeSet = [500, 1000, 2000, 4000]

        for specialScore in extraLifeSet:
            if self.score < specialScore and self.score + amount >= specialScore:
                self._pacman.sounds.play("extralife")
                self.lives += 1

        self.score += amount


    def drawScore(self):
        y = self._pacman.level.lvlHeight * self._pacman.TILE_HEIGHT + SCORE_YOFFSET
        self.drawNumber (self.score, (SCORE_XOFFSET, y) )

        for i in range(0, self.lives, 1):
            self._pacman.graphics.draw (self._imLife, (SCORE_XOFFSET + 80 + i * 10 + 16, y) )

        if self.state == self.STATE_GAME_OVER:
            self._pacman.graphics.draw (self._imGameOver, (self._pacman.TILE_WIDTH * (self._pacman.level.lvlWidth - 1) / 2, self._pacman.TILE_HEIGHT * self._pacman.level.lvlHeight / 2), billboard = True )
        elif self.state == self.STATE_WAIT_START:
            self._pacman.graphics.draw (self._imReady, (self._pacman.TILE_WIDTH * (self._pacman.level.lvlWidth - 1) / 2, self._pacman.TILE_HEIGHT * self._pacman.level.lvlHeight / 2), billboard = True )

        self.drawNumber (self._levelNum, (0, self._pacman.graphics.screenSize[1] - 20) )

    def drawNumber(self, number, position):
        (x, y) = position
        strNumber = str(int(number))

        for i in range(0, len(strNumber), 1):
            iDigit = int(strNumber[i])
            self._pacman.graphics.draw (self._digit[ iDigit ], (x + i * SCORE_COLWIDTH, y) )


    def getLevelNum(self):
        return self._levelNum

    def setNextLevel(self):
        self._levelNum += 1

        self.setState( self.STATE_WAIT_START )
        self._pacman.level.loadLevel( self._levelNum )

        self._pacman.player.stop()

    def setState(self, newState):
        self.state = newState
        self.stateTimer = 0
        # print " ***** GAME STATE IS NOW ***** " + str(newState)
