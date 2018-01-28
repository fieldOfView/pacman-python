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

        self._quad = Quad()
        self._fbo = None

        self.screenSize = (1280, 720)

    def initDisplay(self):
        (width, height) = self.screenSize
        pygame.display.set_mode( (width, height), pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.RESIZABLE | pygame.OPENGL )

        glLoadIdentity()
        gluPerspective(60, (width/height), 0.1, 100.0)
        gluLookAt(
            0, -40, 30,
            0, 0, 0,
            0, 1, 0
        )

    def resizeDisplay(self, size):
        self.screenSize = size
        (width, height) = size
        glViewport(0,0, width, height)

    def clear(self):
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)

    def blit(self, surface, position):
        glPushMatrix()
        (x,y) = (
            (position[0] / self._pacman.TILE_WIDTH) - (self._pacman.level.lvlWidth / 2.0) ,
            (position[1] / self._pacman.TILE_HEIGHT) - (self._pacman.level.lvlHeight / 2.0)
        )
        glTranslatef(2*x, 2*(1-y), 0.0)
        surface.bindTexture()
        self._quad.draw()
        surface.unbindTexture()
        glPopMatrix()

    def loadImage(self, dirname, filename):
        path = os.path.join(sys.path[0], "res", dirname, filename)
        surface = pygame.image.load(path).convert()
        return GameSurface((0,0),0,surface)

    def emptyImage(self):
        return GameSurface((self._pacman.TILE_WIDTH, self._pacman.TILE_HEIGHT), 0)

    def createBuffer(self, size):
        (width, height) = size

        self._fbo = Fbo((width * self._pacman.TILE_WIDTH, height * self._pacman.TILE_HEIGHT))
        self._fbo.bindBuffer()

        glClearColor(1,0,0,1)
        self.clear()
        glClearColor(0,0,0,1)

        # set up perspective
        glPushMatrix()

        gluPerspective(90, (width / height), height / 4, height)
        gluLookAt(
            0, 0, 1,
            0, 0, 0,
            0, 1, 0
        )

        return self._fbo

    def closeBuffer(self):
        self._fbo.unbindBuffer()
        glPopMatrix()

    def drawBuffer(self):
        glEnable(GL_TEXTURE_2D)
        self._fbo.bindTexture()
        (width, height) = (self._pacman.level.lvlWidth, self._pacman.level.lvlHeight)
        height = -height
        self._quad.draw((width, height))
        self._fbo.unbindTexture()

class Fbo():
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
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

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
            super().__init__(surface.get_size(), surface.get_flags())
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
        data = pygame.image.tostring(self, "RGBX")

        self._textureID = glGenTextures(1)

        self.bindTexture()

        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexImage2D(
            GL_TEXTURE_2D, 0, 3, size[0], size[1], 0,
            GL_RGBA, GL_UNSIGNED_BYTE, data
        )

        glEnable(GL_TEXTURE_2D)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
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
        (1,1),
        (1,0),
        (0,0),
        (0,1)
    )

    __edges = (
        (0,1),
        (0,3),
        (2,1),
        (2,3)
    )

    def __init__(self):
        pass

    def draw(self, size=(1,1)):
        glBegin(GL_QUADS)
        for edge in self.__edges:
            for vertex in edge:
                glTexCoord2fv(self.__uvs[vertex])
                v = self.__vertices[vertex]
                glVertex3fv((v[0] * size[0], v[1] * size[1], 0))
        glEnd()
