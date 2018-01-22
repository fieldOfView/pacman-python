#      ___________________
# ___/  graphics manager  \_______________________________________________

import pygame, sys, os
from OpenGL.GL import *
from OpenGL.GLU import *

screenTileSize = (32, 24)

class Graphics():

    def __init__(self, pacman):
        self._pacman = pacman
        self._screen = pygame.display.get_surface()

        self._quad = Quad()

        self.screenSize = (screenTileSize[0] * self._pacman.TILE_WIDTH, screenTileSize[1] * self._pacman.TILE_HEIGHT)

    def initDisplay(self):
        (width, height) = self.screenSize
        pygame.display.set_mode( (width, height), pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.RESIZABLE | pygame.OPENGL )

    def resizeDisplay(self, size):
        self.screenSize = size
        (width, height) = size
        pygame.display.set_mode( size, pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.RESIZABLE | pygame.OPENGL )

        gluPerspective(45, (width/height), 0.1, 100.0)
        glTranslatef(0.0,0.0, -50)
        glRotatef(-45, 1, 0, 0)

    def clear(self):
        #self._screen.fill((0,0,0))
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        pass

    def blit(self, surface, position):
        (x,y) = (
            (position[0] / self._pacman.TILE_WIDTH) - (self._pacman.level.lvlWidth / 2.0) ,
            (position[1] / self._pacman.TILE_HEIGHT) - (self._pacman.level.lvlHeight / 2.0)
        )
        glTranslatef(2*x, 2*(1-y), 0.0)
        surface.bindTexture()
        self._quad.draw()
        surface.unbindTexture()
        glTranslatef(-2*x, -2*(1-y), 0.0)

    def loadImage(self, dirname, filename):
        path = os.path.join(sys.path[0], "res", dirname, filename)
        surface = pygame.image.load(path).convert()
        return GameSurface((0,0),0,surface)

    def emptyImage(self):
        return GameSurface((self._pacman.TILE_WIDTH, self._pacman.TILE_HEIGHT), 0)


class GameSurface(pygame.Surface):
    def __init__(self, size, flags=0, surface=None):
        if surface:
            super().__init__(surface.get_size(), surface.get_flags())
            self.blit(surface, (0,0))
        else:
            super().__init__(size, flags)

        self._textureID = 0
        self.updateTexture()

    #def __del__(self):
    #    if self._textureID:
    #        glDeleteTextures(self._textureID)

    def updateTexture(self):
        size = self.get_size()
        data = pygame.image.tostring(self, "RGBX")

        self._textureID = glGenTextures(1)

        glBindTexture(GL_TEXTURE_2D, self._textureID)

        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexImage2D(
            GL_TEXTURE_2D, 0, 3, size[0], size[1], 0,
            GL_RGBA, GL_UNSIGNED_BYTE, data
        )

        glEnable(GL_TEXTURE_2D)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)

        glBindTexture(GL_TEXTURE_2D, 0)

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

    def draw(self):
        glBegin(GL_QUADS)
        for edge in self.__edges:
            for vertex in edge:
                glTexCoord2fv(self.__uvs[vertex])
                glVertex3fv(self.__vertices[vertex])
        glEnd()
