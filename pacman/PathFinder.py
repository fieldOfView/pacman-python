#      _____________________
# ___/  path finding class  \_______________________________________________

class PathFinder():

    def __init__(self):
        # map is a 1-DIMENSIONAL array.
        # use the Unfold( (row, col) ) function to convert a 2D coordinate pair
        # into a 1D index to use with this array.
        self._map = {}
        self.size = (-1, -1) # rows by columns

        self._pathChainRev = ""
        self._pathChain = ""

        # starting and ending nodes
        self._start = (-1, -1)
        self._end = (-1, -1)

        # current node (used by algorithm)
        self._current = (-1, -1)

        # open and closed lists of nodes to consider (used by algorithm)
        self._openList= []
        self._closedList = []

        # used in algorithm (adjacent neighbors path finder is allowed to consider)
        self._neighborSet = [ (0, -1), (0, 1), (-1, 0), (1, 0) ]

    def resizeMap(self, mapSize):
        (numRows, numCols) = mapSize
        self._map = {}
        self.size = (numRows, numCols)

        # initialize path_finder map to a 2D array of empty nodes
        for row in range(0, self.size[0], 1):
            for col in range(0, self.size[1], 1):
                self.set( (row, col), Node() )
                self.setType( (row, col), 0 )

    def cleanUpTemp(self):

        # this resets variables needed for a search (but preserves the same map / maze)

        self._pathChainRev = ""
        self._pathChain = ""
        self._current = (-1, -1)
        self._openList= []
        self._closedList = []

    def findPath(self, startPos, endPos ):

        self.cleanUpTemp()

        # (row, col) tuples
        self._start = startPos
        self._end = endPos

        # add start node to open list
        self.addToOpenList( self._start )
        self.setG ( self._start, 0 )
        self.setH ( self._start, 0 )
        self.setF ( self._start, 0 )

        doContinue = True

        while (doContinue == True):

            thisLowestFNode = self.getLowestFNode()

            if not thisLowestFNode == self._end and not thisLowestFNode == False:
                self._current = thisLowestFNode
                self.removeFromOpenList( self._current )
                self.addToClosedList( self._current )

                for offset in self._neighborSet:
                    thisNeighbor = (self._current[0] + offset[0], self._current[1] + offset[1])

                    if not thisNeighbor[0] < 0 and not thisNeighbor[1] < 0 and not thisNeighbor[0] > self.size[0] - 1 and not thisNeighbor[1] > self.size[1] - 1 and not self.getType( thisNeighbor ) == 1:
                        cost = self.getG( self._current ) + 10

                        if self.isInOpenList( thisNeighbor ) and cost < self.getG( thisNeighbor ):
                            self.removeFromOpenList( thisNeighbor )

                        #if self.isInClosedList( thisNeighbor ) and cost < self.getG( thisNeighbor ):
                        #   self.removeFromClosedList( thisNeighbor )

                        if not self.isInOpenList( thisNeighbor ) and not self.isInClosedList( thisNeighbor ):
                            self.addToOpenList( thisNeighbor )
                            self.setG( thisNeighbor, cost )
                            self.calcH( thisNeighbor )
                            self.calcF( thisNeighbor )
                            self.setParent( thisNeighbor, self._current )
            else:
                doContinue = False

        if thisLowestFNode == False:
            return False

        # reconstruct path
        self._current = self._end
        while not self._current == self._start:
            # build a string representation of the path using R, L, D, U
            if self._current[1] > self.getParent(self._current)[1]:
                self._pathChainRev += 'R'
            elif self._current[1] < self.getParent(self._current)[1]:
                self._pathChainRev += 'L'
            elif self._current[0] > self.getParent(self._current)[0]:
                self._pathChainRev += 'D'
            elif self._current[0] < self.getParent(self._current)[0]:
                self._pathChainRev += 'U'
            self._current = self.getParent(self._current)
            self.setType( self._current, 4)

        # because pathChainRev was constructed in reverse order, it needs to be reversed!
        for i in range(len(self._pathChainRev) - 1, -1, -1):
            self._pathChain += self._pathChainRev[i]

        # set start and ending positions for future reference
        self.setType( self._start, 2)
        self.setType( self._end, 3)

        return self._pathChain

    def unfold(self, position):
        # this function converts a 2D array coordinate pair (row, col)
        # to a 1D-array index, for the object's 1D map array.
        (row, col) = position
        return (row * self.size[1]) + col

    def set(self, position, newNode):
        # sets the value of a particular map cell (usually refers to a node object)
        (row, col) = position
        self._map[ self.unfold((row, col)) ] = newNode

    def getType(self, position):
        (row, col) = position
        return self._map[ self.unfold((row, col)) ].type

    def setType(self, position, newValue):
        (row, col) = position
        self._map[ self.unfold((row, col)) ].type = newValue

    def getF(self, position):
        (row, col) = position
        return self._map[ self.unfold((row, col)) ].f

    def getG(self, position):
        (row, col) = position
        return self._map[ self.unfold((row, col)) ].g

    def getH(self, position):
        (row, col) = position
        return self._map[ self.unfold((row, col)) ].h

    def setG(self, position, newValue ):
        (row, col) = position
        self._map[ self.unfold((row, col)) ].g = newValue

    def setH(self, position, newValue ):
        (row, col) = position
        self._map[ self.unfold((row, col)) ].h = newValue

    def setF(self, position, newValue ):
        (row, col) = position
        self._map[ self.unfold((row, col)) ].f = newValue

    def calcH(self, position):
        (row, col) = position
        self._map[ self.unfold((row, col)) ].h = abs(row - self._end[0]) + abs(col - self._end[0])

    def calcF(self, position):
        (row, col) = position
        unfoldIndex = self.unfold((row, col))
        self._map[unfoldIndex].f = self._map[unfoldIndex].g + self._map[unfoldIndex].h

    def addToOpenList(self, position ):
        (row, col) = position
        self._openList.append( (row, col) )

    def removeFromOpenList(self, position ):
        (row, col) = position
        self._openList.remove( (row, col) )

    def isInOpenList(self, position ):
        (row, col) = position
        if self._openList.count( (row, col) ) > 0:
            return True
        else:
            return False

    def getLowestFNode(self):
        lowestValue = 1000 # start arbitrarily high
        lowestPair = (-1, -1)

        for iOrderedPair in self._openList:
            if self.getF( iOrderedPair ) < lowestValue:
                lowestValue = self.getF( iOrderedPair )
                lowestPair = iOrderedPair

        if not lowestPair == (-1, -1):
            return lowestPair
        else:
            return False

    def addToClosedList(self, position ):
        (row, col) = position
        self._closedList.append( (row, col) )

    def isInClosedList(self, position ):
        (row, col) = position
        if self._closedList.count( (row, col) ) > 0:
            return True
        else:
            return False

    def setParent(self, position, parentPosition ):
        (row, col) = position
        (parentRow, parentCol) = parentPosition
        self._map[ self.unfold((row, col)) ].parent = (parentRow, parentCol)

    def getParent(self, position ):
        (row, col) = position
        return self._map[ self.unfold((row, col)) ].parent

#      ___________________
# ___/  base object class  \_______________________________________________

class Node():

    def __init__(self):
        self.g = -1 # movement cost to move from previous node to this one (usually +10)
        self.h = -1 # estimated movement cost to move from this node to the ending node (remaining horizontal and vertical steps * 10)
        self.f = -1 # total movement cost of this node (= g + h)
        # parent node - used to trace path back to the starting node at the end
        self.parent = (-1, -1)
        # node type - 0 for empty space, 1 for wall (optionally, 2 for starting node and 3 for end)
        self.type = -1
