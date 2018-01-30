#      ___________________
# ___/  graphics manager  \_______________________________________________

import pygame, sys, os
from OpenGL.GL import *
from OpenGL.GLU import *

from OpenGL.GL.ARB.framebuffer_object import *
from OpenGL.GL.EXT.framebuffer_object import *

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

        self.screenSize = (1280, 720)

    def initDisplay(self):
        (width, height) = self.screenSize
        pygame.display.set_mode( (width, height), pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.RESIZABLE | pygame.OPENGL )

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60, (width/height), 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(
            2, -35, 25,
            0, 0, -10,
            0, 1, 0
        )

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self._quad = Quad()

    def resizeDisplay(self, size):
        self.screenSize = size
        (width, height) = size
        glViewport(0,0, width, height)

    def clear(self):
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)

    def beginAnaglyph(self, left = True):
        proj = glGetFloatv( GL_PROJECTION_MATRIX)
        if left:
            # cyan
            #glTranslate(-2.0, 0., 0.)
            proj[2][0] = -.05
            proj[3][0] = -2.0
            glColorMask(GL_FALSE,GL_TRUE,GL_TRUE,GL_TRUE)
        else:
            # red
            #glTranslate(2.0, 0., 0.)
            proj[2][0] = .05
            proj[3][0] = 2.0
            glColorMask(GL_TRUE,GL_FALSE,GL_FALSE,GL_TRUE)

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadMatrixf(proj)
        glMatrixMode(GL_MODELVIEW)

    def endAnaglyph(self):
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glColorMask(GL_TRUE,GL_TRUE,GL_TRUE,GL_TRUE)

    def beginRenderBatch(self):
        self._batch = []
        self._collectingBatch = True

    def addToRenderBatch(self, data):
        self._batch.append(data)

    def drawRenderBatch(self):
        self._collectingBatch = False
        for data in self._batch:
            self.drawMultiple(data)

    def draw(self, surface, position):
        self.drawMultiple({surface: [position]})

    def drawMultiple(self, data):
        if self._collectingBatch:
            self.addToRenderBatch(data)
            return

        for surface in data:
            surface.bindTexture()
            for position in data[surface]:
                glPushMatrix()
                (x,y) = (
                    (position[0] / self._pacman.TILE_WIDTH) + self._draw_offset[0] ,
                    (position[1] / self._pacman.TILE_HEIGHT) + self._draw_offset[1]
                )
                glTranslatef(2 * x, 2 * (1 - y), 0.0)
                size = surface.get_size()
                if size != (self._pacman.TILE_WIDTH, self._pacman.TILE_HEIGHT):
                    (width, height) = (size[0] / self._pacman.TILE_WIDTH, size[1] / self._pacman.TILE_HEIGHT)
                    glScalef(width, height, 1)
                self._quad.draw()
                glPopMatrix()
            surface.unbindTexture()

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
