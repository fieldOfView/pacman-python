#      ______________________
# ___/  fruit object class   \_______________________________________________

import pygame
from Game import Game

TILE_WIDTH = TILE_HEIGHT=24

BOUNCE_TABLE = [0, 2, 4, 5, 5, 6, 6, 6, 6, 6, 5, 5, 4, 3, 2, 1]

class Fruit():

    def __init__(self, pacman):
        self._pacman = pacman
        self._slowTimer = 0

        # when fruit is not in use, it's in the (-1, -1) position off-screen.
        self.x = -TILE_WIDTH
        self.y = -TILE_HEIGHT
        self._velX = 0
        self._velY = 0
        self._speed = 2
        self.active = False

        self._bouncei = 0
        self._bounceY = 0

        self.nearestRow = (-1, -1)
        self.nearestCol = (-1, -1)

        self.imFruit = {}
        for i in range(0, 5, 1):
            self.imFruit[i] = self._pacman.graphics.loadImage("sprite", "fruit %d.gif" % i)

        self.currentPath = ""
        self.fruitType = 1

        self._pacman.sounds.register("fruitbounce", "fruitbounce.wav")

    def draw(self):
        if self._pacman.game.state == Game.STATE_GAME_OVER or self.active == False:
            return

        self._pacman.graphics.blit (self.imFruit[ self.fruitType ], (self.x - self._pacman.game.screenPixelPos[0], self.y - self._pacman.game.screenPixelPos[1] - self._bounceY))


    def move(self):

        if self.active == False:
            return False

        self._bouncei += 1
        if self._bouncei == 16:
            self._bouncei = 0
            self._pacman.sounds.play("fruitbounce")
        self._bounceY = BOUNCE_TABLE[self._bouncei]

        self._slowTimer += 1
        if self._slowTimer == 2:
            self._slowTimer = 0

            self.x += self._velX
            self.y += self._velY

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
                    self._pacman.game.fruitTimer = 0

    def followNextPathWay(self):

        # only follow this pathway if there is a possible path found!
        if not self.currentPath == False:

            if len(self.currentPath) > 0:
                if self.currentPath[0] == "L":
                    (self._velX, self._velY) = (-self._speed, 0)
                elif self.currentPath[0] == "R":
                    (self._velX, self._velY) = (self._speed, 0)
                elif self.currentPath[0] == "U":
                    (self._velX, self._velY) = (0, -self._speed)
                elif self.currentPath[0] == "D":
                    (self._velX, self._velY) = (0, self._speed)
