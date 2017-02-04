import numpy as np
import math

from util import orthon
from primitive import Object2D, Line, Circle, ArcPath


# 2d objects

class PlanarObject():
    """
    Abstract base class for objects that render into an Object2D.
    """

    def render(self, config):
        """Render into an Object2D."""
        raise NotImplementedError('Abstract method')

class CutoutRect(PlanarObject):
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def render(self, config):

        displace = config.cutting_width / 2

        l = []

        l.append(Line(np.array([displace,              displace]),               np.array([self.width - displace, displace])))
        l.append(Line(np.array([self.width - displace, displace]),               np.array([self.width - displace, self.height - displace])))
        l.append(Line(np.array([self.width - displace, self.height - displace]), np.array([displace,              self.height - displace])))
        l.append(Line(np.array([displace,              self.height - displace]), np.array([displace,              displace])))

        return Object2D(l)

class CutoutRoundedRect(PlanarObject):
    def __init__(self, width, height, radius):
        assert(width >= 2*radius)
        assert(height >= 2*radius)

        self.width = width
        self.height = height
        self.radius = radius

    def render(self, config):

        displace = config.cutting_width / 2

        l = []

        l.append(Line(np.array([displace + self.radius, displace]), np.array([self.width - self.radius - displace, displace])))
        l.append(ArcPath(np.array([self.width - self.radius - displace, displace]), np.array([self.width - - displace, self.radius + displace]), self.radius, False, False))
        l.append(Line(np.array([self.width - displace, self.radius + displace]), np.array([self.width - displace, self.height - self.radius - displace])))
        l.append(ArcPath(np.array([self.width - displace, self.height - self.radius - displace]), np.array([self.width - self.radius - displace, self.height - displace]), self.radius, False, False))
        l.append(Line(np.array([self.width - self.radius - displace, self.height - displace]), np.array([self.radius + displace, self.height - displace])))
        l.append(ArcPath(np.array([self.radius + displace, self.height - displace]), np.array([displace, self.height - self.radius - displace]), self.radius, False, False))
        l.append(Line(np.array([displace, self.height - self.radius - displace]), np.array([displace, self.radius + displace])))
        l.append(ArcPath(np.array([displace, self.radius + displace]), np.array([displace + self.radius, displace]), self.radius, False, False))

        return Object2D(l)

class HexBoltCutout(PlanarObject):
    def __init__(self, width):
        self.width = width

    def render(self, config):
        displace = config.cutting_width / 2
        radius = 2 * self.width / math.sqrt(3)

        y_pos = self.width - displace
        x_pos = radius/2 - (displace / math.sqrt(3))

        hor_x_pos = radius - (2 * displace / math.sqrt(3))

        corners = [
                np.array([-x_pos,  y_pos]),
                np.array([ x_pos,  y_pos]),
                np.array([ hor_x_pos, 0]),
                np.array([ x_pos, -y_pos]),
                np.array([-x_pos, -y_pos]),
                np.array([-hor_x_pos, 0]),

                np.array([-x_pos,  y_pos]),
            ]
        return Object2D([Line(a,b) for a,b in zip(corners, corners[1:])])

class CircleCutout(PlanarObject):
    def __init__(self, radius):
        self.radius = radius

    def render(self, config):
        displace = config.cutting_width / 2

        return Object2D([Circle(0, self.radius - displace)])

class MountingScrewCutout(PlanarObject):
    def __init__(self, radius_head, radius_shaft, shaft_length, shaft_dir):
        assert(radius_head >= radius_shaft)

        self.radius_head = radius_head
        self.radius_shaft = radius_shaft
        self.shaft_length = shaft_length
        self.shaft_dir = shaft_dir

    def render(self, config):
        displace = config.cutting_width / 2

        on = orthon(self.shaft_dir)
        rh = self.radius_head - displace
        rs = (self.radius_shaft - displace)

        shaft_straight_endpoint = (self.shaft_length - math.sqrt(rh*rh - rs*rs)) * self.shaft_dir

        l = []
        l.append(ArcPath(rs * (-on), rs * on, rs))
        l.append(Line(rs * on, rs * on + shaft_straight_endpoint))
        l.append(ArcPath(rs * on + shaft_straight_endpoint, rs * (-on) + shaft_straight_endpoint, rh))
        l.append(Line(rs * (-on) + shaft_straight_endpoint, rs * (-on)))

        return Object2D(l)

class Fan40mmCutout(PlanarObject):

    def render(self, config):
        displace = config.cutting_width / 2

        l = []
        l.append(Circle(0, 19 - displace))
        l.append(Circle(np.array([ 16.5,  16.5]), 2 - displace))
        l.append(Circle(np.array([-16.5,  16.5]), 2 - displace))
        l.append(Circle(np.array([ 16.5, -16.5]), 2 - displace))
        l.append(Circle(np.array([-16.5, -16.5]), 2 - displace))

        return Object2D(l)

class AirVentsCutout(PlanarObject):
    # TODO make more configurable
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def render(self, config):

        displace = config.cutting_width / 2

        short_count = int(math.ceil((self.width + 5) / (5+5)))
        short_length = (self.width + 5) / short_count

        long_count = int(math.ceil((self.height + 5) / (30+5)))
        long_length = (self.height + 5) / long_count

        short_positions = [(i*short_length, (i+1)*short_length-5) for i in range(short_count)]
        long_positions = [(i*long_length, (i+1)*long_length-5) for i in range(long_count)]

        l = []

        for x1, x2 in short_positions:
            for y1, y2 in long_positions:

                l.append(Line(np.array([x1 + displace, y1 + displace]), np.array([x2 - displace, y1 + displace])))
                l.append(Line(np.array([x2 - displace, y1 + displace]), np.array([x2 - displace, y2 - displace])))
                l.append(Line(np.array([x2 - displace, y2 - displace]), np.array([x1 + displace, y2 - displace])))
                l.append(Line(np.array([x1 + displace, y2 - displace]), np.array([x1 + displace, y1 + displace])))

        return Object2D(l)

    @staticmethod
    def _render_rectangle(pos, size):
        pass
