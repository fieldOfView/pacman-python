#      _____________________
# ___/  level object class  \_______________________________________________

import pygame, sys, os, random
from Game import Game
from Ghost import Ghost

# WIN???
SCRIPT_PATH = sys.path[0]

TILE_WIDTH = TILE_HEIGHT=24

class Level():

    def __init__(self, pacman):
        self.pacman = pacman
        self.lvlWidth = 0
        self.lvlHeight = 0
        self.edgeLightColor = (255, 255, 0, 255)
        self.edgeShadowColor = (255, 150, 0, 255)
        self.fillColor = (0, 255, 255, 255)
        self.pelletColor = (255, 255, 255, 255)

        self.map = {}

        self.pellets = 0
        self.powerPelletBlinkTimer = 0

        self.snd_pellet = [
            pygame.mixer.Sound(os.path.join(SCRIPT_PATH,"res","sounds","pellet1.wav")),
            pygame.mixer.Sound(os.path.join(SCRIPT_PATH,"res","sounds","pellet2.wav"))
        ]
        self.snd_powerpellet = pygame.mixer.Sound(os.path.join(SCRIPT_PATH,"res","sounds","powerpellet.wav"))

    def setMapTile(self, position, newValue):
        (row, col) = position
        self.map[ (row * self.lvlWidth) + col ] = newValue

    def getMapTile(self, position):
        (row, col) = position
        if row >= 0 and row < self.lvlHeight and col >= 0 and col < self.lvlWidth:
            return self.map[ (row * self.lvlWidth) + col ]
        else:
            return 0

    def isWall(self, position):
        (row, col) = position
        if row > self.pacman.level.lvlHeight - 1 or row < 0:
            return True

        if col > self.pacman.level.lvlWidth - 1 or col < 0:
            return True

        # check the offending tile ID
        result = self.pacman.level.getMapTile((row, col))

        # if the tile was a wall
        if result >= 100 and result <= 199:
            return True
        else:
            return False

    def checkIfHitWall(self, possiblePlayerPosition, position):
        (possiblePlayerX, possiblePlayerY) = possiblePlayerPosition
        (row, col) = position
        numCollisions = 0

        # check each of the 9 surrounding tiles for a collision
        for iRow in range(row - 1, row + 2, 1):
            for iCol in range(col - 1, col + 2, 1):

                if  (possiblePlayerX - (iCol * TILE_WIDTH) < TILE_WIDTH) and (possiblePlayerX - (iCol * TILE_WIDTH) > -TILE_WIDTH) and (possiblePlayerY - (iRow * TILE_HEIGHT) < TILE_HEIGHT) and (possiblePlayerY - (iRow * TILE_HEIGHT) > -TILE_HEIGHT):

                    if self.isWall((iRow, iCol)):
                        numCollisions += 1

        if numCollisions > 0:
            return True
        else:
            return False


    def checkIfHit(self, playerPosition, position, cushion):
        (playerX, playerY) = playerPosition
        (x, y) = position
        if (playerX - x < cushion) and (playerX - x > -cushion) and (playerY - y < cushion) and (playerY - y > -cushion):
            return True
        else:
            return False


    def checkIfHitSomething(self, playerPosition, position):
        (playerX, playerY) = playerPosition
        (row, col) = position
        for iRow in range(row - 1, row + 2, 1):
            for iCol in range(col - 1, col + 2, 1):

                if  (playerX - (iCol * TILE_WIDTH) < TILE_WIDTH) and (playerX - (iCol * TILE_WIDTH) > -TILE_WIDTH) and (playerY - (iRow * TILE_HEIGHT) < TILE_HEIGHT) and (playerY - (iRow * TILE_HEIGHT) > -TILE_HEIGHT):
                    # check the offending tile ID
                    result = self.pacman.level.getMapTile((iRow, iCol))

                    if result == self.pacman.tileID[ 'pellet' ]:
                        # got a pellet
                        self.pacman.level.setMapTile((iRow, iCol), 0)
                        self.snd_pellet[self.pacman.player.pelletSndNum].play()
                        self.pacman.player.pelletSndNum = 1 - self.pacman.player.pelletSndNum

                        self.pacman.level.pellets -= 1

                        self.pacman.game.addToScore(10)

                        if self.pacman.level.pellets == 0:
                            # no more pellets left!
                            # WON THE LEVEL
                            self.pacman.game.setState( Game.STATE_WAIT_LEVEL_CLEAR )


                    elif result == self.pacman.tileID[ 'pellet-power' ]:
                        # got a power pellet
                        self.pacman.level.setMapTile((iRow, iCol), 0)
                        pygame.mixer.stop()
                        self.snd_powerpellet.play()

                        self.pacman.game.addToScore(100)
                        self.pacman.game.ghostValue = 200

                        self.pacman.game.ghostTimer = 360
                        for i in range(0, 4, 1):
                            if self.pacman.ghosts[i].state == Ghost.STATE_NORMAL:
                                self.pacman.ghosts[i].state = Ghost.STATE_VULNERABLE

                                """
                                # Must line up with grid before invoking a new path (for now)
                                self.pacman.ghosts[i].x = self.pacman.ghosts[i].nearestCol * TILE_HEIGHT
                                self.pacman.ghosts[i].y = self.pacman.ghosts[i].nearestRow * TILE_WIDTH

                                # give each ghost a path to a random spot (containing a pellet)
                                (randRow, randCol) = (0, 0)

                                while not self.getMapTile((randRow, randCol)) == self.pacman.tileID[ 'pellet' ] or (randRow, randCol) == (0, 0):
                                    randRow = random.randint(1, self.lvlHeight - 2)
                                    randCol = random.randint(1, self.lvlWidth - 2)
                                self.pacman.ghosts[i].currentPath = path.findPath( (self.pacman.ghosts[i].nearestRow, self.pacman.ghosts[i].nearestCol), (randRow, randCol) )

                                self.pacman.ghosts[i].followNextPathWay()
                                """

                    elif result == self.pacman.tileID[ 'door-h' ]:
                        # ran into a horizontal door
                        for i in range(0, self.pacman.level.lvlWidth, 1):
                            if not i == iCol:
                                if self.pacman.level.getMapTile((iRow, i)) == self.pacman.tileID[ 'door-h' ]:
                                    self.pacman.player.x = i * TILE_WIDTH

                                    if self.pacman.player.velX > 0:
                                        self.pacman.player.x += TILE_WIDTH
                                    else:
                                        self.pacman.player.x -= TILE_WIDTH

                    elif result == self.pacman.tileID[ 'door-v' ]:
                        # ran into a vertical door
                        for i in range(0, self.pacman.level.lvlHeight, 1):
                            if not i == iRow:
                                if self.pacman.level.getMapTile((i, iCol)) == self.pacman.tileID[ 'door-v' ]:
                                    self.pacman.player.y = i * TILE_HEIGHT

                                    if self.pacman.player.velY > 0:
                                        self.pacman.player.y += TILE_HEIGHT
                                    else:
                                        self.pacman.player.y -= TILE_HEIGHT

    def getGhostBoxPos(self):
        for row in range(0, self.lvlHeight, 1):
            for col in range(0, self.lvlWidth, 1):
                if self.getMapTile((row, col)) == self.pacman.tileID[ 'ghost-door' ]:
                    return (row, col)

        return False

    def getPathwayPairPos(self):
        doorArray = []

        for row in range(0, self.lvlHeight, 1):
            for col in range(0, self.lvlWidth, 1):
                if self.getMapTile((row, col)) == self.pacman.tileID[ 'door-h' ]:
                    # found a horizontal door
                    doorArray.append( (row, col) )
                elif self.getMapTile((row, col)) == self.pacman.tileID[ 'door-v' ]:
                    # found a vertical door
                    doorArray.append( (row, col) )

        if len(doorArray) == 0:
            return False

        chosenDoor = random.randint(0, len(doorArray) - 1)

        if self.getMapTile( doorArray[chosenDoor] ) == self.pacman.tileID[ 'door-h' ]:
            # horizontal door was chosen
            # look for the opposite one
            for i in range(0, self.pacman.level.lvlWidth, 1):
                if not i == doorArray[chosenDoor][1]:
                    if self.pacman.level.getMapTile((doorArray[chosenDoor][0], i)) == self.pacman.tileID[ 'door-h' ]:
                        return doorArray[chosenDoor], (doorArray[chosenDoor][0], i)
        else:
            # vertical door was chosen
            # look for the opposite one
            for i in range(0, self.pacman.level.lvlHeight, 1):
                if not i == doorArray[chosenDoor][0]:
                    if self.pacman.level.getMapTile((i, doorArray[chosenDoor][1])) == self.pacman.tileID[ 'door-v' ]:
                        return doorArray[chosenDoor], (i, doorArray[chosenDoor][1])

        return False

    def printMap(self):
        for row in range(0, self.lvlHeight, 1):
            outputLine = ""
            for col in range(0, self.lvlWidth, 1):

                outputLine += str( self.getMapTile((row, col)) ) + ", "

            # print outputLine

    def drawMap(self):
        self.powerPelletBlinkTimer += 1
        if self.powerPelletBlinkTimer == 60:
            self.powerPelletBlinkTimer = 0

        for row in range(-1, self.pacman.game.screenTileSize[0] +1, 1):
            outputLine = ""
            for col in range(-1, self.pacman.game.screenTileSize[1] +1, 1):

                # row containing tile that actually goes here
                actualRow = self.pacman.game.screenNearestTilePos[0] + row
                actualCol = self.pacman.game.screenNearestTilePos[1] + col

                useTile = self.getMapTile((actualRow, actualCol))
                if not useTile == 0 and not useTile == self.pacman.tileID['door-h'] and not useTile == self.pacman.tileID['door-v']:
                    # if this isn't a blank tile

                    if useTile == self.pacman.tileID['pellet-power']:
                        if self.powerPelletBlinkTimer < 30:
                            self.pacman.screen.blit (self.pacman.tileIDImage[ useTile ], (col * TILE_WIDTH - self.pacman.game.screenPixelOffset[0], row * TILE_HEIGHT - self.pacman.game.screenPixelOffset[1]) )

                    elif useTile == self.pacman.tileID['showlogo']:
                        self.pacman.screen.blit (self.pacman.game.imLogo, (col * TILE_WIDTH - self.pacman.game.screenPixelOffset[0], row * TILE_HEIGHT - self.pacman.game.screenPixelOffset[1]) )

                    elif useTile == self.pacman.tileID['hiscores']:
                            self.pacman.screen.blit(self.pacman.game.imHiscores,(col*TILE_WIDTH-self.pacman.game.screenPixelOffset[0],row*TILE_HEIGHT-self.pacman.game.screenPixelOffset[1]))

                    else:
                        self.pacman.screen.blit (self.pacman.tileIDImage[ useTile ], (col * TILE_WIDTH - self.pacman.game.screenPixelOffset[0], row * TILE_HEIGHT - self.pacman.game.screenPixelOffset[1]) )

    def loadLevel(self, levelNum):
        self.map = {}

        self.pellets = 0

        f = open(os.path.join(SCRIPT_PATH,"res","levels",str(levelNum) + ".txt"), 'r')
        lineNum=-1
        rowNum = 0
        useLine = False
        isReadingLevelData = False

        for line in f:

          lineNum += 1

            # print " ------- Level Line " + str(lineNum) + " -------- "
          while len(line)>0 and (line[-1]=="\n" or line[-1]=="\r"): line=line[:-1]
          while len(line)>0 and (line[0]=="\n" or line[0]=="\r"): line=line[1:]
          str_splitBySpace = line.split(' ')


          j = str_splitBySpace[0]

          if (j == "'" or j == ""):
                # comment / whitespace line
                # print " ignoring comment line.. "
                useLine = False
          elif j == "#":
                # special divider / attribute line
                useLine = False

                firstWord = str_splitBySpace[1]

                if firstWord == "lvlwidth":
                    self.lvlWidth = int( str_splitBySpace[2] )
                    # print "Width is " + str( self.lvlWidth )

                elif firstWord == "lvlheight":
                    self.lvlHeight = int( str_splitBySpace[2] )
                    # print "Height is " + str( self.lvlHeight )

                elif firstWord == "edgecolor":
                    # edge color keyword for backwards compatibility (single edge color) mazes
                    red = int( str_splitBySpace[2] )
                    green = int( str_splitBySpace[3] )
                    blue = int( str_splitBySpace[4] )
                    self.edgeLightColor = (red, green, blue, 255)
                    self.edgeShadowColor = (red, green, blue, 255)

                elif firstWord == "edgelightcolor":
                    red = int( str_splitBySpace[2] )
                    green = int( str_splitBySpace[3] )
                    blue = int( str_splitBySpace[4] )
                    self.edgeLightColor = (red, green, blue, 255)

                elif firstWord == "edgeshadowcolor":
                    red = int( str_splitBySpace[2] )
                    green = int( str_splitBySpace[3] )
                    blue = int( str_splitBySpace[4] )
                    self.edgeShadowColor = (red, green, blue, 255)

                elif firstWord == "fillcolor":
                    red = int( str_splitBySpace[2] )
                    green = int( str_splitBySpace[3] )
                    blue = int( str_splitBySpace[4] )
                    self.fillColor = (red, green, blue, 255)

                elif firstWord == "pelletcolor":
                    red = int( str_splitBySpace[2] )
                    green = int( str_splitBySpace[3] )
                    blue = int( str_splitBySpace[4] )
                    self.pelletColor = (red, green, blue, 255)

                elif firstWord == "fruittype":
                    self.pacman.fruit.fruitType = int( str_splitBySpace[2] )

                elif firstWord == "startleveldata":
                    isReadingLevelData = True
                        # print "Level data has begun"
                    rowNum = 0

                elif firstWord == "endleveldata":
                    isReadingLevelData = False
                    # print "Level data has ended"

          else:
                useLine = True


            # this is a map data line
          if useLine == True:

                if isReadingLevelData == True:

                    # print str( len(str_splitBySpace) ) + " tiles in this column"

                    for k in range(0, self.lvlWidth, 1):
                        self.setMapTile((rowNum, k), int(str_splitBySpace[k]) )

                        thisID = int(str_splitBySpace[k])
                        if thisID == 4:
                            # starting position for pac-man

                            self.pacman.player.homeX = k * TILE_WIDTH
                            self.pacman.player.homeY = rowNum * TILE_HEIGHT
                            self.setMapTile((rowNum, k), 0 )

                        elif thisID >= 10 and thisID <= 13:
                            # one of the ghosts

                            self.pacman.ghosts[thisID - 10].homeX = k * TILE_WIDTH
                            self.pacman.ghosts[thisID - 10].homeY = rowNum * TILE_HEIGHT
                            self.setMapTile((rowNum, k), 0 )

                        elif thisID == 2:
                            # pellet

                            self.pellets += 1

                    rowNum += 1


        # reload all tiles and set appropriate colors
        self.pacman.getCrossRef()

        # load map into the pathfinder object
        self.pacman.path.resizeMap( (self.lvlHeight, self.lvlWidth) )

        for row in range(0, self.pacman.path.size[0], 1):
            for col in range(0, self.pacman.path.size[1], 1):
                if self.isWall( (row, col) ):
                    self.pacman.path.setType( (row, col), 1 )
                else:
                    self.pacman.path.setType( (row, col), 0 )

        # do all the level-starting stuff
        self.restart()

    def restart(self):
        for i in range(0, 4, 1):
            # move ghosts back to home

            self.pacman.ghosts[i].x = self.pacman.ghosts[i].homeX
            self.pacman.ghosts[i].y = self.pacman.ghosts[i].homeY
            self.pacman.ghosts[i].velX = 0
            self.pacman.ghosts[i].velY = 0
            self.pacman.ghosts[i].state = Ghost.STATE_NORMAL
            self.pacman.ghosts[i].speed = 1
            self.pacman.ghosts[i].move()

            # give each ghost a path to a random spot (containing a pellet)
            (randRow, randCol) = (0, 0)

            while not self.getMapTile((randRow, randCol)) == self.pacman.tileID[ 'pellet' ] or (randRow, randCol) == (0, 0):
                randRow = random.randint(1, self.lvlHeight - 2)
                randCol = random.randint(1, self.lvlWidth - 2)

            # print "Ghost " + str(i) + " headed towards " + str((randRow, randCol))
            self.pacman.ghosts[i].currentPath = self.pacman.path.findPath( (self.pacman.ghosts[i].nearestRow, self.pacman.ghosts[i].nearestCol), (randRow, randCol) )
            self.pacman.ghosts[i].followNextPathWay()

        self.pacman.fruit.active = False

        self.pacman.game.fruitTimer = 0

        self.pacman.player.x = self.pacman.player.homeX
        self.pacman.player.y = self.pacman.player.homeY
        self.pacman.player.velX = 0
        self.pacman.player.velY = 0

        self.pacman.player.anim_pacmanCurrent = self.pacman.player.anim_pacmanS
        self.pacman.player.animFrame = 3
