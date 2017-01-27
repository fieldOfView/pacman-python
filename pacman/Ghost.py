#      _____________________
# ___/  ghost object class  \_______________________________________________

import pygame, sys, os, random

# WIN???
SCRIPT_PATH = sys.path[0]

TILE_WIDTH = TILE_HEIGHT=24

class Ghost():

    ghostcolor = [
        (255, 0, 0, 255),
        (255, 128, 255, 255),
        (128, 255, 255, 255),
        (255, 128, 0, 255),
        (50, 50, 255, 255), # blue, vulnerable ghost
        (255, 255, 255, 255) # white, flashing ghost
    ]

    def __init__(self, pacman, ghostID):
        self.pacman = pacman
        self.x = 0
        self.y = 0
        self.velX = 0
        self.velY = 0
        self.speed = 1

        self.nearestRow = 0
        self.nearestCol = 0

        self.id = ghostID

        # ghost "state" variable
        # 1 = normal
        # 2 = vulnerable
        # 3 = spectacles
        self.state = 1

        self.homeX = 0
        self.homeY = 0

        self.currentPath = ""

        self.anim = {}
        for i in range(1, 7, 1):
            self.anim[i] = pygame.image.load(os.path.join(SCRIPT_PATH,"res","sprite","ghost " + str(i) + ".gif")).convert()

            # change the ghost color in this frame
            for y in range(0, TILE_HEIGHT, 1):
                for x in range(0, TILE_WIDTH, 1):

                    if self.anim[i].get_at( (x, y) ) == (255, 0, 0, 255):
                        # default, red ghost body color
                        self.anim[i].set_at( (x, y), self.ghostcolor[ self.id ] )

        self.animFrame = 1
        self.animDelay = 0

    def draw(self):

        if self.pacman.game.mode == 3:
            return False


        # ghost eyes --
        for y in range(6,12,1):
            for x in [5,6,8,9]:
                self.anim[ self.animFrame ].set_at( (x, y), (0xf8,0xf8,0xf8,255) )
                self.anim[ self.animFrame ].set_at( (x+9, y), (0xf8,0xf8,0xf8,255) )

        if self.pacman.player.x > self.x and self.pacman.player.y > self.y:
            #player is to lower-right
            pupilSet = (8,9)
        elif self.pacman.player.x < self.x and self.pacman.player.y > self.y:
            #player is to lower-left
            pupilSet = (5,9)
        elif self.pacman.player.x > self.x and self.pacman.player.y < self.y:
            #player is to upper-right
            pupilSet = (8,6)
        elif self.pacman.player.x < self.x and self.pacman.player.y < self.y:
            #player is to upper-left
            pupilSet = (5,6)
        else:
            pupilSet = (5,9)

        for y in range(pupilSet[1], pupilSet[1] + 3, 1):
            for x in range(pupilSet[0], pupilSet[0] + 2, 1):
                self.anim[ self.animFrame ].set_at( (x, y), (0, 0, 255, 255) )
                self.anim[ self.animFrame ].set_at( (x+9, y), (0, 0, 255, 255) )
        # -- end ghost eyes

        if self.state == 1:
            # draw regular ghost (this one)
            self.pacman.screen.blit (self.anim[ self.animFrame ], (self.x - self.pacman.game.screenPixelPos[0], self.y - self.pacman.game.screenPixelPos[1]))
        elif self.state == 2:
            # draw vulnerable ghost

            if self.pacman.game.ghostTimer > 100:
                # blue
                self.pacman.screen.blit (self.pacman.ghosts[4].anim[ self.animFrame ], (self.x - self.pacman.game.screenPixelPos[0], self.y - self.pacman.game.screenPixelPos[1]))
            else:
                # blue/white flashing
                tempTimerI = int(self.pacman.game.ghostTimer / 10)
                if tempTimerI == 1 or tempTimerI == 3 or tempTimerI == 5 or tempTimerI == 7 or tempTimerI == 9:
                    self.pacman.screen.blit (self.pacman.ghosts[5].anim[ self.animFrame ], (self.x - self.pacman.game.screenPixelPos[0], self.y - self.pacman.game.screenPixelPos[1]))
                else:
                    self.pacman.screen.blit (self.pacman.ghosts[4].anim[ self.animFrame ], (self.x - self.pacman.game.screenPixelPos[0], self.y - self.pacman.game.screenPixelPos[1]))

        elif self.state == 3:
            # draw glasses
            self.pacman.screen.blit (self.pacman.tileIDImage[ self.pacman.tileID[ 'glasses' ] ], (self.x - self.pacman.game.screenPixelPos[0], self.y - self.pacman.game.screenPixelPos[1]))

        if self.pacman.game.mode == 6 or self.pacman.game.mode == 7:
            # don't animate ghost if the level is complete
            return False

        self.animDelay += 1

        if self.animDelay == 2:
            self.animFrame += 1

            if self.animFrame == 7:
                # wrap to beginning
                self.animFrame = 1

            self.animDelay = 0

    def move(self):

        self.x += self.velX
        self.y += self.velY

        self.nearestRow = int(((self.y + (TILE_HEIGHT/2)) / TILE_HEIGHT))
        self.nearestCol = int(((self.x + (TILE_HEIGHT/2)) / TILE_WIDTH))

        if (self.x % TILE_WIDTH) == 0 and (self.y % TILE_HEIGHT) == 0:
            # if the ghost is lined up with the grid again
            # meaning, it's time to go to the next path item

            if len(self.currentPath) > 0:
                self.currentPath = self.currentPath[1:]
                self.followNextPathWay()

            else:
                self.x = self.nearestCol * TILE_WIDTH
                self.y = self.nearestRow * TILE_HEIGHT

                # chase pac-man
                self.currentPath = self.pacman.path.findPath( (self.nearestRow, self.nearestCol), (self.pacman.player.nearestRow, self.pacman.player.nearestCol) )
                self.followNextPathWay()

    def followNextPathWay(self):

        # print "Ghost " + str(self.id) + " rem: " + self.currentPath

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

            else:
                # this ghost has reached his destination!!

                if not self.state == 3:
                    # chase pac-man
                    self.currentPath = self.pacman.path.findPath( (self.nearestRow, self.nearestCol), (self.pacman.player.nearestRow, self.pacman.player.nearestCol) )
                    self.followNextPathWay()

                else:
                    # glasses found way back to ghost box
                    self.state = 1
                    self.speed = self.speed / 4

                    # give ghost a path to a random spot (containing a pellet)
                    (randRow, randCol) = (0, 0)

                    while not self.pacman.level.getMapTile((randRow, randCol)) == self.pacman.tileID[ 'pellet' ] or (randRow, randCol) == (0, 0):
                        randRow = random.randint(1, self.pacman.level.lvlHeight - 2)
                        randCol = random.randint(1, self.pacman.level.lvlWidth - 2)

                    self.currentPath = self.pacman.path.findPath( (self.nearestRow, self.nearestCol), (randRow, randCol) )
                    self.followNextPathWay()
