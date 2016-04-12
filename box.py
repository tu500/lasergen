from wall import ToplessWall, ExtendedWall, SideWall
from util import DIR

class Box():
    def __init__(self, width, height, depth):
        self.width = width
        self.height = height
        self.depth = depth

        self._construct_walls()

    def render(self, config):
        return [w.render(config) for w in self.walls if w is not None]

    def get_wall_by_direction(self, v):
        if (v == DIR.UP).all():    return self.walls[0]
        if (v == DIR.DOWN).all():  return self.walls[1]
        if (v == DIR.LEFT).all():  return self.walls[2]
        if (v == DIR.RIGHT).all(): return self.walls[3]
        if (v == DIR.FRONT).all(): return self.walls[4]
        if (v == DIR.BACK).all():  return self.walls[5]

    def _construct_walls(self):
        raise Exception("Abstract method")

class ToplessBox(Box):
    def _construct_walls(self):
        self.walls = []
        self.walls.append(SideWall(self.width, self.depth))
        self.walls.append(SideWall(self.height, self.depth))
        self.walls.append(SideWall(self.width, self.depth))
        self.walls.append(SideWall(self.height, self.depth))
        self.walls.append(ExtendedWall(self.width, self.height))
        self.walls.append(ExtendedWall(self.width, self.height))

class ClosedBox(Box):
    def _construct_walls(self):
        self.walls = []
        self.walls.append(ToplessWall(self.width, self.depth))
        self.walls.append(ToplessWall(self.height, self.depth))
        self.walls.append(ToplessWall(self.width, self.depth))
        self.walls.append(ToplessWall(self.height, self.depth))
        self.walls.append(None)
        self.walls.append(ExtendedWall(self.width, self.height))
