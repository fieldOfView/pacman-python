#      _____________________
# ___/  level object class  \_______________________________________________

import sys, os, random
from Game import Game
from Ghost import Ghost

class Level():

    def __init__(self, pacman):
        self._pacman = pacman
        self.lvlWidth = 0
        self.lvlHeight = 0
        self.edgeLightColor = (255, 255, 0, 255)
        self.edgeShadowColor = (255, 150, 0, 255)
        self.fillColor = (0, 255, 255, 255)
        self.pelletColor = (255, 255, 255, 255)

        self._map = {}

        self._pellets = 0
        self._powerPelletBlinkTimer = 0
        self._pelletsDisplayList = None

        self._pacman.sounds.register("pellet0", "pellet1.wav")
        self._pacman.sounds.register("pellet1", "pellet2.wav")
        self._pacman.sounds.register("powerpellet", "powerpellet.wav")

    def setMapTile(self, position, newValue):
        (row, col) = position
        self._map[ (row * self.lvlWidth) + col ] = newValue

    def getMapTile(self, position):
        (row, col) = position
        if row >= 0 and row < self.lvlHeight and col >= 0 and col < self.lvlWidth:
            return self._map[ (row * self.lvlWidth) + col ]
        else:
            return 0

    def isWall(self, position):
        (row, col) = position
        if row > self.lvlHeight - 1 or row < 0:
            return True

        if col > self.lvlWidth - 1 or col < 0:
            return True

        # check the offending tile ID
        result = self.getMapTile((row, col))

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
                if  self._pacman.TILE_WIDTH > possiblePlayerX - (iCol * self._pacman.TILE_WIDTH) > -self._pacman.TILE_WIDTH and self._pacman.TILE_HEIGHT > possiblePlayerY - (iRow * self._pacman.TILE_HEIGHT) > -self._pacman.TILE_HEIGHT:

                    if self.isWall((iRow, iCol)):
                        numCollisions += 1

        if numCollisions > 0:
            return True
        else:
            return False


    def checkIfHit(self, playerPosition, position, cushion):
        (playerX, playerY) = playerPosition
        (x, y) = position
        if cushion > playerX - x  > -cushion and cushion > playerY - y > -cushion:
            return True
        else:
            return False


    def checkIfHitSomething(self, playerPosition, position):
        (playerX, playerY) = playerPosition
        (row, col) = position
        for iRow in range(row - 1, row + 2, 1):
            for iCol in range(col - 1, col + 2, 1):

                if  self._pacman.TILE_WIDTH > playerX - (iCol * self._pacman.TILE_WIDTH) > -self._pacman.TILE_WIDTH and self._pacman.TILE_HEIGHT > playerY - (iRow * self._pacman.TILE_HEIGHT) > -self._pacman.TILE_HEIGHT:
                    # check the offending tile ID
                    result = self.getMapTile((iRow, iCol))

                    if result == self._pacman.tileID[ 'pellet' ]:
                        # got a pellet
                        self.setMapTile((iRow, iCol), 0)
                        self._pacman.sounds.play("pellet%d" % self._pacman.player.pelletSndNum)
                        self._pacman.player.pelletSndNum = 1 - self._pacman.player.pelletSndNum

                        self._pellets -= 1

                        self._pacman.game.addToScore(1)

                        self._pelletsDisplayList = None

                        if self._pellets == 0:
                            # no more pellets left!
                            # WON THE LEVEL
                            self._pacman.game.setState( Game.STATE_WAIT_LEVEL_CLEAR )


                    elif result == self._pacman.tileID[ 'pellet-power' ]:
                        # got a power pellet
                        self.setMapTile((iRow, iCol), 0)
                        self._pacman.sounds.stop()
                        self._pacman.sounds.play("powerpellet")

                        self._pacman.game.addToScore(2)
                        self._pacman.game.ghostValue = 5

                        self._pelletsDisplayList = None

                        self._pacman.game.ghostTimer = 360
                        for i in range(0, 4, 1):
                            if self._pacman.ghosts[i].state == Ghost.STATE_NORMAL:
                                self._pacman.ghosts[i].state = Ghost.STATE_VULNERABLE

                                """
                                # Must line up with grid before invoking a new path (for now)
                                self._pacman.ghosts[i].x = self._pacman.ghosts[i].nearestCol * self._pacman.TILE_HEIGHT
                                self._pacman.ghosts[i].y = self._pacman.ghosts[i].nearestRow * self._pacman.TILE_WIDTH

                                # give each ghost a path to a random spot (containing a pellet)
                                (randRow, randCol) = (0, 0)

                                while not self.getMapTile((randRow, randCol)) == self._pacman.tileID[ 'pellet' ] or (randRow, randCol) == (0, 0):
                                    randRow = random.randint(1, self.lvlHeight - 2)
                                    randCol = random.randint(1, self.lvlWidth - 2)
                                self._pacman.ghosts[i].currentPath = path.findPath( (self._pacman.ghosts[i].nearestRow, self._pacman.ghosts[i].nearestCol), (randRow, randCol) )

                                self._pacman.ghosts[i].followNextPathWay()
                                """

                    elif result == self._pacman.tileID[ 'door-h' ]:
                        # ran into a horizontal door
                        for i in range(0, self.lvlWidth, 1):
                            if not i == iCol:
                                if self.getMapTile((iRow, i)) == self._pacman.tileID[ 'door-h' ]:
                                    self._pacman.player.x = i * self._pacman.TILE_WIDTH

                                    if self._pacman.player.velX > 0:
                                        self._pacman.player.x += self._pacman.TILE_WIDTH
                                    else:
                                        self._pacman.player.x -= self._pacman.TILE_WIDTH

                    elif result == self._pacman.tileID[ 'door-v' ]:
                        # ran into a vertical door
                        for i in range(0, self.lvlHeight, 1):
                            if not i == iRow:
                                if self.getMapTile((i, iCol)) == self._pacman.tileID[ 'door-v' ]:
                                    self._pacman.player.y = i * self._pacman.TILE_HEIGHT

                                    if self._pacman.player.velY > 0:
                                        self._pacman.player.y += self._pacman.TILE_HEIGHT
                                    else:
                                        self._pacman.player.y -= self._pacman.TILE_HEIGHT

    def getGhostBoxPos(self):
        for row in range(0, self.lvlHeight, 1):
            for col in range(0, self.lvlWidth, 1):
                if self.getMapTile((row, col)) == self._pacman.tileID[ 'ghost-door' ]:
                    return (row, col)

        return False

    def getPathwayPairPos(self):
        doorArray = []

        for row in range(0, self.lvlHeight, 1):
            for col in range(0, self.lvlWidth, 1):
                if self.getMapTile((row, col)) == self._pacman.tileID[ 'door-h' ]:
                    # found a horizontal door
                    doorArray.append( (row, col) )
                elif self.getMapTile((row, col)) == self._pacman.tileID[ 'door-v' ]:
                    # found a vertical door
                    doorArray.append( (row, col) )

        if len(doorArray) == 0:
            return False

        chosenDoor = random.randint(0, len(doorArray) - 1)

        if self.getMapTile( doorArray[chosenDoor] ) == self._pacman.tileID[ 'door-h' ]:
            # horizontal door was chosen
            # look for the opposite one
            for i in range(0, self.lvlWidth, 1):
                if not i == doorArray[chosenDoor][1]:
                    if self.getMapTile((doorArray[chosenDoor][0], i)) == self._pacman.tileID[ 'door-h' ]:
                        return doorArray[chosenDoor], (doorArray[chosenDoor][0], i)
        else:
            # vertical door was chosen
            # look for the opposite one
            for i in range(0, self.lvlHeight, 1):
                if not i == doorArray[chosenDoor][0]:
                    if self.getMapTile((i, doorArray[chosenDoor][1])) == self._pacman.tileID[ 'door-v' ]:
                        return doorArray[chosenDoor], (i, doorArray[chosenDoor][1])

        return False

    def printMap(self):
        for row in range(0, self.lvlHeight, 1):
            outputLine = ""
            for col in range(0, self.lvlWidth, 1):

                outputLine += str( self.getMapTile((row, col)) ) + ", "

            # print outputLine

    def drawMap(self, drawPellets = False):
        self._powerPelletBlinkTimer += 1
        if self._powerPelletBlinkTimer == 60:
            self._powerPelletBlinkTimer = 0

        drawData = {}

        if drawPellets and self._pelletsDisplayList:
            self._pacman.graphics.drawMultiple([self._pelletsDisplayList])
            return

        for row in range(0, self.lvlHeight, 1):
            outputLine = ""
            for col in range(0, self.lvlWidth, 1):

                useTile = self.getMapTile((row, col))
                if not useTile == 0 and not useTile == self._pacman.tileID['door-h'] and not useTile == self._pacman.tileID['door-v']:
                    # if this isn't a blank tile
                    position = (col * self._pacman.TILE_WIDTH, row * self._pacman.TILE_HEIGHT)
                    surface = None

                    if drawPellets:
                        if useTile in [self._pacman.tileID['pellet'], self._pacman.tileID['pellet-power']]:
                            surface = self._pacman.tileIDImage[ useTile ]

                    else:
                        if useTile in [self._pacman.tileID['showlogo'], self._pacman.tileID['hiscores']]:
                            surface = None

                        elif useTile not in [self._pacman.tileID['pellet-power'], self._pacman.tileID['pellet']]:
                            surface = self._pacman.tileIDImage[ useTile ]

                    if surface:
                        if surface not in drawData:
                            drawData[surface] = []
                        drawData[surface].append((position, drawPellets))

        if drawPellets:
            self._pelletsDisplayList = self._pacman.graphics.createList()
            self._pelletsDisplayList.begin()

        self._pacman.graphics.drawMultiple(drawData, immediate = True)

        if drawPellets:
            self._pelletsDisplayList.end()
            self._pacman.graphics.drawMultiple([self._pelletsDisplayList])

    def loadLevel(self, levelNum):
        try:
            f = open(os.path.join(sys.path[0], "res", "levels", str(levelNum) + ".txt"), 'r')
        except FileNotFoundError:
            # no more levels!
            self._pacman.game.setState( Game.STATE_GAME_OVER )
            return

        self._map = {}
        self._pellets = 0
        self._pelletsDisplayList = None

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
                    self._pacman.fruit.fruitType = int( str_splitBySpace[2] )

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

                            self._pacman.player.homeX = k * self._pacman.TILE_WIDTH
                            self._pacman.player.homeY = rowNum * self._pacman.TILE_HEIGHT
                            self.setMapTile((rowNum, k), 0 )

                        elif thisID >= 10 and thisID <= 13:
                            # one of the ghosts

                            self._pacman.ghosts[thisID - 10].homeX = k * self._pacman.TILE_WIDTH
                            self._pacman.ghosts[thisID - 10].homeY = rowNum * self._pacman.TILE_HEIGHT
                            self.setMapTile((rowNum, k), 0 )

                        elif thisID == 2:
                            # pellet

                            self._pellets += 1

                    rowNum += 1


        # reload all tiles and set appropriate colors
        self._pacman.getCrossRef()

        # load map into the pathfinder object
        self._pacman.path.resizeMap( (self.lvlHeight, self.lvlWidth) )

        for row in range(0, self._pacman.path.size[0], 1):
            for col in range(0, self._pacman.path.size[1], 1):
                if self.isWall( (row, col) ):
                    self._pacman.path.setType( (row, col), 1 )
                else:
                    self._pacman.path.setType( (row, col), 0 )

        # draw everything but pellets into buffer
        self._pacman.graphics.createBuffer((self.lvlWidth, self.lvlHeight))
        self.drawMap(drawPellets = False)
        self._pacman.graphics.closeBuffer()

        # do all the level-starting stuff
        self.restart()

    def restart(self):
        for i in range(0, 4, 1):
            self._pacman.ghosts[i].restart()

        self._pacman.fruit.active = False

        self._pacman.game.fruitTimer = 0

        self._pacman.player.x = self._pacman.player.homeX
        self._pacman.player.y = self._pacman.player.homeY

        self._pacman.player.stop()