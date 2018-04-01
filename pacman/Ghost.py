#      _____________________
# ___/  ghost object class  \_______________________________________________

import random
from Game import Game

GHOST_COLORS = [
    (255, 50, 50, 255),
    (255, 128, 255, 255),
    (128, 255, 255, 255),
    (255, 128, 0, 255),
    (200, 200, 200, 255), # blue, vulnerable ghost
    (140, 140, 140, 255)  # white, flashing ghost
]

MAX_FRAME = 7

class Ghost():
    STATE_NORMAL = 1
    STATE_VULNERABLE = 2
    STATE_SPECTACLES = 3

    def __init__(self, pacman, ghostID):
        self._pacman = pacman
        self.x = 0
        self.y = 0
        self._velX = 0
        self._velY = 0
        self._speed = 2

        self.nearestRow = 0
        self.nearestCol = 0

        self._id = ghostID

        # ghost "state" variable
        self.state = self.STATE_NORMAL

        self.homeX = 0
        self.homeY = 0

        self.currentPath = ""

        self.anim = {}
        for i in range(1, MAX_FRAME, 1):
            self.anim[i] = self._pacman.graphics.loadImage("sprite", "ghost %d.gif" % i)

            # change the ghost color in this frame
            for y in range(0, self._pacman.TILE_HEIGHT, 1):
                for x in range(0, self._pacman.TILE_WIDTH, 1):

                    if self.anim[i].get_at( (x, y) ) == (255, 0, 0, 255):
                        # default, red ghost body color
                        self.anim[i].set_at( (x, y), GHOST_COLORS[ self._id ] )
            self.anim[i].updateTexture()

        self._animFrame = 1
        self._animDelay = 0

    def draw(self):
        if self._pacman.game.state == Game.STATE_GAME_OVER:
            return

        if self.state == self.STATE_NORMAL:
            # draw regular ghost (this one)
            self._pacman.graphics.draw (self.anim[ self._animFrame ], (self.x, self.y), billboard = True)
        elif self.state == self.STATE_VULNERABLE:
            # draw vulnerable ghost

            if self._pacman.game.ghostTimer > 100:
                # blue
                self._pacman.graphics.draw (self._pacman.ghosts[4].anim[ self._animFrame ], (self.x, self.y), billboard = True)
            else:
                # blue/white flashing
                tempTimerI = int(self._pacman.game.ghostTimer / 10)
                if tempTimerI % 2:
                    self._pacman.graphics.draw (self._pacman.ghosts[5].anim[ self._animFrame ], (self.x, self.y), billboard = True)
                else:
                    self._pacman.graphics.draw (self._pacman.ghosts[4].anim[ self._animFrame ], (self.x, self.y), billboard = True)

        elif self.state == self.STATE_SPECTACLES:
            # draw glasses
            self._pacman.graphics.draw (self._pacman.tileIDImage[ self._pacman.tileID[ 'glasses' ] ], (self.x, self.y), billboard = True)

        if self._pacman.game.state >= Game.STATE_WAIT_LEVEL_CLEAR:
            # don't animate ghost if the level is complete
            return

        self._animDelay += 1

        if self._animDelay == 2:
            self._animFrame += 1

            if self._animFrame == MAX_FRAME:
                # wrap to beginning
                self._animFrame = 1

            self._animDelay = 0

    def move(self):
        self.x += self._velX
        self.y += self._velY

        self.nearestRow = int(((self.y + (self._pacman.TILE_HEIGHT/2)) / self._pacman.TILE_HEIGHT))
        self.nearestCol = int(((self.x + (self._pacman.TILE_HEIGHT/2)) / self._pacman.TILE_WIDTH))

        if (self.x % self._pacman.TILE_WIDTH) == 0 and (self.y % self._pacman.TILE_HEIGHT) == 0:
            # if the ghost is lined up with the grid again
            # meaning, it's time to go to the next path item

            if len(self.currentPath) > 0:
                self.currentPath = self.currentPath[1:]
                self.followNextPathWay()

            else:
                self.x = self.nearestCol * self._pacman.TILE_WIDTH
                self.y = self.nearestRow * self._pacman.TILE_HEIGHT

                # chase pac-man
                self.currentPath = self._pacman.path.findPath( (self.nearestRow, self.nearestCol), (self._pacman.player.nearestRow, self._pacman.player.nearestCol) )
                self.followNextPathWay()

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

            else:
                # this ghost has reached his destination!!

                if not self.state == self.STATE_SPECTACLES:
                    # chase pac-man
                    self.currentPath = self._pacman.path.findPath( (self.nearestRow, self.nearestCol), (self._pacman.player.nearestRow, self._pacman.player.nearestCol) )
                    self.followNextPathWay()

                else:
                    # glasses found way back to ghost box
                    self.state = self.STATE_NORMAL
                    self._speed = self._speed / 4

                    # give ghost a path to a random spot (containing a pellet)
                    (randRow, randCol) = (0, 0)

                    while not self._pacman.level.getMapTile((randRow, randCol)) == self._pacman.tileID[ 'pellet' ] or (randRow, randCol) == (0, 0):
                        randRow = random.randint(1, self._pacman.level.lvlHeight - 2)
                        randCol = random.randint(1, self._pacman.level.lvlWidth - 2)

                    self.currentPath = self._pacman.path.findPath( (self.nearestRow, self.nearestCol), (randRow, randCol) )
                    self.followNextPathWay()

    def runHome(self):
        # make them run
        self._speed = self._speed * 4
        # and send them to the ghost box
        self.x = self.nearestCol * self._pacman.TILE_WIDTH
        self.y = self.nearestRow * self._pacman.TILE_HEIGHT
        self.currentPath = self._pacman.path.findPath( (self.nearestRow, self.nearestCol), (self._pacman.level.getGhostBoxPos()[0]+1, self._pacman.level.getGhostBoxPos()[1]) )
        self.followNextPathWay()

    def restart(self):
        # move ghosts back to home
        self.x = self.homeX
        self.y = self.homeY
        self._velX = 0
        self._velY = 0
        self.state = Ghost.STATE_NORMAL
        self._speed = 1
        self.move()

        # give each ghost a path to a random spot (containing a pellet)
        (randRow, randCol) = (0, 0)

        while not self._pacman.level.getMapTile((randRow, randCol)) == self._pacman.tileID[ 'pellet' ] or (randRow, randCol) == (0, 0):
            randRow = random.randint(1, self._pacman.level.lvlHeight - 2)
            randCol = random.randint(1, self._pacman.level.lvlWidth - 2)

        # print "Ghost " + str(i) + " headed towards " + str((randRow, randCol))
        self.currentPath = self._pacman.path.findPath( (self.nearestRow, self.nearestCol), (randRow, randCol) )
        self.followNextPathWay()
