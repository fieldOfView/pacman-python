#      _____________________
# ___/  sound file manager  \_______________________________________________

import pygame, sys, os

TILE_WIDTH = TILE_HEIGHT=24

class Graphics():

    def __init__(self, pacman):
        self._pacman = pacman
        self._screen = pygame.display.get_surface()

        self._scale = 1
        self._offset = (0, 0)

    def initDisplay(self):
        self._gameSize = self._pacman.game.screenSize

        (width, height) = self._gameSize
        pygame.display.set_mode( (width * self._scale, height * self._scale), pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.RESIZABLE )

    def resizeDisplay(self, size):
        self._scale = min(size[0] / self._gameSize[0], size[1] / self._gameSize[1])
        self._offset = ((size[0] - self._gameSize[0] * self._scale) / 2, (size[1] - self._gameSize[1] * self._scale) / 2)
        pygame.display.set_mode( size, pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.RESIZABLE )

    def blit(self, surface, position):
        tmp = pygame.transform.scale(surface, (int(self._scale * surface.get_width()), int(self._scale * surface.get_height())))
        (x,y) = position
        self._screen.blit(tmp, (self._offset[0] + x * self._scale, self._offset[1] + y * self._scale))

    def loadImage(self, dirname, filename):
    	path = os.path.join(sys.path[0], "res", dirname, filename)
    	return pygame.image.load(path).convert()