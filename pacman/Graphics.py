#      ___________________
# ___/  graphics manager  \_______________________________________________

import pygame, sys, os, math
from OpenGL.GL import *
from OpenGL.GLU import *

from OpenGL.GL.ARB.framebuffer_object import *
from OpenGL.GL.EXT.framebuffer_object import *

NUMERIC_COLWIDTH = 13 # width of each character

ANAGLYPH_FOCUS = 2
ANAGLYPH_IOD = 0.05

class Graphics():

    def __init__(self, pacman):
        self._pacman = pacman
        self._screen = pygame.display.get_surface()

        self._draw_offset = (0, 0)
        self._quad = None
        self._fbo = None
        self._fbo_position = (0, 0)

        self._batch = []
        self._collectingBatch = False

        self._billboardDisplayList = None

        self.screenSize = (1280, 720)

        self._view_x = 0
        self._view_y = 0
        self._focus_factor = 1

        # numerical display digits
        self._digit = {}


    def initDisplay(self):
        (width, height) = self.screenSize
        flags = pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.RESIZABLE | pygame.OPENGL
        try:
            if os.uname().machine == "armv7l":
                flags |= pygame.FULLSCREEN
                pygame.mouse.set_visible(False)
        except:
            pass
        pygame.display.set_mode( (width, height), flags )

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60, (width/height), 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self._quad = Quad()

        self._billboardDisplayList = DisplayList()
        self._billboardDisplayList.begin()
        glRotatef(60, 1, 0, 0)
        glTranslatef(0, 0.5, 0)
        self._billboardDisplayList.end()

        # numerical display digits
        for i in range(0, 10, 1):
            self._digit[i] = self.loadImage("text",str(i) + ".gif")


    def setView(self):
        x = ((self._pacman.player.x / self._pacman.TILE_WIDTH) - (self._pacman.level.lvlWidth / 2)) / 2
        self._view_x = self._view_x + 0.1 * (x - self._view_x)
        y = ((self._pacman.player.y / self._pacman.TILE_HEIGHT) - (self._pacman.level.lvlHeight / 2)) / 3
        self._view_y = self._view_y + 0.1 * (y - self._view_y)
        glLoadIdentity()
        gluLookAt(
            self._view_x, -45, 12 - self._view_y,
            0, 0, -5,
            0, 1, 0
        )

    def resizeDisplay(self, size):
        self.screenSize = size
        (width, height) = size
        glViewport(0,0, width, height)

    def clear(self):
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)

    def beginAnaglyph(self, left = True):
        focus_factor = 1 + ((self._pacman.level.lvlHeight / 2) - (self._pacman.player.y / self._pacman.TILE_HEIGHT)) / self._pacman.level.lvlHeight
        self._focus_factor = self._focus_factor + 0.1 * (focus_factor - self._focus_factor)

        proj = glGetFloatv( GL_PROJECTION_MATRIX)
        if left:
            # cyan
            proj[2][0] = -ANAGLYPH_IOD
            proj[3][0] = -ANAGLYPH_FOCUS * self._focus_factor
            glColorMask(GL_TRUE,GL_FALSE,GL_FALSE,GL_TRUE)
        else:
            # red
            proj[2][0] = ANAGLYPH_IOD
            proj[3][0] = ANAGLYPH_FOCUS * self._focus_factor
            glColorMask(GL_FALSE,GL_TRUE,GL_TRUE,GL_TRUE)

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadMatrixf(proj)
        glMatrixMode(GL_MODELVIEW)

    def endAnaglyph(self):
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glColorMask(GL_TRUE,GL_TRUE,GL_TRUE,GL_TRUE)
        proj = glGetFloatv( GL_PROJECTION_MATRIX)
        proj[2][0] = 0
        proj[3][0] = 0

    def beginRenderBatch(self):
        self._batch = []
        self._collectingBatch = True

    def addToRenderBatch(self, data):
        self._batch.append(data)

    def drawRenderBatch(self):
        self._collectingBatch = False
        for data in self._batch:
            self.drawMultiple(data)

    def draw(self, surface, position, billboard = False, immediate = False):
        self.drawMultiple({surface: [(position, billboard)]}, immediate)

    def drawMultiple(self, data, immediate = False):
        if self._collectingBatch and not immediate:
            self.addToRenderBatch(data)
            return

        for item in data:
            if type(item) == DisplayList:
                item.execute()
                return

            surface = item
            surface.bindTexture()
            for (position, billboard) in data[surface]:
                glPushMatrix()

                glTranslatef(
                    2 * ((position[0] / self._pacman.TILE_WIDTH) + self._draw_offset[0]) ,
                    2 * (1 - ((position[1] / self._pacman.TILE_HEIGHT) + self._draw_offset[1])),
                    position[2] / self._pacman.TILE_HEIGHT if len(position) > 2 else 0
                )

                size = surface.get_size()
                if size != (self._pacman.TILE_WIDTH, self._pacman.TILE_HEIGHT):
                    glScalef(size[0] / self._pacman.TILE_WIDTH, size[1] / self._pacman.TILE_HEIGHT, 1)

                if billboard:
                    self._billboardDisplayList.execute()

                self._quad.draw()
                glPopMatrix()
            surface.unbindTexture()

    def drawNumber(self, number, position, immediate = False):
        (x, y) = position
        strNumber = str(int(number))

        for i in range(0, len(strNumber), 1):
            iDigit = int(strNumber[i])
            self.draw (self._digit[ iDigit ], (x + i * NUMERIC_COLWIDTH, y), billboard = True, immediate = immediate)

    def loadImage(self, dirname, filename):
        path = os.path.join(sys.path[0], "res", dirname, filename)
        surface = pygame.image.load(path).convert_alpha()
        return self.createImage(surface)

    def createImage(self, surface):
        return GameSurface((0, 0), 0, surface)

    def createBuffer(self, size):
        (width, height) = size
        self._fbo_position = (
            (self._pacman.TILE_WIDTH * (width - 1) / 2.0),
            (self._pacman.TILE_HEIGHT * (height - 1) / 2.0)
        )

        self._draw_offset = (
            0.5 - (self._pacman.level.lvlWidth / 2.0),
            1.5 - (self._pacman.level.lvlHeight / 2.0)
        )

        self._fbo = FrameBuffer((width * self._pacman.TILE_WIDTH, height * self._pacman.TILE_HEIGHT))
        self._fbo.bindBuffer()

        self.clear()

        # set up perspective
        glPushMatrix()
        glLoadIdentity()
        gluLookAt(
            0, 0, height,
            0, 0, 0,
            0, 1, 0
        )
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluPerspective(90, (width/height), 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

    def closeBuffer(self):
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        self._fbo.unbindBuffer()

    def drawBuffer(self):
        self.draw(self._fbo, self._fbo_position)

    def createList(self):
        return DisplayList()


class FrameBuffer():
    def __init__(self, size):
        self._size = size
        (width, height) = size
        self._bufferID = None
        self._textureID = glGenTextures(1)

        glBindTexture( GL_TEXTURE_2D, self._textureID )
        glTexEnvf( GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE )
        glTexParameterf( GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameterf( GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT )
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)

        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGBA, GL_UNSIGNED_INT, None)
        glEnable(GL_TEXTURE_2D)

        self._bufferID = glGenFramebuffers(1)

    def __del__(self):
        if self._bufferID is not None:
            try:
                glDeleteFramebuffers(1, self._bufferID)
            except:
                pass
            self._bufferID = None
        if self._textureID is not None:
            try:
                glDeleteTextures(self._textureID)
            except:
                pass
            self._textureID = None

    def get_size(self):
        return self._size

    def bindBuffer(self):
        glPushAttrib(GL_VIEWPORT_BIT)
        glViewport(0,0,self._size[0], self._size[1])
        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, self._bufferID);

        # render to the texture
        glFramebufferTexture2DEXT(GL_FRAMEBUFFER_EXT, GL_COLOR_ATTACHMENT0_EXT, GL_TEXTURE_2D, self._textureID, 0)

    def unbindBuffer(self):
        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, 0)
        glPopAttrib()

    def bindTexture(self):
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self._textureID)

    def unbindTexture(self):
        glBindTexture(GL_TEXTURE_2D, 0)

    def getSize(self):
        return self._size


class GameSurface(pygame.Surface):
    def __init__(self, size, flags=0, surface=None):
        if surface:
            super().__init__(surface.get_size(), surface.get_flags(), depth=32)
            self.blit(surface, (0,0))
        else:
            super().__init__(size, flags)

        self._textureID = None
        self.updateTexture()

    def __del__(self):
        if self._textureID is not None:
            try:
                glDeleteTextures(self._textureID)
            except:
                pass

    def updateTexture(self):
        if self._textureID:
            glDeleteTextures(self._textureID)

        size = self.get_size()
        data = pygame.image.tostring(self, "RGBA", True) # flipped = True

        self._textureID = glGenTextures(1)

        self.bindTexture()

        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RGBA, size[0], size[1], 0,
            GL_RGBA, GL_UNSIGNED_BYTE, data
        )

        glEnable(GL_TEXTURE_2D)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)

        self.unbindTexture()

    def bindTexture(self):
        glBindTexture(GL_TEXTURE_2D, self._textureID)

    def unbindTexture(self):
        glBindTexture(GL_TEXTURE_2D, 0)


class Quad():
    __vertices = (
        (1, -1, 0),
        (1, 1, 0),
        (-1, 1, 0),
        (-1, -1, 0)
    )

    __uvs = (
        (1,0),
        (1,1),
        (0,1),
        (0,0)
    )

    def __init__(self):
        self._list = DisplayList()
        self._list.begin()

        glBegin(GL_QUADS)
        for vertex in range(0, len(self.__vertices)):
            glTexCoord2fv(self.__uvs[vertex])
            glVertex3fv(self.__vertices[vertex])
        glEnd()

        self._list.end()

    def draw(self):
        self._list.execute()


class DisplayList():
    def __init__(self):
        self._listID = glGenLists(1)

    def __del__(self):
        if self._listID is not None:
            try:
                glDeleteLists(self._listID)
            except:
                pass
            self._listID = None

    def __del__(self):
        pass

    def begin(self):
        glNewList(self._listID, GL_COMPILE)

    def end(self):
        glEndList()

    def execute(self):
        glCallList(self._listID)
