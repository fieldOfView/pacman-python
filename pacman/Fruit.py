#      ______________________
# ___/  fruit object class   \_______________________________________________

import pygame, sys, os
from Game import Game

# WIN???
SCRIPT_PATH = sys.path[0]

TILE_WIDTH = TILE_HEIGHT=24

BOUNCE_TABLE = [0, 2, 4, 5, 5, 6, 6, 6, 6, 6, 5, 5, 4, 3, 2, 1]

class Fruit():

    def __init__(self, pacman):
        self.pacman = pacman
        # when fruit is not in use, it's in the (-1, -1) position off-screen.
        self.slowTimer = 0
        self.x = -TILE_WIDTH
        self.y = -TILE_HEIGHT
        self.velX = 0
        self.velY = 0
        self.speed = 2
        self.active = False

        self.bouncei = 0
        self.bounceY = 0

        self.nearestRow = (-1, -1)
        self.nearestCol = (-1, -1)

        self.imFruit = {}
        for i in range(0, 5, 1):
            self.imFruit[i] = pygame.image.load(os.path.join(SCRIPT_PATH,"res","sprite","fruit " + str(i) + ".gif")).convert()

        self.currentPath = ""
        self.fruitType = 1

        self.snd_fruitbounce = pygame.mixer.Sound(os.path.join(SCRIPT_PATH,"res","sounds","fruitbounce.wav"))


    def draw(self):
        if self.pacman.game.state == Game.STATE_GAME_OVER or self.active == False:
            return

        self.pacman.screen.blit (self.imFruit[ self.fruitType ], (self.x - self.pacman.game.screenPixelPos[0], self.y - self.pacman.game.screenPixelPos[1] - self.bounceY))


    def move(self):

        if self.active == False:
            return False

        self.bouncei += 1
        if self.bouncei == 16:
            self.bouncei = 0
            self.snd_fruitbounce.play()
        self.bounceY = BOUNCE_TABLE[self.bouncei]

        self.slowTimer += 1
        if self.slowTimer == 2:
            self.slowTimer = 0

            self.x += self.velX
            self.y += self.velY

            self.nearestRow = int(((self.y + (TILE_WIDTH/2)) / TILE_WIDTH))
            self.nearestCol = int(((self.x + (TILE_HEIGHT/2)) / TILE_HEIGHT))

            if (self.x % TILE_WIDTH) == 0 and (self.y % TILE_HEIGHT) == 0:
                # if the fruit is lined up with the grid again
                # meaning, it's time to go to the next path item

                if len(self.currentPath) > 0:
                    self.currentPath = self.currentPath[1:]
                    self.followNextPathWay()

                else:
                    self.x = self.nearestCol * TILE_WIDTH
                    self.y = self.nearestRow * TILE_HEIGHT

                    self.active = False
                    self.pacman.game.fruitTimer = 0

    def followNextPathWay(self):

        # only follow this pathway if there is a possible path found!
        if not self.currentPath == False:

            if len(self.currentPath) > 0:
                if self.currentPath[0] == "L":
                    (self.velX, self.velY) = (-self.speed, 0)
                elif self.currentPath[0] == "R":
                    (self.velX, self.velY) = (self.speed, 0)
                elif self.currentPath[0] == "U":
                    (self.velX, self.velY) = (0, -self.speed)
                elif self.currentPath[0] == "D":
                    (self.velX, self.velY) = (0, self.speed)
