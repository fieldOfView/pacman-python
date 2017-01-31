#      ______________________
# ___/  score manager class  \_______________________________________________

import pygame, sys, os

# WIN???
SCRIPT_PATH = sys.path[0]

TILE_WIDTH = TILE_HEIGHT=24

# constants for the high-score display
HS_FONT_SIZE = 14
HS_LINE_HEIGHT = 16
HS_WIDTH = 408
HS_HEIGHT = 120
HS_ALPHA = 200

# new constants for the score's position
SCORE_XOFFSET = 50 # pixels from left edge
SCORE_YOFFSET = 34 # pixels from bottom edge (to top of score)
SCORE_COLWIDTH = 13 # width of each character

NO_WX = 0 # if set, the high-score code will not attempt to ask the user his name
USER_NAME = "User" # USER_NAME=os.getlogin() # the default user name if wx fails to load or NO_WX
                 # Oops! os.getlogin() only works if you launch from a terminal

class Game():
    STATE_PLAYING = 1            # normal
    STATE_HIT_GHOST = 2          # hit ghost
    STATE_GAME_OVER = 3          # game over
    STATE_WAIT_START = 4         # wait to start
    STATE_WAIT_ATE_GHOST = 5     # wait after eating ghost
    STATE_WAIT_LEVEL_CLEAR = 6   # wait after eating all pellets
    STATE_FLASH_LEVEL = 7        # flash level when complete
    STATE_WAIT_LEVEL_SWITCH = 8  # wait after finishing level

    def __init__(self, pacman):
        self._pacman = pacman

        self._levelNum = 0
        self.score = 0
        self.lives = 3

        # game "state" variable
        self.state = self.STATE_GAME_OVER
        self.stateTimer = 0
        self.ghostTimer = 0
        self.ghostValue = 0
        self.fruitTimer = 0
        self.fruitScoreTimer = 0
        self.fruitScorePos = (0, 0)

        self.setState( self.STATE_GAME_OVER )

        # camera variables
        self.screenPixelPos = (0, 0) # absolute x,y position of the screen from the upper-left corner of the level
        self.screenNearestTilePos = (0, 0) # nearest-tile position of the screen from the UL corner
        self.screenPixelOffset = (0, 0) # offset in pixels of the screen from its nearest-tile position

        self.screenTileSize = (23, 21)
        self.screenSize = (self.screenTileSize[1] * TILE_WIDTH, self.screenTileSize[0] * TILE_HEIGHT)

        # numerical display digits
        self._digit = {}
        for i in range(0, 10, 1):
            self._digit[i] = self._pacman.graphics.loadImage("text",str(i) + ".gif")
        self._imLife = self._pacman.graphics.loadImage("text","life.gif")
        self._imGameOver = self._pacman.graphics.loadImage("text","gameover.gif")
        self._imReady = self._pacman.graphics.loadImage("text","ready.gif")

        self.imLogo = self._pacman.graphics.loadImage("text","logo.gif")
        self.imHiscores = self.makeHiScoreList()

        self._pacman.sounds.register("extralife", "extralife.wav")
        self._pacman.sounds.register("start", "start.wav")

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
                hs.insert(hs.index(line),(newscore,self.getPlayerName()))
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
        self._levelNum = 1
        self.score = 0
        self.lives = 3

        self.setState( self.STATE_WAIT_START )
        self._pacman.level.loadLevel( self._levelNum )
        self._pacman.sounds.play("start")

    def addToScore(self, amount):
        extraLifeSet = [25000, 50000, 100000, 150000]

        for specialScore in extraLifeSet:
            if self.score < specialScore and self.score + amount >= specialScore:
                self._pacman.sounds.play("extralife")
                self.lives += 1

        self.score += amount


    def drawScore(self):
        self.drawNumber (self.score, (SCORE_XOFFSET, self.screenSize[1] - SCORE_YOFFSET) )

        for i in range(0, self.lives, 1):
            self._pacman.graphics.blit (self._imLife, (34 + i * 10 + 16, self.screenSize[1] - 18) )

        self._pacman.graphics.blit (self._pacman.fruit.imFruit[ self._pacman.fruit.fruitType ], (4 + 16, self.screenSize[1] - 28) )

        if self.state == self.STATE_GAME_OVER:
            self._pacman.graphics.blit (self._imGameOver, (self.screenSize[0] / 2 - (self._imGameOver.get_width()/2), self.screenSize[1] / 2 - (self._imGameOver.get_height()/2)) )
        elif self.state == self.STATE_WAIT_START:
            self._pacman.graphics.blit (self._imReady, (self.screenSize[0] / 2 - 20, self.screenSize[1] / 2 + 12) )

        self.drawNumber (self._levelNum, (0, self.screenSize[1] - 20) )

    def drawNumber(self, number, position):
        (x, y) = position
        strNumber = str(int(number))

        for i in range(0, len(strNumber), 1):
            iDigit = int(strNumber[i])
            self._pacman.graphics.blit (self._digit[ iDigit ], (x + i * SCORE_COLWIDTH, y) )

    def smartMoveScreen(self):
        possibleScreenX = self._pacman.player.x - self.screenTileSize[1] / 2 * TILE_WIDTH
        possibleScreenY = self._pacman.player.y - self.screenTileSize[0] / 2 * TILE_HEIGHT

        if possibleScreenX < 0:
            possibleScreenX = 0
        elif possibleScreenX > self._pacman.level.lvlWidth * TILE_WIDTH - self.screenSize[0]:
            possibleScreenX = self._pacman.level.lvlWidth * TILE_HEIGHT - self.screenSize[0]

        if possibleScreenY < 0:
            possibleScreenY = 0
        elif possibleScreenY > self._pacman.level.lvlHeight * TILE_WIDTH - self.screenSize[1]:
            possibleScreenY = self._pacman.level.lvlHeight * TILE_HEIGHT - self.screenSize[1]

        self.moveScreen( (possibleScreenX, possibleScreenY) )

    def moveScreen(self, newPosition ):
        if self.state != self.STATE_GAME_OVER:
            factor = 0.1
            nfactor = 1 - factor
            (newX, newY) = (self.screenPixelPos[0] * nfactor + newPosition[0] * factor), (self.screenPixelPos[1] * nfactor + newPosition[1] * factor)
        else:
            (newX, newY) = newPosition
        self.screenPixelPos = (newX, newY)
        self.screenNearestTilePos = (int(newY / TILE_HEIGHT), int(newX / TILE_WIDTH)) # nearest-tile position of the screen from the UL corner
        self.screenPixelOffset = (newX - self.screenNearestTilePos[1]*TILE_WIDTH, newY - self.screenNearestTilePos[0]*TILE_HEIGHT)

    def getScreenPos(self):
        return self.screenPixelPos

    def getLevelNum(self):
        return self._levelNum

    def setNextLevel(self):
        self._levelNum += 1

        self.setState( self.STATE_WAIT_START )
        self._pacman.level.loadLevel( self._levelNum )

        self._pacman.player.stop()

    def setState(self, newState):
        self.state = newState
        self.stateTimer = 0
        # print " ***** GAME STATE IS NOW ***** " + str(newState)
