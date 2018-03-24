#      ______________________
# ___/  score manager class  \_______________________________________________

import pygame, sys, os, math

# new constants for the score's position
SCORE_XOFFSET = 50 # pixels from left edge
SCORE_YOFFSET = 0 # pixels from bottom edge (to top of score)

START_LIVES = 3

class Game():
    STATE_PLAYING = 1            # normal
    STATE_HIT_GHOST = 2          # hit ghost
    STATE_GAME_OVER = 3          # game over
    STATE_WAIT_START = 4         # wait to start
    STATE_WAIT_ATE_GHOST = 5     # wait after eating ghost
    STATE_WAIT_LEVEL_CLEAR = 6   # wait after eating all pellets
    STATE_FLASH_LEVEL = 7        # flash level when complete
    STATE_WAIT_LEVEL_SWITCH = 8  # wait after finishing level
    STATE_WAIT_HI_SCORE = 9      # wait after game over with new hi score

    def __init__(self, pacman):
        self._pacman = pacman

        self._levelNum = 0
        self.score = 0
        self.setLives(START_LIVES)

        self.hiScore = 100

        # game "state" variable
        self.state = self.STATE_GAME_OVER
        self.stateTimer = 0
        self.ghostTimer = 0
        self.ghostValue = 0
        self.fruitTimer = 0
        self.fruitScoreTimer = 0
        self.fruitScorePos = (0, 0)

        self.setState( self.STATE_GAME_OVER )

        self._dashboardList = None

        self._imLife = self._pacman.graphics.loadImage("text","life.gif")
        self._imGameOver = self._pacman.graphics.loadImage("text","gameover.gif")
        self._imHiScore = self._pacman.graphics.loadImage("text","hiscore.gif")
        self._imReady = self._pacman.graphics.loadImage("text","ready.gif")

        self._pacman.sounds.register("extralife", "extralife.wav")
        self._pacman.sounds.register("start", "start.wav")
        self._pacman.sounds.register("hiscore", "hiscore.wav")

    def startNewGame(self):
        self._levelNum = 1
        self.score = 0
        self.setLives(START_LIVES)

        self.setState( self.STATE_WAIT_START )
        self._pacman.level.loadLevel( self._levelNum )
        self._pacman.sounds.play("start")

        self._pacman.multiplayer.emitValue("score", self.score)
        self._pacman.multiplayer.emitValue("level", self._levelNum)

    def gameOver(self):
        if self.score > self.hiScore:
            self.hiScore = self.score
            self._pacman.multiplayer.emitValue("hi-score", self.hiScore)
            self.setState( Game.STATE_WAIT_HI_SCORE )
            self._pacman.sounds.play("hiscore")
        else:
            self.setState( Game.STATE_GAME_OVER )

    def setLives(self, lives):
        self.lives = lives

        if self.lives == 0:
            self.gameOver()
        else:
            self.setState( Game.STATE_WAIT_START )

        if self._pacman.multiplayer:
            self._pacman.multiplayer.emitValue("lives", self.lives)

        self._dashboardList = None

    def addToScore(self, amount):
        extraLifeSet = [500, 1000, 2000, 4000]

        for specialScore in extraLifeSet:
            if self.score < specialScore and self.score + amount >= specialScore:
                self._pacman.sounds.play("extralife")
                self.setLives(self.lives + 1)

        self.score += amount

        self._pacman.multiplayer.emitValue("score", self.score)

        self._dashboardList = None

    def drawScore(self):
        if not self._dashboardList:
            self._dashboardList = self._pacman.graphics.createList()
            self._dashboardList.begin()

            y = self._pacman.level.lvlHeight * self._pacman.TILE_HEIGHT + SCORE_YOFFSET
            self._pacman.graphics.drawNumber (self.score, (SCORE_XOFFSET, y), immediate = True )
            self._pacman.graphics.drawNumber (max(self.score, self.hiScore), (SCORE_XOFFSET + 360, y), immediate = True )

            for i in range(0, self.lives):
                self._pacman.graphics.draw (self._imLife, (SCORE_XOFFSET + 80 + i * 10 + 16, y), billboard = True, immediate = True)

            self._pacman.graphics.drawNumber (self._levelNum, (0, self._pacman.graphics.screenSize[1] - 20), immediate = True )

            self._dashboardList.end()

        self._pacman.graphics.drawMultiple([self._dashboardList])

        if self.state == self.STATE_GAME_OVER:
            self._pacman.graphics.draw (self._imGameOver, (self._pacman.TILE_WIDTH * (self._pacman.level.lvlWidth - 1) / 2, self._pacman.TILE_HEIGHT * self._pacman.level.lvlHeight / 2), billboard = True )
        if self.state == self.STATE_WAIT_HI_SCORE:
            self._pacman.graphics.draw (self._imHiScore, (self._pacman.TILE_WIDTH * (self._pacman.level.lvlWidth - 1) / 2, self._pacman.TILE_HEIGHT * self._pacman.level.lvlHeight / 2, 32 * math.sin(self.stateTimer / 10)), billboard = False )
        elif self.state == self.STATE_WAIT_START:
            self._pacman.graphics.draw (self._imReady, (self._pacman.TILE_WIDTH * (self._pacman.level.lvlWidth - 1) / 2, self._pacman.TILE_HEIGHT * self._pacman.level.lvlHeight / 2, 32 * math.sin(self.stateTimer / 5)), billboard = True )


    def getLevelNum(self):
        return self._levelNum

    def setNextLevel(self):
        self._levelNum += 1
        self._pacman.multiplayer.emitValue("level", self._levelNum)

        self.setState( self.STATE_WAIT_START )
        self._pacman.level.loadLevel( self._levelNum )

        self._pacman.player.stop()

        self._dashboardList = None

    def setState(self, newState):
        self.state = newState
        self.stateTimer = 0
        if self._pacman.multiplayer:
            self._pacman.multiplayer.emitValue("state", self.state)

        if self._pacman.piface:
            if self.state == self.STATE_PLAYING:
                self._pacman.piface.relays[0].turn_on()
            elif self.state == self.STATE_WAIT_HI_SCORE:
                self._pacman.piface.relays[0].turn_off()
                self._pacman.piface.relays[1].turn_on()
            elif self.state == self.STATE_GAME_OVER:
                self._pacman.piface.relays[0].turn_off()
                self._pacman.piface.relays[1].turn_off()

        # print " ***** GAME STATE IS NOW ***** " + str(newState)
