#      _______________________
# ___/  player object class   \_______________________________________________

import pygame, sys, os, random
from Game import Game
from Ghost import Ghost

# WIN???
SCRIPT_PATH = sys.path[0]

TILE_WIDTH = TILE_HEIGHT=24

class Player():

    def __init__(self, pacman):
        self.pacman = pacman
        self.x = 0
        self.y = 0
        self.velX = 0
        self.velY = 0
        self.speed = 3

        self.nearestRow = 0
        self.nearestCol = 0

        self.homeX = 0
        self.homeY = 0

        self.anim_pacmanL = {}
        self.anim_pacmanR = {}
        self.anim_pacmanU = {}
        self.anim_pacmanD = {}
        self.anim_pacmanS = {}
        self.anim_pacmanCurrent = {}

        for i in range(1, 9, 1):
            self.anim_pacmanL[i] = pygame.image.load(os.path.join(SCRIPT_PATH,"res","sprite","pacman-l " + str(i) + ".gif")).convert()
            self.anim_pacmanR[i] = pygame.image.load(os.path.join(SCRIPT_PATH,"res","sprite","pacman-r " + str(i) + ".gif")).convert()
            self.anim_pacmanU[i] = pygame.image.load(os.path.join(SCRIPT_PATH,"res","sprite","pacman-u " + str(i) + ".gif")).convert()
            self.anim_pacmanD[i] = pygame.image.load(os.path.join(SCRIPT_PATH,"res","sprite","pacman-d " + str(i) + ".gif")).convert()
            self.anim_pacmanS[i] = pygame.image.load(os.path.join(SCRIPT_PATH,"res","sprite","pacman.gif")).convert()

        self.pelletSndNum = 0

        self.snd_eatgh = pygame.mixer.Sound(os.path.join(SCRIPT_PATH,"res","sounds","eatgh2.wav"))
        self.snd_eatfruit = pygame.mixer.Sound(os.path.join(SCRIPT_PATH,"res","sounds","eatfruit.wav"))


    def move(self):
        self.nearestRow = int(((self.y + (TILE_WIDTH/2)) / TILE_WIDTH))
        self.nearestCol = int(((self.x + (TILE_HEIGHT/2)) / TILE_HEIGHT))

        # make sure the current velocity will not cause a collision before moving
        if not self.pacman.level.checkIfHitWall((self.x + self.velX, self.y + self.velY), (self.nearestRow, self.nearestCol)):
            # it's ok to Move
            self.x += self.velX
            self.y += self.velY

            # check for collisions with other tiles (pellets, etc)
            self.pacman.level.checkIfHitSomething((self.x, self.y), (self.nearestRow, self.nearestCol))

            # check for collisions with the ghosts
            for i in range(0, 4, 1):
                if self.pacman.level.checkIfHit( (self.x, self.y), (self.pacman.ghosts[i].x, self.pacman.ghosts[i].y), TILE_WIDTH/2):
                    # hit a ghost

                    if self.pacman.ghosts[i].state == Ghost.STATE_NORMAL:
                        # ghost is normal
                        self.pacman.game.setState( Game.STATE_HIT_GHOST )

                    elif self.pacman.ghosts[i].state == Ghost.STATE_VULNERABLE:
                        # ghost is vulnerable
                        # give them glasses
                        # make them run
                        self.pacman.game.addToScore(self.pacman.game.ghostValue)
                        self.pacman.game.ghostValue = self.pacman.game.ghostValue * 2
                        self.snd_eatgh.play()

                        self.pacman.ghosts[i].state = Ghost.STATE_SPECTACLES
                        self.pacman.ghosts[i].speed = self.pacman.ghosts[i].speed * 4
                        # and send them to the ghost box
                        self.pacman.ghosts[i].x = self.pacman.ghosts[i].nearestCol * TILE_WIDTH
                        self.pacman.ghosts[i].y = self.pacman.ghosts[i].nearestRow * TILE_HEIGHT
                        self.pacman.ghosts[i].currentPath = self.pacman.path.findPath( (self.pacman.ghosts[i].nearestRow, self.pacman.ghosts[i].nearestCol), (self.pacman.level.getGhostBoxPos()[0]+1, self.pacman.level.getGhostBoxPos()[1]) )
                        self.pacman.ghosts[i].followNextPathWay()

                        # set game state to brief pause after eating
                        self.pacman.game.setState( Game.STATE_WAIT_ATE_GHOST )

            # check for collisions with the fruit
            if self.pacman.fruit.active == True:
                if self.pacman.level.checkIfHit( (self.x, self.y), (self.pacman.fruit.x, self.pacman.fruit.y), TILE_WIDTH/2):
                    self.pacman.game.addToScore(2500)
                    self.pacman.fruit.active = False
                    self.pacman.game.fruitTimer = 0
                    self.pacman.game.fruitScoreTimer = 120
                    self.snd_eatfruit.play()

        else:
            # we're going to hit a wall -- stop moving
            self.velX = 0
            self.velY = 0

        # deal with power-pellet ghost timer
        if self.pacman.game.ghostTimer > 0:
            self.pacman.game.ghostTimer -= 1

            if self.pacman.game.ghostTimer == 0:
                for i in range(0, 4, 1):
                    if self.pacman.ghosts[i].state == Ghost.STATE_VULNERABLE:
                        self.pacman.ghosts[i].state = Ghost.STATE_NORMAL
                self.ghostValue = 0

        # deal with fruit timer
        self.pacman.game.fruitTimer += 1
        if self.pacman.game.fruitTimer == 500:
            pathwayPair = self.pacman.level.getPathwayPairPos()

            if not pathwayPair == False:

                pathwayEntrance = pathwayPair[0]
                pathwayExit = pathwayPair[1]

                self.pacman.fruit.active = True

                self.pacman.fruit.nearestRow = pathwayEntrance[0]
                self.pacman.fruit.nearestCol = pathwayEntrance[1]

                self.pacman.fruit.x = self.pacman.fruit.nearestCol * TILE_WIDTH
                self.pacman.fruit.y = self.pacman.fruit.nearestRow * TILE_HEIGHT

                self.pacman.fruit.currentPath = self.pacman.path.findPath( (self.pacman.fruit.nearestRow, self.pacman.fruit.nearestCol), pathwayExit )
                self.pacman.fruit.followNextPathWay()

        if self.pacman.game.fruitScoreTimer > 0:
            self.pacman.game.fruitScoreTimer -= 1


    def draw(self):

        if self.pacman.game.state == Game.STATE_GAME_OVER:
            return False

        # set the current frame array to match the direction pacman is facing
        if self.velX > 0:
            self.anim_pacmanCurrent = self.anim_pacmanR
        elif self.velX < 0:
            self.anim_pacmanCurrent = self.anim_pacmanL
        elif self.velY > 0:
            self.anim_pacmanCurrent = self.anim_pacmanD
        elif self.velY < 0:
            self.anim_pacmanCurrent = self.anim_pacmanU

        self.pacman.screen.blit (self.anim_pacmanCurrent[ self.animFrame ], (self.x - self.pacman.game.screenPixelPos[0], self.y - self.pacman.game.screenPixelPos[1]))

        if self.pacman.game.state == Game.STATE_PLAYING:
            if not self.velX == 0 or not self.velY == 0:
                # only Move mouth when pacman is moving
                self.animFrame += 1

            if self.animFrame == 9:
                # wrap to beginning
                self.animFrame = 1
