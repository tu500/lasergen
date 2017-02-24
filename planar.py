import numpy as np
import math

from util import DIR2
from primitive import Object2D, PlanarObject, Line, Circle, ArcPath
from edge import EDGE_STYLE, EDGE_ELEMENT_STYLE


class CutoutRect(PlanarObject):
    """
    A planar object rendering a rectangle.
    """

    data_to_local_coords = ['size', 'center_dir']

    def __init__(self, size, center=False, layer='cut'):
        super(CutoutRect, self).__init__(layer)

        self.size = np.array(size)
        self.center_dir = self._calc_center_dir(center)

    def render(self, config):

        displace = config.cutting_width / 2
        width, height = self.size

        l = []

        l.append(Line(np.array([displace,         displace]),          np.array([width - displace, displace])))
        l.append(Line(np.array([width - displace, displace]),          np.array([width - displace, height - displace])))
        l.append(Line(np.array([width - displace, height - displace]), np.array([displace,         height - displace])))
        l.append(Line(np.array([displace,         height - displace]), np.array([displace,         displace])))

        return Object2D(l, self.layer) - (self.center_dir * self.size / 2)

class CutoutRoundedRect(PlanarObject):
    """
    A planar object rendering a rectangle with rounded off corners.
    """

    data_to_local_coords = ['size', 'center_dir']

    def __init__(self, size, radius, center=False, layer='cut'):
        super(CutoutRoundedRect, self).__init__(layer)

        self.size = np.array(size)
        self.radius = radius
        self.center_dir = self._calc_center_dir(center)

    def render(self, config):

        displace = config.cutting_width / 2
        width, height = self.size
        radius = self.radius

        assert(width >= 2*radius)
        assert(height >= 2*radius)

        l = []

        l.append(ArcPath(np.array([width - radius, displace]), np.array([width - displace, radius]), radius - displace, False, False))
        l.append(Line(np.array([width - displace, radius]), np.array([width - displace, height - radius])))
        l.append(ArcPath(np.array([width - displace, height - radius]), np.array([width - radius, height - displace]), radius - displace, False, False))
        l.append(Line(np.array([width - radius, height - displace]), np.array([radius, height - displace])))
        l.append(ArcPath(np.array([radius, height - displace]), np.array([displace, height - radius]), radius - displace, False, False))
        l.append(Line(np.array([displace, height - radius]), np.array([displace, radius])))
        l.append(ArcPath(np.array([displace, radius]), np.array([radius, displace]), radius - displace, False, False))
        l.append(Line(np.array([radius, displace]), np.array([width - radius, displace])))

        return Object2D(l, self.layer) - (self.center_dir * self.size / 2)

class HexBoltCutout(PlanarObject):
    """
    A planar object rendering a hexagon.

    Useful for cutting out a hexbolt shape.
    """

    def __init__(self, width, layer='cut'):
        super(HexBoltCutout, self).__init__(layer)

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
        return Object2D([Line(a,b) for a,b in zip(corners, corners[1:])], self.layer)

class CircleCutout(PlanarObject):
    """
    A planar object rendering a circle.
    """

    def __init__(self, radius, layer='cut'):
        super(CircleCutout, self).__init__(layer)

        self.radius = radius

    def render(self, config):
        displace = config.cutting_width / 2

        return Object2D([Circle(0, self.radius - displace)], self.layer)

class MountingScrewCutout(PlanarObject):
    """
    A planar object rendering a cutout for a backside screw mounting hole.
    """

    data_to_local_coords = ['shaft_dir']

    def __init__(self, radius_head, radius_shaft, shaft_length, shaft_dir, layer='cut'):
        super(MountingScrewCutout, self).__init__(layer)

        assert(radius_head >= radius_shaft)

        self.radius_head = radius_head
        self.radius_shaft = radius_shaft
        self.shaft_length = shaft_length
        self.shaft_dir = np.array(shaft_dir)

    def render(self, config):
        displace = config.cutting_width / 2

        on = DIR2.orthon(self.shaft_dir)
        rh = self.radius_head - displace
        rs = (self.radius_shaft - displace)

        shaft_straight_endpoint = (self.shaft_length - math.sqrt(rh*rh - rs*rs)) * self.shaft_dir

        l = []
        l.append(ArcPath(rs * (-on), rs * on, rs))
        l.append(Line(rs * on, rs * on + shaft_straight_endpoint))
        l.append(ArcPath(rs * on + shaft_straight_endpoint, rs * (-on) + shaft_straight_endpoint, rh))
        l.append(Line(rs * (-on) + shaft_straight_endpoint, rs * (-on)))

        return Object2D(l, self.layer)

class FanCutout(PlanarObject):
    """
    A planar object rendering cutouts for a standard sized fan.

    Renders mounting holes for the screws and an appropriate sized air hole.
    """

    data_to_local_coords = ['center_dir']

    # TODO only 40mm size verified
    dimensions = {
            # (main diameter, mounting hole diameter, mounting hole displace)
            40:  ( 38, 4, 3.5),
            60:  ( 58, 4, 4.0),
            70:  ( 68, 4, 4.0),
            80:  ( 76, 4, 4.5),
            92:  ( 89, 4, 5.0),
            120: (117, 4, 7.0),
        }

    def __init__(self, size, center=True, layer='cut'):
        super(FanCutout, self).__init__(layer)

        assert(size in self.dimensions)
        self.size = size
        self.center_dir = self._calc_center_dir(center)

    def render(self, config):
        displace = config.cutting_width / 2

        main_dia, mounting_hole_dia, mounting_hole_displace = self.dimensions[self.size]

        main_radius = main_dia / 2
        mounting_hole_radius = mounting_hole_dia / 2
        mounting_position = self.size / 2 - mounting_hole_displace

        l = []
        l.append(Circle(0, main_radius - displace))
        l.append(Circle(np.array([ mounting_position,  mounting_position]), mounting_hole_radius - displace))
        l.append(Circle(np.array([-mounting_position,  mounting_position]), mounting_hole_radius - displace))
        l.append(Circle(np.array([ mounting_position, -mounting_position]), mounting_hole_radius - displace))
        l.append(Circle(np.array([-mounting_position, -mounting_position]), mounting_hole_radius - displace))

        return Object2D(l, self.layer) - ((1-self.center_dir) * self.size / 2)

class AirVentsCutout(PlanarObject):
    """
    A planar object rendering a gutter of rectangular air vents.
    """

    data_to_local_coords = ['size', 'center_dir', 'hole_target_size']

    def __init__(self, size, hole_target_size=(5,30), hole_distance=5, center=False, layer='cut'):
        super(AirVentsCutout, self).__init__(layer)

        self.size = np.array(size)
        self.center_dir = self._calc_center_dir(center)
        self.hole_target_size = np.array(hole_target_size)
        self.hole_distance = hole_distance

    def render(self, config):

        displace = config.cutting_width / 2
        width, height = self.size
        h_dist = self.hole_distance
        ht_width, ht_height = self.hole_target_size

        x_count = int(math.ceil((width + h_dist) / (ht_width + h_dist)))
        x_length = (width + h_dist) / x_count

        y_count = int(math.ceil((height + h_dist) / (ht_height + h_dist)))
        y_length = (height + h_dist) / y_count

        x_positions = [(i * x_length, (i+1) * x_length - h_dist) for i in range(x_count)]
        y_positions = [(i * y_length, (i+1) * y_length - h_dist) for i in range(y_count)]

        l = []

        for x1, x2 in x_positions:
            for y1, y2 in y_positions:

                l.append(Line(np.array([x1 + displace, y1 + displace]), np.array([x2 - displace, y1 + displace])))
                l.append(Line(np.array([x2 - displace, y1 + displace]), np.array([x2 - displace, y2 - displace])))
                l.append(Line(np.array([x2 - displace, y2 - displace]), np.array([x1 + displace, y2 - displace])))
                l.append(Line(np.array([x1 + displace, y2 - displace]), np.array([x1 + displace, y1 + displace])))

        return Object2D(l, self.layer) - (self.center_dir * self.size / 2)


class RectEdgeCutout(PlanarObject):
    """
    A planar object rendering a rectangular cutout from a wall's edge.
    """

    data_to_local_coords = ['size', 'edge_dir']

    def __init__(self, size, edge_dir, center=False, layer='cut'):
        super(RectEdgeCutout, self).__init__(layer)

        self.size = np.array(size)
        self.edge_dir = np.array(edge_dir)
        self.center = center

    def init_parent(self):

        edge_dir = self.edge_dir
        n_dir = abs(DIR2.orthon(edge_dir))
        width = DIR2.project_along_axis(self.size, edge_dir)

        if self.center:
            self.start = n_dir * (-width/2)
        else:
            self.start = np.array([0,0])

        e = self.parent.get_edge_by_direction(self.edge_dir)
        e.add_element(
                self.start + self.position,
                self.size,
                EDGE_ELEMENT_STYLE.REMOVE,
                EDGE_STYLE.INTERNAL_FLAT,
                EDGE_STYLE.INTERNAL_FLAT,
            )

    def render(self, config):

        edge_dir = self.edge_dir
        n_dir = abs(DIR2.orthon(edge_dir))

        displace = config.cutting_width / 2
        width = DIR2.project_along_axis(self.size, edge_dir)
        height = DIR2.project_along_axis(self.size, n_dir)
        start = self.start

        l = []

        l.append(Line(start + edge_dir * displace + n_dir * displace, start + edge_dir * (-height + displace) + n_dir * displace))
        l.append(Line(start + edge_dir * (-height + displace) + n_dir * displace, start + edge_dir * (-height + displace) + n_dir * (width - displace)))
        l.append(Line(start + edge_dir * (-height + displace) + n_dir * (width - displace), start + edge_dir * displace + n_dir * (width - displace)))

        return Object2D(l, self.layer)

class RoundedRectEdgeCutout(PlanarObject):
    """
    A planar object rendering a rounded rectangular cutout from a wall's edge.
    """

    data_to_local_coords = ['size', 'edge_dir']

    def __init__(self, size, radius, edge_dir, center=False, layer='cut'):
        super(RoundedRectEdgeCutout, self).__init__(layer)

        self.size = np.array(size)
        self.radius = radius
        self.edge_dir = np.array(edge_dir)
        self.center = center

    def init_parent(self):

        edge_dir = self.edge_dir
        n_dir = abs(DIR2.orthon(edge_dir))
        width = DIR2.project_along_axis(self.size, edge_dir)

        if self.center:
            self.start = n_dir * (-width/2)
        else:
            self.start = np.array([0,0])

        e = self.parent.get_edge_by_direction(self.edge_dir)
        e.add_element(
                self.start + self.position,
                self.size,
                EDGE_ELEMENT_STYLE.REMOVE,
                EDGE_STYLE.INTERNAL_FLAT,
                EDGE_STYLE.INTERNAL_FLAT,
            )

    def render(self, config):

        edge_dir = self.edge_dir
        n_dir = abs(DIR2.orthon(edge_dir))

        displace = config.cutting_width / 2
        width = DIR2.project_along_axis(self.size, edge_dir)
        height = DIR2.project_along_axis(self.size, n_dir)
        radius = self.radius
        start = self.start

        assert(width >= 2*radius)
        assert(height >= radius)

        l = []

        l.append(Line(start + edge_dir * displace + n_dir * displace, start + edge_dir * (-height + radius) + n_dir * displace))
        l.append(ArcPath(start + edge_dir * (-height + radius) + n_dir * displace, start + edge_dir * (-height + displace) + n_dir * radius, radius - displace, False, False))
        l.append(Line(start + edge_dir * (-height + displace) + n_dir * radius, start + edge_dir * (-height + displace) + n_dir * (width - radius)))
        l.append(ArcPath(start + edge_dir * (-height + displace) + n_dir * (width - radius), start + edge_dir * (-height + radius) + n_dir * (width - displace), radius - displace, False, False))
        l.append(Line(start + edge_dir * (-height + radius) + n_dir * (width - displace), start + edge_dir * displace + n_dir * (width - displace)))

        return Object2D(l, self.layer)
