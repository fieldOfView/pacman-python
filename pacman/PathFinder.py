#      _____________________
# ___/  path finding class  \_______________________________________________

from Node import Node

class PathFinder():

    def __init__(self, pacman):
        self.pacman = pacman
        # map is a 1-DIMENSIONAL array.
        # use the Unfold( (row, col) ) function to convert a 2D coordinate pair
        # into a 1D index to use with this array.
        self.map = {}
        self.size = (-1, -1) # rows by columns

        self.pathChainRev = ""
        self.pathChain = ""

        # starting and ending nodes
        self.start = (-1, -1)
        self.end = (-1, -1)

        # current node (used by algorithm)
        self.current = (-1, -1)

        # open and closed lists of nodes to consider (used by algorithm)
        self.openList = []
        self.closedList = []

        # used in algorithm (adjacent neighbors path finder is allowed to consider)
        self.neighborSet = [ (0, -1), (0, 1), (-1, 0), (1, 0) ]

    def resizeMap(self, mapSize):
        (numRows, numCols) = mapSize
        self.map = {}
        self.size = (numRows, numCols)

        # initialize path_finder map to a 2D array of empty nodes
        for row in range(0, self.size[0], 1):
            for col in range(0, self.size[1], 1):
                self.set( (row, col), Node(self.pacman) )
                self.setType( (row, col), 0 )

    def cleanUpTemp(self):

        # this resets variables needed for a search (but preserves the same map / maze)

        self.pathChainRev = ""
        self.pathChain = ""
        self.current = (-1, -1)
        self.openList = []
        self.closedList = []

    def findPath(self, startPos, endPos ):

        self.cleanUpTemp()

        # (row, col) tuples
        self.start = startPos
        self.end = endPos

        # add start node to open list
        self.addToOpenList( self.start )
        self.setG ( self.start, 0 )
        self.setH ( self.start, 0 )
        self.setF ( self.start, 0 )

        doContinue = True

        while (doContinue == True):

            thisLowestFNode = self.getLowestFNode()

            if not thisLowestFNode == self.end and not thisLowestFNode == False:
                self.current = thisLowestFNode
                self.removeFromOpenList( self.current )
                self.addToClosedList( self.current )

                for offset in self.neighborSet:
                    thisNeighbor = (self.current[0] + offset[0], self.current[1] + offset[1])

                    if not thisNeighbor[0] < 0 and not thisNeighbor[1] < 0 and not thisNeighbor[0] > self.size[0] - 1 and not thisNeighbor[1] > self.size[1] - 1 and not self.getType( thisNeighbor ) == 1:
                        cost = self.getG( self.current ) + 10

                        if self.isInOpenList( thisNeighbor ) and cost < self.getG( thisNeighbor ):
                            self.removeFromOpenList( thisNeighbor )

                        #if self.isInClosedList( thisNeighbor ) and cost < self.getG( thisNeighbor ):
                        #   self.removeFromClosedList( thisNeighbor )

                        if not self.isInOpenList( thisNeighbor ) and not self.isInClosedList( thisNeighbor ):
                            self.addToOpenList( thisNeighbor )
                            self.setG( thisNeighbor, cost )
                            self.calcH( thisNeighbor )
                            self.calcF( thisNeighbor )
                            self.setParent( thisNeighbor, self.current )
            else:
                doContinue = False

        if thisLowestFNode == False:
            return False

        # reconstruct path
        self.current = self.end
        while not self.current == self.start:
            # build a string representation of the path using R, L, D, U
            if self.current[1] > self.getParent(self.current)[1]:
                self.pathChainRev += 'R'
            elif self.current[1] < self.getParent(self.current)[1]:
                self.pathChainRev += 'L'
            elif self.current[0] > self.getParent(self.current)[0]:
                self.pathChainRev += 'D'
            elif self.current[0] < self.getParent(self.current)[0]:
                self.pathChainRev += 'U'
            self.current = self.getParent(self.current)
            self.setType( self.current, 4)

        # because pathChainRev was constructed in reverse order, it needs to be reversed!
        for i in range(len(self.pathChainRev) - 1, -1, -1):
            self.pathChain += self.pathChainRev[i]

        # set start and ending positions for future reference
        self.setType( self.start, 2)
        self.setType( self.end, 3)

        return self.pathChain

    def unfold(self, position):
        # this function converts a 2D array coordinate pair (row, col)
        # to a 1D-array index, for the object's 1D map array.
        (row, col) = position
        return (row * self.size[1]) + col

    def set(self, position, newNode):
        # sets the value of a particular map cell (usually refers to a node object)
        (row, col) = position
        self.map[ self.unfold((row, col)) ] = newNode

    def getType(self, position):
        (row, col) = position
        return self.map[ self.unfold((row, col)) ].type

    def setType(self, position, newValue):
        (row, col) = position
        self.map[ self.unfold((row, col)) ].type = newValue

    def getF(self, position):
        (row, col) = position
        return self.map[ self.unfold((row, col)) ].f

    def getG(self, position):
        (row, col) = position
        return self.map[ self.unfold((row, col)) ].g

    def getH(self, position):
        (row, col) = position
        return self.map[ self.unfold((row, col)) ].h

    def setG(self, position, newValue ):
        (row, col) = position
        self.map[ self.unfold((row, col)) ].g = newValue

    def setH(self, position, newValue ):
        (row, col) = position
        self.map[ self.unfold((row, col)) ].h = newValue

    def setF(self, position, newValue ):
        (row, col) = position
        self.map[ self.unfold((row, col)) ].f = newValue

    def calcH(self, position):
        (row, col) = position
        self.map[ self.unfold((row, col)) ].h = abs(row - self.end[0]) + abs(col - self.end[0])

    def calcF(self, position):
        (row, col) = position
        unfoldIndex = self.unfold((row, col))
        self.map[unfoldIndex].f = self.map[unfoldIndex].g + self.map[unfoldIndex].h

    def addToOpenList(self, position ):
        (row, col) = position
        self.openList.append( (row, col) )

    def removeFromOpenList(self, position ):
        (row, col) = position
        self.openList.remove( (row, col) )

    def isInOpenList(self, position ):
        (row, col) = position
        if self.openList.count( (row, col) ) > 0:
            return True
        else:
            return False

    def getLowestFNode(self):
        lowestValue = 1000 # start arbitrarily high
        lowestPair = (-1, -1)

        for iOrderedPair in self.openList:
            if self.getF( iOrderedPair ) < lowestValue:
                lowestValue = self.getF( iOrderedPair )
                lowestPair = iOrderedPair

        if not lowestPair == (-1, -1):
            return lowestPair
        else:
            return False

    def addToClosedList(self, position ):
        (row, col) = position
        self.closedList.append( (row, col) )

    def isInClosedList(self, position ):
        (row, col) = position
        if self.closedList.count( (row, col) ) > 0:
            return True
        else:
            return False

    def setParent(self, position, parentPosition ):
        (row, col) = position
        (parentRow, parentCol) = parentPosition
        self.map[ self.unfold((row, col)) ].parent = (parentRow, parentCol)

    def getParent(self, position ):
        (row, col) = position
        return self.map[ self.unfold((row, col)) ].parent

    def draw(self):
        for row in range(0, self.size[0], 1):
            for col in range(0, self.size[1], 1):

                thisTile = self.getType((row, col))
                self.pacman.screen.blit (self.pacman.tileIDImage[ thisTile ], (col * (TILE_WIDTH*2), row * (TILE_WIDTH*2)))
