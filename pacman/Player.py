#      _______________________
# ___/  player object class   \_______________________________________________

import pygame, random
from Game import Game
from Ghost import Ghost

class Player():

    def __init__(self, pacman):
        self._pacman = pacman
        self.x = 0
        self.y = 0
        self.velX = 0
        self.velY = 0
        self.speed = 3

        self.nearestRow = 0
        self.nearestCol = 0

        self.homeX = 0
        self.homeY = 0

        self._animFrame = 0
        self._anim_pacmanL = {}
        self._anim_pacmanR = {}
        self._anim_pacmanU = {}
        self._anim_pacmanD = {}
        self._anim_pacmanS = {}
        self._anim_pacmanCurrent = {}

        for i in range(1, 9, 1):
            self._anim_pacmanL[i] = self._pacman.graphics.loadImage("sprite", "pacman-l %d.gif" % i)
            self._anim_pacmanR[i] = self._pacman.graphics.loadImage("sprite", "pacman-r %d.gif" % i)
            self._anim_pacmanU[i] = self._pacman.graphics.loadImage("sprite", "pacman-u %d.gif" % i)
            self._anim_pacmanD[i] = self._pacman.graphics.loadImage("sprite", "pacman-d %d.gif" % i)
            self._anim_pacmanS[i] = self._pacman.graphics.loadImage("sprite", "pacman.gif")

        self.pelletSndNum = 0

        self._pacman.sounds.register("eatghost", "eatgh2.wav")
        self._pacman.sounds.register("eatfruit", "eatfruit.wav")
        self._pacman.sounds.register("death", "death.wav")

    def stop(self):
        self.velX = 0
        self.velY = 0

        self._anim_pacmanCurrent = self._anim_pacmanS
        self._animFrame = 3

    def move(self):
        self.nearestRow = int(((self.y + (self._pacman.TILE_WIDTH/2)) / self._pacman.TILE_WIDTH))
        self.nearestCol = int(((self.x + (self._pacman.TILE_HEIGHT/2)) / self._pacman.TILE_HEIGHT))

        # make sure the current velocity will not cause a collision before moving
        if not self._pacman.level.checkIfHitWall((self.x + self.velX, self.y + self.velY), (self.nearestRow, self.nearestCol)):
            # it's ok to Move
            self.x += self.velX
            self.y += self.velY

            # check for collisions with other tiles (pellets, etc)
            self._pacman.level.checkIfHitSomething((self.x, self.y), (self.nearestRow, self.nearestCol))

            # check for collisions with the ghosts
            for i in range(0, 4, 1):
                if self._pacman.level.checkIfHit( (self.x, self.y), (self._pacman.ghosts[i].x, self._pacman.ghosts[i].y), self._pacman.TILE_WIDTH/2):
                    # hit a ghost

                    if self._pacman.ghosts[i].state == Ghost.STATE_NORMAL:
                        # ghost is normal
                        self._pacman.game.setState( Game.STATE_HIT_GHOST )
                        self._pacman.sounds.play("death")

                    elif self._pacman.ghosts[i].state == Ghost.STATE_VULNERABLE:
                        self._pacman.game.addToScore(self._pacman.game.ghostValue)
                        self._pacman.game.ghostValue = self._pacman.game.ghostValue * 2
                        self._pacman.sounds.play("eatghost")

                        # ghost is vulnerable
                        # give them glasses
                        self._pacman.ghosts[i].state = Ghost.STATE_SPECTACLES
                        self._pacman.ghosts[i].runHome()

                        # set game state to brief pause after eating
                        self._pacman.game.setState( Game.STATE_WAIT_ATE_GHOST )

            # check for collisions with the fruit
            if self._pacman.fruit.active == True:
                if self._pacman.level.checkIfHit( (self.x, self.y), (self._pacman.fruit.x, self._pacman.fruit.y), self._pacman.TILE_WIDTH/2):
                    self._pacman.game.addToScore(2500)
                    self._pacman.fruit.active = False
                    self._pacman.game.fruitTimer = 0
                    self._pacman.game.fruitScoreTimer = 120
                    self._pacman.sounds.play("eatfruit")

        else:
            # we're going to hit a wall -- stop moving
            self.velX = 0
            self.velY = 0

        # deal with power-pellet ghost timer
        if self._pacman.game.ghostTimer > 0:
            self._pacman.game.ghostTimer -= 1

            if self._pacman.game.ghostTimer == 0:
                for i in range(0, 4, 1):
                    if self._pacman.ghosts[i].state == Ghost.STATE_VULNERABLE:
                        self._pacman.ghosts[i].state = Ghost.STATE_NORMAL
                self.ghostValue = 0

        # deal with fruit timer
        self._pacman.game.fruitTimer += 1
        if self._pacman.game.fruitTimer == 500:
            pathwayPair = self._pacman.level.getPathwayPairPos()

            if not pathwayPair == False:

                pathwayEntrance = pathwayPair[0]
                pathwayExit = pathwayPair[1]

                self._pacman.fruit.active = True

                self._pacman.fruit.nearestRow = pathwayEntrance[0]
                self._pacman.fruit.nearestCol = pathwayEntrance[1]

                self._pacman.fruit.x = self._pacman.fruit.nearestCol * self._pacman.TILE_WIDTH
                self._pacman.fruit.y = self._pacman.fruit.nearestRow * self._pacman.TILE_HEIGHT

                self._pacman.fruit.currentPath = self._pacman.path.findPath( (self._pacman.fruit.nearestRow, self._pacman.fruit.nearestCol), pathwayExit )
                self._pacman.fruit.followNextPathWay()

        if self._pacman.game.fruitScoreTimer > 0:
            self._pacman.game.fruitScoreTimer -= 1


    def draw(self):

        if self._pacman.game.state == Game.STATE_GAME_OVER:
            return False

        # set the current frame array to match the direction pacman is facing
        if self.velX > 0:
            self._anim_pacmanCurrent = self._anim_pacmanR
        elif self.velX < 0:
            self._anim_pacmanCurrent = self._anim_pacmanL
        elif self.velY > 0:
            self._anim_pacmanCurrent = self._anim_pacmanD
        elif self.velY < 0:
            self._anim_pacmanCurrent = self._anim_pacmanU

        self._pacman.graphics.blit (self._anim_pacmanCurrent[ self._animFrame ], (self.x - self._pacman.game.screenPixelPos[0], self.y - self._pacman.game.screenPixelPos[1]))

        if self._pacman.game.state == Game.STATE_PLAYING:
            if not self.velX == 0 or not self.velY == 0:
                # only Move mouth when pacman is moving
                self._animFrame += 1

            if self._animFrame == 9:
                # wrap to beginning
                self._animFrame = 1
