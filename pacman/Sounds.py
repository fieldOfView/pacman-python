#      _____________________
# ___/  sound file manager  \_______________________________________________

import pygame, sys, os

class Sounds():
    def __init__(self):
        # Must come before pygame.init()
        pygame.mixer.pre_init(22050, 16, 2, 512)
        pygame.mixer.init()

        self._sounds = {}

    def register(self, name, filename):
        path = os.path.join(sys.path[0], "res", "sounds", filename)
        self._sounds[name] = pygame.mixer.Sound(path)

    def play(self, name):
        if name in self._sounds:
            self._sounds[name].play()
        else:
            print("unknown sound: %s" % name)

    def stop(self):
        pygame.mixer.stop()