#      ___________________
# ___/  base object class  \_______________________________________________

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
