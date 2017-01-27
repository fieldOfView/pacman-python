#! /usr/bin/python

# pacman.pyw
# By David Reilly

# Modified by Andy Sommerville, 8 October 2007:
# - Changed hard-coded DOS paths to os.path calls
# - Added constant SCRIPT_PATH (so you don't need to have pacman.pyw and res in your cwd, as long
# -   as those two are in the same directory)
# - Changed text-file reading to accomodate any known EOLn method (\n, \r, or \r\n)
# - I (happily) don't have a Windows box to test this. Blocks marked "WIN???"
# -   should be examined if this doesn't run in Windows
# - Added joystick support (configure by changing JS_* constants)
# - Added a high-score list. Depends on wx for querying the user's name

# Modified by Andy Sommerville, 11 October 2007:
# - Mom's eyes aren't what they used to be, so I'm switching 16x16 tiles to 24x24
#   Added constants TILE_WIDTH,TILE_HEIGHT to make this easier to change later.

import pygame, sys, os, random
from pygame.locals import *

# WIN???
SCRIPT_PATH=sys.path[0]

TILE_WIDTH=TILE_HEIGHT=24

# NO_GIF_TILES -- tile numbers which do not correspond to a GIF file
# currently only "23" for the high-score list
NO_GIF_TILES=[23]

NO_WX=0 # if set, the high-score code will not attempt to ask the user his name
USER_NAME="User" # USER_NAME=os.getlogin() # the default user name if wx fails to load or NO_WX
                 # Oops! os.getlogin() only works if you launch from a terminal
# constants for the high-score display
HS_FONT_SIZE=14
HS_LINE_HEIGHT=16
HS_WIDTH=408
HS_HEIGHT=120
HS_XOFFSET=48
HS_YOFFSET=384
HS_ALPHA=200

# new constants for the score's position
SCORE_XOFFSET=50 # pixels from left edge
SCORE_YOFFSET=34 # pixels from bottom edge (to top of score)
SCORE_COLWIDTH=13 # width of each character

# Joystick defaults - maybe add a Preferences dialog in the future?
JS_DEVNUM=0 # device 0 (pygame joysticks always start at 0). if JS_DEVNUM is not a valid device, will use 0
JS_XAXIS=0 # axis 0 for left/right (default for most joysticks)
JS_YAXIS=1 # axis 1 for up/down (default for most joysticks)
JS_STARTBUTTON=9 # button number to start the game. this is a matter of personal preference, and will vary from device to device

# See getCrossRef() -- where these colors occur in a GIF, they are replaced according to the level file
IMG_EDGE_LIGHT_COLOR = (0xff,0xce,0xff,0xff)
IMG_FILL_COLOR = (0x84,0x00,0x84,0xff)
IMG_EDGE_SHADOW_COLOR = (0xff,0x00,0xff,0xff)
IMG_PELLET_COLOR = (0x80,0x00,0x80,0xff)

# Must come before pygame.init()
pygame.mixer.pre_init(22050,16,2,512)
pygame.mixer.init()


clock = pygame.time.Clock()
pygame.init()

window = pygame.display.set_mode((1, 1))
pygame.display.set_caption("Pacman")

screen = pygame.display.get_surface()

img_Background = pygame.image.load(os.path.join(SCRIPT_PATH,"res","backgrounds","1.gif")).convert()

snd_pellet = {}
snd_pellet[0] = pygame.mixer.Sound(os.path.join(SCRIPT_PATH,"res","sounds","pellet1.wav"))
snd_pellet[1] = pygame.mixer.Sound(os.path.join(SCRIPT_PATH,"res","sounds","pellet2.wav"))
snd_powerpellet = pygame.mixer.Sound(os.path.join(SCRIPT_PATH,"res","sounds","powerpellet.wav"))
snd_eatgh = pygame.mixer.Sound(os.path.join(SCRIPT_PATH,"res","sounds","eatgh2.wav"))
snd_fruitbounce = pygame.mixer.Sound(os.path.join(SCRIPT_PATH,"res","sounds","fruitbounce.wav"))
snd_eatfruit = pygame.mixer.Sound(os.path.join(SCRIPT_PATH,"res","sounds","eatfruit.wav"))
snd_extralife = pygame.mixer.Sound(os.path.join(SCRIPT_PATH,"res","sounds","extralife.wav"))

ghostcolor = {}
ghostcolor[0] = (255, 0, 0, 255)
ghostcolor[1] = (255, 128, 255, 255)
ghostcolor[2] = (128, 255, 255, 255)
ghostcolor[3] = (255, 128, 0, 255)
ghostcolor[4] = (50, 50, 255, 255) # blue, vulnerable ghost
ghostcolor[5] = (255, 255, 255, 255) # white, flashing ghost

#      ___________________
# ___/  class definitions  \_______________________________________________

class Game():

    def __init__(self, pacman):
        self.pacman = pacman

        self.levelNum = 0
        self.score = 0
        self.lives = 3

        # game "mode" variable
        # 1 = normal
        # 2 = hit ghost
        # 3 = game over
        # 4 = wait to start
        # 5 = wait after eating ghost
        # 6 = wait after finishing level
        self.mode = 0
        self.modeTimer = 0
        self.ghostTimer = 0
        self.ghostValue = 0
        self.fruitTimer = 0
        self.fruitScoreTimer = 0
        self.fruitScorePos = (0, 0)

        self.setMode( 3 )

        # camera variables
        self.screenPixelPos = (0, 0) # absolute x,y position of the screen from the upper-left corner of the level
        self.screenNearestTilePos = (0, 0) # nearest-tile position of the screen from the UL corner
        self.screenPixelOffset = (0, 0) # offset in pixels of the screen from its nearest-tile position

        self.screenTileSize = (23, 21)
        self.screenSize = (self.screenTileSize[1] * TILE_WIDTH, self.screenTileSize[0] * TILE_HEIGHT)

        # numerical display digits
        self.digit = {}
        for i in range(0, 10, 1):
            self.digit[i] = pygame.image.load(os.path.join(SCRIPT_PATH,"res","text",str(i) + ".gif")).convert()
        self.imLife = pygame.image.load(os.path.join(SCRIPT_PATH,"res","text","life.gif")).convert()
        self.imGameOver = pygame.image.load(os.path.join(SCRIPT_PATH,"res","text","gameover.gif")).convert()
        self.imReady = pygame.image.load(os.path.join(SCRIPT_PATH,"res","text","ready.gif")).convert()
        self.imLogo = pygame.image.load(os.path.join(SCRIPT_PATH,"res","text","logo.gif")).convert()
        self.imHiscores = self.makeHiScoreList()

    def defaultHiScoreList(self):
            return [ (100000,"David") , (80000,"Andy") , (60000,"Count Pacula") , (40000,"Cleopacra") , (20000,"Brett Favre") , (10000,"Sergei Pachmaninoff") ]

    def getHiScores(self):
            """If res/hiscore.txt exists, read it. If not, return the default high scores.
               Output is [ (score,name) , (score,name) , .. ]. Always 6 entries."""
            try:
              f=open(os.path.join(SCRIPT_PATH,"res","hiscore.txt"))
              hs=[]
              for line in f:
                while len(line)>0 and (line[0]=="\n" or line[0]=="\r"): line=line[1:]
                while len(line)>0 and (line[-1]=="\n" or line[-1]=="\r"): line=line[:-1]
                score=int(line.split(" ")[0])
                name=line.partition(" ")[2]
                if score>99999999: score=99999999
                if len(name)>22: name=name[:22]
                hs.append((score,name))
              f.close()
              if len(hs)>6: hs=hs[:6]
              while len(hs)<6: hs.append((0,""))
              return hs
            except IOError:
              return self.defaultHiScorelist()

    def writeHiScores(self,hs):
            """Given a new list, write it to the default file."""
            fname=os.path.join(SCRIPT_PATH,"res","hiscore.txt")
            f=open(fname,"w")
            for line in hs:
              f.write(str(line[0])+" "+line[1]+"\n")
            f.close()

    def getPlayerName(self):
            """Ask the player his name, to go on the high-score list."""
            if NO_WX: return USER_NAME
            try:
              import wx
            except:
              print("Pacman Error: No module wx. Can not ask the user his name!")
              print("     :(       Download wx from http://www.wxpython.org/")
              print("     :(       To avoid seeing this error again, set NO_WX in file pacman.pyw.")
              return USER_NAME
            app=wx.App(None)
            dlog=wx.TextEntryDialog(None,"You made the high-score list! Name:")
            dlog.ShowModal()
            name=dlog.getValue()
            dlog.Destroy()
            app.Destroy()
            return name

    def updateHiScores(self,newscore):
            """Add newscore to the high score list, if appropriate."""
            hs=self.getHiScores()
            for line in hs:
              if newscore>=line[0]:
                hs.insert(hs.index(line),(newscore,self.getplayername()))
                hs.pop(-1)
                break
            self.writeHiScores(hs)

    def makeHiScoreList(self):
            "Read the High-Score file and convert it to a useable Surface."
            # My apologies for all the hard-coded constants.... -Andy
            f=pygame.font.Font(os.path.join(SCRIPT_PATH,"res","VeraMoBd.ttf"),HS_FONT_SIZE)
            scoresurf=pygame.Surface((HS_WIDTH,HS_HEIGHT),pygame.SRCALPHA)
            scoresurf.set_alpha(HS_ALPHA)
            linesurf=f.render(" "*18+"HIGH SCORES",1,(255,255,0))
            scoresurf.blit(linesurf,(0,0))
            hs=self.getHiScores()
            vpos=0
            for line in hs:
              vpos+=HS_LINE_HEIGHT
              linesurf=f.render(line[1].rjust(22)+str(line[0]).rjust(9),1,(255,255,255))
              scoresurf.blit(linesurf,(0,vpos))
            return scoresurf

    def drawMidGameHiScores(self):
            """Redraw the high-score list image after pacman dies."""
            self.imHiscores=self.makeHiScoreList()

    def startNewGame(self):
        self.levelNum = 1
        self.score = 0
        self.lives = 3

        self.setMode( 4 )
        self.pacman.level.loadLevel( self.pacman.game.getLevelNum() )

    def addToScore(self, amount):

        extraLifeSet = [25000, 50000, 100000, 150000]

        for specialScore in extraLifeSet:
            if self.score < specialScore and self.score + amount >= specialScore:
                snd_extralife.play()
                self.pacman.game.lives += 1

        self.score += amount


    def drawScore(self):
        self.drawNumber (self.score, (SCORE_XOFFSET, self.screenSize[1] - SCORE_YOFFSET) )

        for i in range(0, self.lives, 1):
            screen.blit (self.imLife, (34 + i * 10 + 16, self.screenSize[1] - 18) )

        screen.blit (self.pacman.fruit.imFruit[ self.pacman.fruit.fruitType ], (4 + 16, self.screenSize[1] - 28) )

        if self.mode == 3:
            screen.blit (self.imGameOver, (self.screenSize[0] / 2 - (self.imGameOver.get_width()/2), self.screenSize[1] / 2 - (self.imGameOver.get_height()/2)) )
        elif self.mode == 4:
            screen.blit (self.imReady, (self.screenSize[0] / 2 - 20, self.screenSize[1] / 2 + 12) )

        self.drawNumber (self.levelNum, (0, self.screenSize[1] - 20) )

    def drawNumber(self, number, position):
        (x, y) = position
        strNumber = str(int(number))

        for i in range(0, len(strNumber), 1):
            iDigit = int(strNumber[i])
            screen.blit (self.digit[ iDigit ], (x + i * SCORE_COLWIDTH, y) )

    def smartMoveScreen(self):

        possibleScreenX = self.pacman.player.x - self.screenTileSize[1] / 2 * TILE_WIDTH
        possibleScreenY = self.pacman.player.y - self.screenTileSize[0] / 2 * TILE_HEIGHT

        if possibleScreenX < 0:
            possibleScreenX = 0
        elif possibleScreenX > self.pacman.level.lvlWidth * TILE_WIDTH - self.screenSize[0]:
            possibleScreenX = self.pacman.level.lvlWidth * TILE_HEIGHT - self.screenSize[0]

        if possibleScreenY < 0:
            possibleScreenY = 0
        elif possibleScreenY > self.pacman.level.lvlHeight * TILE_WIDTH - self.screenSize[1]:
            possibleScreenY = self.pacman.level.lvlHeight * TILE_HEIGHT - self.screenSize[1]

        self.pacman.game.moveScreen( (possibleScreenX, possibleScreenY) )

    def moveScreen(self, newPosition ):
        (newX, newY) = newPosition
        self.screenPixelPos = newPosition
        self.screenNearestTilePos = (int(newY / TILE_HEIGHT), int(newX / TILE_WIDTH)) # nearest-tile position of the screen from the UL corner
        self.screenPixelOffset = (newX - self.screenNearestTilePos[1]*TILE_WIDTH, newY - self.screenNearestTilePos[0]*TILE_HEIGHT)

    def getScreenPos(self):
        return self.screenPixelPos

    def getLevelNum(self):
        return self.levelNum

    def setNextLevel(self):
        self.levelNum += 1

        self.setMode( 4 )
        self.pacman.level.loadLevel( self.pacman.game.getLevelNum() )

        self.pacman.player.velX = 0
        self.pacman.player.velY = 0
        self.pacman.player.anim_pacmanCurrent = self.pacman.player.anim_pacmanS


    def setMode(self, newMode):
        self.mode = newMode
        self.modeTimer = 0
        # print " ***** GAME MODE IS NOW ***** " + str(newMode)

class Node():

    def __init__(self, pacman):
        self.pacman = pacman
        self.g = -1 # movement cost to move from previous node to this one (usually +10)
        self.h = -1 # estimated movement cost to move from this node to the ending node (remaining horizontal and vertical steps * 10)
        self.f = -1 # total movement cost of this node (= g + h)
        # parent node - used to trace path back to the starting node at the end
        self.parent = (-1, -1)
        # node type - 0 for empty space, 1 for wall (optionally, 2 for starting node and 3 for end)
        self.type = -1

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
                screen.blit (self.pacman.tileIDImage[ thisTile ], (col * (TILE_WIDTH*2), row * (TILE_WIDTH*2)))

class Ghost():

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
                        self.anim[i].set_at( (x, y), ghostcolor[ self.id ] )

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
            screen.blit (self.anim[ self.animFrame ], (self.x - self.pacman.game.screenPixelPos[0], self.y - self.pacman.game.screenPixelPos[1]))
        elif self.state == 2:
            # draw vulnerable ghost

            if self.pacman.game.ghostTimer > 100:
                # blue
                screen.blit (self.pacman.ghosts[4].anim[ self.animFrame ], (self.x - self.pacman.game.screenPixelPos[0], self.y - self.pacman.game.screenPixelPos[1]))
            else:
                # blue/white flashing
                tempTimerI = int(self.pacman.game.ghostTimer / 10)
                if tempTimerI == 1 or tempTimerI == 3 or tempTimerI == 5 or tempTimerI == 7 or tempTimerI == 9:
                    screen.blit (self.pacman.ghosts[5].anim[ self.animFrame ], (self.x - self.pacman.game.screenPixelPos[0], self.y - self.pacman.game.screenPixelPos[1]))
                else:
                    screen.blit (self.pacman.ghosts[4].anim[ self.animFrame ], (self.x - self.pacman.game.screenPixelPos[0], self.y - self.pacman.game.screenPixelPos[1]))

        elif self.state == 3:
            # draw glasses
            screen.blit (self.pacman.tileIDImage[ self.pacman.tileID[ 'glasses' ] ], (self.x - self.pacman.game.screenPixelPos[0], self.y - self.pacman.game.screenPixelPos[1]))

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

    def draw(self):

        if self.pacman.game.mode == 3 or self.active == False:
            return False

        screen.blit (self.imFruit[ self.fruitType ], (self.x - self.pacman.game.screenPixelPos[0], self.y - self.pacman.game.screenPixelPos[1] - self.bounceY))


    def move(self):

        if self.active == False:
            return False

        self.bouncei += 1
        if self.bouncei == 1:
            self.bounceY = 2
        elif self.bouncei == 2:
            self.bounceY = 4
        elif self.bouncei == 3:
            self.bounceY = 5
        elif self.bouncei == 4:
            self.bounceY = 5
        elif self.bouncei == 5:
            self.bounceY = 6
        elif self.bouncei == 6:
            self.bounceY = 6
        elif self.bouncei == 9:
            self.bounceY = 6
        elif self.bouncei == 10:
            self.bounceY = 5
        elif self.bouncei == 11:
            self.bounceY = 5
        elif self.bouncei == 12:
            self.bounceY = 4
        elif self.bouncei == 13:
            self.bounceY = 3
        elif self.bouncei == 14:
            self.bounceY = 2
        elif self.bouncei == 15:
            self.bounceY = 1
        elif self.bouncei == 16:
            self.bounceY = 0
            self.bouncei = 0
            snd_fruitbounce.play()

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

                    if self.pacman.ghosts[i].state == 1:
                        # ghost is normal
                        self.pacman.game.setMode( 2 )

                    elif self.pacman.ghosts[i].state == 2:
                        # ghost is vulnerable
                        # give them glasses
                        # make them run
                        self.pacman.game.addToScore(self.pacman.game.ghostValue)
                        self.pacman.game.ghostValue = self.pacman.game.ghostValue * 2
                        snd_eatgh.play()

                        self.pacman.ghosts[i].state = 3
                        self.pacman.ghosts[i].speed = self.pacman.ghosts[i].speed * 4
                        # and send them to the ghost box
                        self.pacman.ghosts[i].x = self.pacman.ghosts[i].nearestCol * TILE_WIDTH
                        self.pacman.ghosts[i].y = self.pacman.ghosts[i].nearestRow * TILE_HEIGHT
                        self.pacman.ghosts[i].currentPath = self.pacman.path.findPath( (self.pacman.ghosts[i].nearestRow, self.pacman.ghosts[i].nearestCol), (self.pacman.level.getGhostBoxPos()[0]+1, self.pacman.level.getGhostBoxPos()[1]) )
                        self.pacman.ghosts[i].followNextPathWay()

                        # set game mode to brief pause after eating
                        self.pacman.game.setMode( 5 )

            # check for collisions with the fruit
            if self.pacman.fruit.active == True:
                if self.pacman.level.checkIfHit( (self.x, self.y), (self.pacman.fruit.x, self.pacman.fruit.y), TILE_WIDTH/2):
                    self.pacman.game.addToScore(2500)
                    self.pacman.fruit.active = False
                    self.pacman.game.fruitTimer = 0
                    self.pacman.game.fruitScoreTimer = 120
                    snd_eatfruit.play()

        else:
            # we're going to hit a wall -- stop moving
            self.velX = 0
            self.velY = 0

        # deal with power-pellet ghost timer
        if self.pacman.game.ghostTimer > 0:
            self.pacman.game.ghostTimer -= 1

            if self.pacman.game.ghostTimer == 0:
                for i in range(0, 4, 1):
                    if self.pacman.ghosts[i].state == 2:
                        self.pacman.ghosts[i].state = 1
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

        if self.pacman.game.mode == 3:
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

        screen.blit (self.anim_pacmanCurrent[ self.animFrame ], (self.x - self.pacman.game.screenPixelPos[0], self.y - self.pacman.game.screenPixelPos[1]))

        if self.pacman.game.mode == 1:
            if not self.velX == 0 or not self.velY == 0:
                # only Move mouth when pacman is moving
                self.animFrame += 1

            if self.animFrame == 9:
                # wrap to beginning
                self.animFrame = 1

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
                        snd_pellet[self.pacman.player.pelletSndNum].play()
                        self.pacman.player.pelletSndNum = 1 - self.pacman.player.pelletSndNum

                        self.pacman.level.pellets -= 1

                        self.pacman.game.addToScore(10)

                        if self.pacman.level.pellets == 0:
                            # no more pellets left!
                            # WON THE LEVEL
                            self.pacman.game.setMode( 6 )


                    elif result == self.pacman.tileID[ 'pellet-power' ]:
                        # got a power pellet
                        self.pacman.level.setMapTile((iRow, iCol), 0)
                        pygame.mixer.stop()
                        snd_powerpellet.play()

                        self.pacman.game.addToScore(100)
                        self.pacman.game.ghostValue = 200

                        self.pacman.game.ghostTimer = 360
                        for i in range(0, 4, 1):
                            if self.pacman.ghosts[i].state == 1:
                                self.pacman.ghosts[i].state = 2

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
                            screen.blit (self.pacman.tileIDImage[ useTile ], (col * TILE_WIDTH - self.pacman.game.screenPixelOffset[0], row * TILE_HEIGHT - self.pacman.game.screenPixelOffset[1]) )

                    elif useTile == self.pacman.tileID['showlogo']:
                        screen.blit (self.pacman.game.imLogo, (col * TILE_WIDTH - self.pacman.game.screenPixelOffset[0], row * TILE_HEIGHT - self.pacman.game.screenPixelOffset[1]) )

                    elif useTile == self.pacman.tileID['hiscores']:
                            screen.blit(self.pacman.game.imHiscores,(col*TILE_WIDTH-self.pacman.game.screenPixelOffset[0],row*TILE_HEIGHT-self.pacman.game.screenPixelOffset[1]))

                    else:
                        screen.blit (self.pacman.tileIDImage[ useTile ], (col * TILE_WIDTH - self.pacman.game.screenPixelOffset[0], row * TILE_HEIGHT - self.pacman.game.screenPixelOffset[1]) )

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
            self.pacman.ghosts[i].state = 1
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


#      __________________
# ___/  main game class  \_____________________________________________________

class Pacman():
    def __init__(self):
        # create the pacman
        self.player = Player(self)

        # create a path_finder object
        self.path = PathFinder(self)

        # create ghost objects
        self.ghosts = {}
        for i in range(0, 6, 1):
            # remember, ghost[4] is the blue, vulnerable ghost
            self.ghosts[i] = Ghost(self, i)

        # create piece of fruit
        self.fruit = Fruit(self)

        self.tileIDName = {} # gives tile name (when the ID# is known)
        self.tileID = {} # gives tile ID (when the name is known)
        self.tileIDImage = {} # gives tile image (when the ID# is known)

        # create game and level objects and load first level
        self.game = Game(self)
        self.level = Level(self)
        self.level.loadLevel( self.game.getLevelNum() )

        self.window = pygame.display.set_mode( self.game.screenSize, pygame.DOUBLEBUF | pygame.HWSURFACE )

        # initialise the joystick
        if pygame.joystick.get_count() > 0:
            if JS_DEVNUM < pygame.joystick.get_count():
                self.js = pygame.joystick.Joystick(JS_DEVNUM)
            else:
                self.js = pygame.joystick.Joystick(0)
            self.js.init()
        else: self.js = None

    def run(self):
        while True:

            self.checkIfCloseButton( pygame.event.get() )

            if self.game.mode == 1:
                # normal gameplay mode
                self.checkInputs()

                self.game.modeTimer += 1
                self.player.move()
                for i in range(0, 4, 1):
                    self.ghosts[i].move()
                self.fruit.move()

            elif self.game.mode == 2:
                # waiting after getting hit by a ghost
                self.game.modeTimer += 1

                if self.game.modeTimer == 90:
                    self.level.restart()

                    self.game.lives -= 1
                    if self.game.lives == -1:
                        self.game.updateHiScores(self.game.score)
                        self.game.setMode( 3 )
                        self.game.drawMidGameHiScores()
                    else:
                        self.game.setMode( 4 )

            elif self.game.mode == 3:
                # game over
                self.checkInputs()

            elif self.game.mode == 4:
                # waiting to start
                self.game.modeTimer += 1

                if self.game.modeTimer == 90:
                    self.game.setMode( 1 )
                    self.player.velX = self.player.speed

            elif self.game.mode == 5:
                # brief pause after munching a vulnerable ghost
                self.game.modeTimer += 1

                if self.game.modeTimer == 30:
                    self.game.setMode( 1 )

            elif self.game.mode == 6:
                # pause after eating all the pellets
                self.game.modeTimer += 1

                if self.game.modeTimer == 60:
                    self.game.setMode( 7 )
                    oldEdgeLightColor = self.level.edgeLightColor
                    oldEdgeShadowColor = self.level.edgeShadowColor
                    oldFillColor = self.level.fillColor

            elif self.game.mode == 7:
                # flashing maze after finishing level
                self.game.modeTimer += 1

                whiteSet = [10, 30, 50, 70]
                normalSet = [20, 40, 60, 80]

                if not whiteSet.count(self.game.modeTimer) == 0:
                    # member of white set
                    self.level.edgeLightColor = (255, 255, 255, 255)
                    self.level.edgeShadowColor = (255, 255, 255, 255)
                    self.level.fillColor = (0, 0, 0, 255)
                    self.getCrossRef()
                elif not normalSet.count(self.game.modeTimer) == 0:
                    # member of normal set
                    self.level.edgeLightColor = oldEdgeLightColor
                    self.level.edgeShadowColor = oldEdgeShadowColor
                    self.level.fillColor = oldFillColor
                    self.getCrossRef()
                elif self.game.modeTimer == 150:
                    self.game.setMode ( 8 )

            elif self.game.mode == 8:
                # blank screen before changing levels
                self.game.modeTimer += 1
                if self.game.modeTimer == 10:
                    self.game.setNextLevel()

            self.game.smartMoveScreen()

            screen.blit(img_Background, (0, 0))

            if not self.game.mode == 8:
                self.level.drawMap()

                if self.game.fruitScoreTimer > 0:
                    if self.game.modeTimer % 2 == 0:
                        self.game.drawNumber (2500, (self.fruit.x - self.game.screenPixelPos[0] - 16, self.fruit.y - self.game.screenPixelPos[1] + 4))

                for i in range(0, 4, 1):
                    self.ghosts[i].draw()
                self.fruit.draw()
                self.player.draw()

                if self.game.mode == 3:
                        screen.blit(self.game.imHiscores,(HS_XOFFSET,HS_YOFFSET))

            if self.game.mode == 5:
                self.game.drawNumber (self.game.ghostValue / 2, (self.player.x - self.game.screenPixelPos[0] - 4, self.player.y - self.game.screenPixelPos[1] + 6))

            self.game.drawScore()

            pygame.display.flip()

            clock.tick (60)


    def checkIfCloseButton(self, events):
        for event in events:
            if event.type == QUIT:
                sys.exit(0)


    def checkInputs(self):
        if self.game.mode == 1:
            if pygame.key.get_pressed()[ pygame.K_RIGHT ] or (self.js != None and self.js.get_axis(JS_XAXIS) > 0):
                if not self.level.checkIfHitWall((self.player.x + self.player.speed, self.player.y), (self.player.nearestRow, self.player.nearestCol)):
                    self.player.velX = self.player.speed
                    self.player.velY = 0

            elif pygame.key.get_pressed()[ pygame.K_LEFT ] or (self.js != None and self.js.get_axis(JS_XAXIS) < 0):
                if not self.level.checkIfHitWall((self.player.x - self.player.speed, self.player.y), (self.player.nearestRow, self.player.nearestCol)):
                    self.player.velX = -self.player.speed
                    self.player.velY = 0

            elif pygame.key.get_pressed()[ pygame.K_DOWN ] or (self.js != None and self.js.get_axis(JS_YAXIS) > 0):
                if not self.level.checkIfHitWall((self.player.x, self.player.y + self.player.speed), (self.player.nearestRow, self.player.nearestCol)):
                    self.player.velX = 0
                    self.player.velY = self.player.speed

            elif pygame.key.get_pressed()[ pygame.K_UP ] or (self.js != None and self.js.get_axis(JS_YAXIS) < 0):
                if not self.level.checkIfHitWall((self.player.x, self.player.y - self.player.speed), (self.player.nearestRow, self.player.nearestCol)):
                    self.player.velX = 0
                    self.player.velY = -self.player.speed

        if pygame.key.get_pressed()[ pygame.K_ESCAPE ]:
            sys.exit(0)

        elif self.game.mode == 3:
            if pygame.key.get_pressed()[ pygame.K_RETURN ] or (self.js != None and self.js.get_button(JS_STARTBUTTON)):
                self.game.startNewGame()



    #      _____________________________________________
    # ___/  function: Get ID-Tilename Cross References  \______________________________________

    def getCrossRef(self):

        f = open(os.path.join(SCRIPT_PATH,"res","crossref.txt"), 'r')

        lineNum = 0
        useLine = False

        for i in f.readlines():
            # print " ========= Line " + str(lineNum) + " ============ "
            while len(i)>0 and (i[-1]=='\n' or i[-1]=='\r'): i=i[:-1]
            while len(i)>0 and (i[0]=='\n' or i[0]=='\r'): i=i[1:]
            str_splitBySpace = i.split(' ')

            j = str_splitBySpace[0]

            if (j == "'" or j == "" or j == "#"):
                # comment / whitespace line
                # print " ignoring comment line.. "
                useLine = False
            else:
                # print str(wordNum) + ". " + j
                useLine = True

            if useLine == True:
                self.tileIDName[ int(str_splitBySpace[0]) ] = str_splitBySpace[1]
                self.tileID[ str_splitBySpace[1] ] = int(str_splitBySpace[0])

                thisID = int(str_splitBySpace[0])
                if not thisID in NO_GIF_TILES:
                    self.tileIDImage[ thisID ] = pygame.image.load(os.path.join(SCRIPT_PATH,"res","tiles",str_splitBySpace[1] + ".gif")).convert()
                else:
                    self.tileIDImage[ thisID ] = pygame.Surface((TILE_WIDTH,TILE_HEIGHT))

                # change colors in self.pacman.tileIDImage to match maze colors
                for y in range(0, TILE_WIDTH, 1):
                    for x in range(0, TILE_HEIGHT, 1):

                        if self.tileIDImage[ thisID ].get_at( (x, y) ) == IMG_EDGE_LIGHT_COLOR:
                            # wall edge
                            self.tileIDImage[ thisID ].set_at( (x, y), self.level.edgeLightColor )

                        elif self.tileIDImage[ thisID ].get_at( (x, y) ) == IMG_FILL_COLOR:
                            # wall fill
                            self.tileIDImage[ thisID ].set_at( (x, y), self.level.fillColor )

                        elif self.tileIDImage[ thisID ].get_at( (x, y) ) == IMG_EDGE_SHADOW_COLOR:
                            # pellet color
                            self.tileIDImage[ thisID ].set_at( (x, y), self.level.edgeShadowColor )

                        elif self.tileIDImage[ thisID ].get_at( (x, y) ) == IMG_PELLET_COLOR:
                            # pellet color
                            self.tileIDImage[ thisID ].set_at( (x, y), self.level.pelletColor )

                # print str_splitBySpace[0] + " is married to " + str_splitBySpace[1]
            lineNum += 1

#      __________________
# ___/  main code block  \_____________________________________________________

if __name__ == '__main__':
    pacman = Pacman()
    pacman.run()