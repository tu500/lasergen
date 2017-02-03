import numpy as np
import math

from util import DIR, orthon, min_vec, max_vec, project_along_axis, mirror_array_bool_to_factor


# Edge Styles:
#
#    ╲                                ╲
#     ╲                                ╲
#      ╲                                ╲
#       ╔════════════╗                   ╲    ╔════════╗
#       ║╲           ║                    ╲   ║        ║
#       ║ ╲          ║                     ╲  ║        ║
#       ║  ╲         ║                      ╲ ║        ║
#       ║   ╲        ║                       ╲║        ║
#       ║    ╲-------╚═══════════┄┄┄┄┄        ║--------╚═══════════┄┄┄┄┄
#       ║    |╲                               ║╲
#       ║    | ╲                              ║ ╲
#       ║    |  ╲      EXTENDED               ║  ╲      TOOTHED
#       ║    |   ╲                            ║   ╲
#       ╚════╗    ╲                           ║    ╲
#            ║     ╲                          ║     ╲
#            ║      ╲                         ║      ╲
#            ║       ╲                        ║       ╲
#            ║        ╲                       ║        ╲
#            ┆         ╲                      ┆         ╲
#            ┆                                ┆
#            ┆  EXTENDED                      ┆  FLAT

class EDGE_STYLE():
    TOOTHED, \
    EXTENDED, \
    FLAT, \
    INTERNAL_FLAT = range(4)


# 2d primitives

class Object2D():
    """
    Helper class to group several 2D primitives toghether into a 2D object.
    """

    def __init__(self, primitives=None):
        if primitives is None:
            self.primitives = []
        else:
            self.primitives = primitives

    def bounding_box(self):
        """
        Calculate an axis aligned bounding box containing all primitives.
        Return value is (min_corner, max_corner).
        """

        if not self.primitives:
            raise Exception("PANIC!!!!")

        p = self.primitives[0]
        if isinstance(p, Line):
            vmin = p.start
            vmax = p.start
        elif isinstance(p, Circle):
            vmin = p.center
            vmax = p.center

        for p in self.primitives:
            if isinstance(p, Line):
                vmin = min_vec(vmin, p.start, p.end)
                vmax = max_vec(vmax, p.start, p.end)
            elif isinstance(p, Circle):
                vmin = min_vec(vmin, p.center - np.array([p.radius, p.radius]))
                vmax = max_vec(vmax, p.center + np.array([p.radius, p.radius]))
            elif isinstance(p, ArcPath):
                # TODO: this is only a (bad) heuristic
                vmin = min_vec(vmin, p.start - 2*np.array([p.radius, p.radius]), p.end - 2*np.array([p.radius, p.radius]))
                vmax = max_vec(vmax, p.start + 2*np.array([p.radius, p.radius]), p.end + 2*np.array([p.radius, p.radius]))
            else:
                raise Exception("PANIC")

        return (vmin, vmax)

    def __add__(self, b):
        """
        If argument is an Object2D, create a new Object2D concatenating both's
        primitive list. Else perform element wise additionn.
        """
        if isinstance(b, Object2D):
            return Object2D(self.primitives + b.primitives)
        return Object2D([i + b for i in self.primitives])

    def __sub__(self, b):
        """
        Perform elementwise subtraction.
        """
        return Object2D([i - b for i in self.primitives])

    def extend(self, b):
        """
        Extend own primitive list with another Object2D's one.
        """
        self.primitives.extend(b.primitives)

    def mirror(self, mirror_axes):
        """
        Return a new Object2D created by mirroring all primitives in the
        'global' (meaning local to this Object2D, not its primitives) reference
        system along the specified axes.
        """
        return Object2D([p.mirror(mirror_axes) for p in self.primitives])


class Primitive2D():
    """
    Abstract base class for 2D primitives.
    """
    def __add__(self, b):
        """Translation."""
        raise NotImplementedError('Abstract method')
    def __sub__(self, b):
        """Translation."""
        raise NotImplementedError('Abstract method')
    def mirror(self, mirror_axes):
        raise NotImplementedError('Abstract method')

class Line(Primitive2D):
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def __add__(self, b):
        return Line(self.start + b, self.end + b)
    def __sub__(self, b):
        return Line(self.start - b, self.end - b)
    def mirror(self, mirror_axes):
        fac = mirror_array_bool_to_factor(mirror_axes)
        return Line(self.start * fac, self.end * fac)

class Circle(Primitive2D):
    def __init__(self, center, radius):
        self.center = center
        self.radius = radius

    def __add__(self, b):
        return Circle(self.center + b, self.radius)
    def __sub__(self, b):
        return Circle(self.center - b, self.radius)
    def mirror(self, mirror_axes):
        fac = mirror_array_bool_to_factor(mirror_axes)
        return Circle(self.center * fac, self.radius)

class ArcPath(Primitive2D):
    def __init__(self, start, end, radius, large_arc=True, sweep=True):
        self.start = start
        self.end = end
        self.radius = radius
        self.large_arc = large_arc
        self.sweep = sweep

    def __add__(self, b):
        return ArcPath(self.start + b, self.end + b, self.radius, self.large_arc, self.sweep)
    def __sub__(self, b):
        return ArcPath(self.start - b, self.end - b, self.radius, self.large_arc, self.sweep)
    def mirror(self, mirror_axes):
        # TODO
        return self

    @staticmethod
    def from_center_angle(center, angle_start, angle_end, radius):
        start = center + radius * np.array([math.cos(angle_start / 180 * math.pi), math.sin(angle_start / 180 * math.pi)])
        end = center + radius * np.array([math.cos(angle_end / 180 * math.pi), math.sin(angle_end / 180 * math.pi)])
        large_arc = angle_end - angle_start >= 180
        return ArcPath(start, end, radius, large_arc=large_arc)

class Text(Primitive2D):
    def __init__(self, positionn, text, fontsize=5):
        self.position = position
        self.text = text
        self.fontsize = fontsize

    def __add__(self, b):
        return Text(self.position + b, self.text, self.fontsize)
    def __sub__(self, b):
        return Text(self.position - b, self.text, self.fontsize)
    def mirror(self, mirror_axes):
        # TODO
        return self


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

# walls

class Edge(PlanarObject):
    def __init__(self, length, outward_dir, begin_style=EDGE_STYLE.FLAT, end_style=EDGE_STYLE.FLAT, flat=False):
        self.length = length
        self.outward_dir = outward_dir / np.linalg.norm(outward_dir)
        self.begin_style = begin_style
        self.end_style = end_style
        self.flat = flat

    def render(self, config):

        start = np.array([0,0])

        # perpendicular to outward direction
        # abs works because this should be a unit vector or its negative
        direction = abs(orthon(self.outward_dir))

        displace = config.cutting_width / 2.
        wall_thickness = config.wall_thickness


        if self.flat:
            return Object2D([Line(
                start - direction * displace + self.outward_dir * displace,
                start + direction * (self.length + displace) + self.outward_dir * displace
                )])


        if (self.begin_style in [EDGE_STYLE.TOOTHED, EDGE_STYLE.EXTENDED] and self.end_style == EDGE_STYLE.FLAT) or \
            (self.begin_style == EDGE_STYLE.FLAT and self.end_style in [EDGE_STYLE.TOOTHED, EDGE_STYLE.EXTENDED]):

            odd_tooth_count = False

        else:
            odd_tooth_count = True

        tooth_count = self._get_tooth_count(config, self.length, odd_tooth_count)
        tooth_length = self.length / tooth_count

        tooth_positions = [0] + list(np.cumsum([tooth_length for i in range(tooth_count)]))

        return self._render_toothed_line(
                start,
                self.begin_style,
                self.end_style,
                tooth_positions,
                direction,
                self.outward_dir,
                wall_thickness,
                displace
            )


    #TODO should this really be a static method?
    @staticmethod
    def _render_toothed_line(start, begin_style, end_style, tooth_positions, direction, outward_dir, wall_thickness, displace=0):
        """
        tooth_positions: list of starting points of tooths, including full edge length
                         i.e. [0, first_tooth_width, first_tooth_width + second_tooth_width, ..., full_edge_length]
        """

        if begin_style in [EDGE_STYLE.EXTENDED, EDGE_STYLE.TOOTHED]:
            extended_list = [True, False] * math.ceil(len(tooth_positions)/2)
        else:
            extended_list = [False, True] * math.ceil(len(tooth_positions)/2)

        tooth_data = list(zip(
                tooth_positions,
                tooth_positions[1:],
                extended_list
            ))

        assert(Edge._check_tooth_count(begin_style, end_style, len(tooth_data)))


        if len(tooth_data) == 1:
            #TODO only certain configurations allowed
            raise Exception("Not Implemented")

        middle_teeth = tooth_data[1:-1]


        lines = []

        # render first tooth
        start_pos, end_pos, extended = tooth_data[0]

        if begin_style == EDGE_STYLE.EXTENDED:
            lines.append(Line(
                start + direction * (start_pos - wall_thickness - displace) + outward_dir * (wall_thickness + displace),
                start + direction * (end_pos + displace) + outward_dir * (wall_thickness + displace)
                ))
            lines.append(Line(
                start + direction * (end_pos + displace) + outward_dir * (wall_thickness + displace),
                start + direction * (end_pos + displace) + outward_dir * displace
                ))

        elif begin_style == EDGE_STYLE.TOOTHED:
            middle_teeth = tooth_data[0:-1]

        elif begin_style == EDGE_STYLE.FLAT:
            lines.append(Line(
                start + direction * (start_pos - displace) + outward_dir * displace,
                start + direction * (end_pos - displace) + outward_dir * displace
                ))

        elif begin_style == EDGE_STYLE.INTERNAL_FLAT:
            middle_teeth = tooth_data[0:-1]


        # render last tooth
        start_pos, end_pos, extended = tooth_data[-1]
        last_lines = []

        if end_style == EDGE_STYLE.FLAT:
            last_lines.append(Line(
                start + direction * (start_pos + displace) + outward_dir * displace,
                start + direction * (end_pos + displace) + outward_dir * displace,
                ))

        elif end_style == EDGE_STYLE.EXTENDED:
            last_lines.append(Line(
                start + direction * (start_pos - displace) + outward_dir * displace,
                start + direction * (start_pos - displace) + outward_dir * (wall_thickness + displace),
                ))
            last_lines.append(Line(
                start + direction * (start_pos - displace) + outward_dir * (wall_thickness + displace),
                start + direction * (end_pos + wall_thickness + displace) + outward_dir * (wall_thickness + displace),
                ))

        elif end_style == EDGE_STYLE.TOOTHED:
            middle_teeth.append(tooth_data[-1])

        elif end_style == EDGE_STYLE.INTERNAL_FLAT:
            middle_teeth.append(tooth_data[-1])


        # render middle teeth
        for start_pos, end_pos, extended in middle_teeth:
            if extended:
                lines.append(Line(
                    start + direction * (start_pos - displace) + outward_dir * displace,
                    start + direction * (start_pos - displace) + outward_dir * (wall_thickness + displace)
                    ))
                lines.append(Line(
                    start + direction * (start_pos - displace) + outward_dir * (wall_thickness + displace),
                    start + direction * (end_pos + displace) + outward_dir * (wall_thickness + displace)
                    ))
                lines.append(Line(
                    start + direction * (end_pos + displace) + outward_dir * (wall_thickness + displace),
                    start + direction * (end_pos + displace) + outward_dir * displace
                    ))
            else:
                lines.append(Line(
                    start + direction * (start_pos + displace) + outward_dir * displace,
                    start + direction * (end_pos - displace) + outward_dir * displace
                    ))

        return Object2D(lines + last_lines)


    @staticmethod
    def _check_tooth_count(begin_style, end_style, tooth_count):
        """
        Check whether a specific tooth count matches given begin and end styles.
        """
        if tooth_count % 2 == 0:
            return  (begin_style in [EDGE_STYLE.EXTENDED, EDGE_STYLE.TOOTHED] and end_style in [EDGE_STYLE.FLAT, EDGE_STYLE.INTERNAL_FLAT]) or \
                    (end_style in [EDGE_STYLE.EXTENDED, EDGE_STYLE.TOOTHED] and begin_style in [EDGE_STYLE.FLAT, EDGE_STYLE.INTERNAL_FLAT])
        else:
            return  (begin_style in [EDGE_STYLE.EXTENDED, EDGE_STYLE.TOOTHED] and end_style in [EDGE_STYLE.EXTENDED, EDGE_STYLE.TOOTHED]) or \
                    (begin_style in [EDGE_STYLE.FLAT, EDGE_STYLE.INTERNAL_FLAT] and end_style in [EDGE_STYLE.FLAT, EDGE_STYLE.INTERNAL_FLAT])

    @staticmethod
    def _get_tooth_count(config, length, odd_tooth_count):
        """
        Calculate a matching number of teeth for the edge, given its length,
        configured tooth length bounds and whether there should be an even or
        odd amount of theeth.
        """
        # TODO add preferred tooth length

        min_tooth_count = math.ceil(length / config.tooth_max_width)
        max_tooth_count = math.floor(length / config.tooth_min_width)

        if min_tooth_count > max_tooth_count:
            raise Exception("PANIC!")

        if min_tooth_count == max_tooth_count:
            if (min_tooth_count % 2 == 0 and odd_tooth_count) or \
                (min_tooth_count % 2 == 1 and not odd_tooth_count):
                raise Exception("PANIC!!")

        # now take the middle
        avg = (min_tooth_count + max_tooth_count) / 2
        c = math.ceil(avg)

        if (c % 2 == 1 and odd_tooth_count) or (c % 2 == 0 and not odd_tooth_count):
            tooth_count = c
        else:
            #TODO does this always work?
            tooth_count = c - 1

        return tooth_count


class CutoutEdge(Edge):

    @staticmethod
    def _render_rectangle(start, start_pos, end_pos, direction, outward_dir, wall_thickness, displace):
        lines = []

        lines.append(Line(
            start + direction * (start_pos + displace) + outward_dir * displace,
            start + direction * (end_pos - displace) + outward_dir * displace
            ))
        lines.append(Line(
            start + direction * (end_pos - displace) + outward_dir * displace,
            start + direction * (end_pos - displace) + outward_dir * (wall_thickness - displace)
            ))
        lines.append(Line(
            start + direction * (end_pos - displace) + outward_dir * (wall_thickness - displace),
            start + direction * (start_pos + displace) + outward_dir * (wall_thickness - displace)
            ))
        lines.append(Line(
            start + direction * (start_pos + displace) + outward_dir * (wall_thickness - displace),
            start + direction * (start_pos + displace) + outward_dir * displace
            ))

        return Object2D(lines)


    @staticmethod
    def _render_toothed_line(start, begin_style, end_style, tooth_positions, direction, outward_dir, wall_thickness, displace=0):
        """
        tooth_positions: list of starting points of tooths, including full edge length
                         i.e. [0, first_tooth_width, first_tooth_width + second_tooth_width, ..., full_edge_length]
        """

        if begin_style in [EDGE_STYLE.EXTENDED, EDGE_STYLE.TOOTHED]:
            extended_list = [True, False] * math.ceil(len(tooth_positions)/2)
        else:
            extended_list = [False, True] * math.ceil(len(tooth_positions)/2)

        tooth_data = list(zip(
                tooth_positions,
                tooth_positions[1:],
                extended_list
            ))

        assert(Edge._check_tooth_count(begin_style, end_style, len(tooth_data)))


        if len(tooth_data) == 1:
            #TODO only certain configurations allowed
            raise Exception("Not Implemented")

        middle_teeth = tooth_data[1:-1]


        lines = []

        # render first tooth
        start_pos, end_pos, extended = tooth_data[0]

        if begin_style == EDGE_STYLE.EXTENDED:
            lines.extend(self._render_rectangle(start, start_pos - wall_thickness, end_pos, direction, outward_dir, wall_thickness, displace))

        elif begin_style == EDGE_STYLE.TOOTHED:
            middle_teeth = tooth_data[0:-1]


        # render last tooth
        start_pos, end_pos, extended = tooth_data[-1]
        last_lines = []

        if end_style == EDGE_STYLE.EXTENDED:
            lines.extend(self._render_rectangle(start, start_pos, end_pos + wall_thickness, direction, outward_dir, wall_thickness, displace))

        elif end_style == EDGE_STYLE.TOOTHED:
            middle_teeth.append(tooth_data[-1])


        # render middle teeth
        for start_pos, end_pos, extended in middle_teeth:
            if extended:
                lines.extend(self._render_rectangle(start, start_pos, end_pos, direction, outward_dir, wall_thickness, displace))

        return Object2D(lines + last_lines)


class Wall(PlanarObject):
    #size = None
    #children = None
    #edges = None

    def __init__(self, width, height):
        self.size = np.array([width, height])

        self.children = []

        self._construct_edges()

    def _construct_edges(self):
        raise NotImplementedError('Abstract method')

    def get_edge_by_direction(self, v):
        if (v[0:2] == DIR.UP).all():    return self.edges[0]
        if (v[0:2] == DIR.DOWN).all():  return self.edges[1]
        if (v[0:2] == DIR.LEFT).all():  return self.edges[2]
        if (v[0:2] == DIR.RIGHT).all(): return self.edges[3]

    def render(self, config):
        l = Object2D()

        l.extend(self.edges[0].render(config) + np.array([0, self.size[1]]))
        l.extend(self.edges[1].render(config) + np.array([0, 0]))
        l.extend(self.edges[2].render(config) + np.array([0, 0]))
        l.extend(self.edges[3].render(config) + np.array([self.size[0], 0]))

        for child, pos, mirror_axes in self.children:
            l.extend(child.render(config).mirror(mirror_axes) + pos)

        return l

    def add_child(self, child, pos, mirrored=np.array([False, False])):
        self.children.append((child, pos, mirrored))

    def get_reference(self, pos=np.array([0,0]), size=None, mirror_children=np.array([False, False]), projection_dir=None):
        if size is not None:
            assert( (pos + size <= self.size).all() )
        return WallReference(self, pos, size, mirror_children, projection_dir)

    def dereference(self):
        return self

class WallReference():

    def __init__(self, target, pos=np.array([0,0]), size=None, mirror_children=np.array([False, False]), projection_dir=None):
        assert( (pos >= np.array([0,0])).all() )

        if size is None:
            size = target.size - pos
            assert( (size >= np.array([0,0])).all() )

        self.target = target
        self.position = pos
        self.size = size
        self.mirror_children = mirror_children
        self.projection_dir = projection_dir

    def to_local_coords(self, v):
        assert(self.projection_dir is not None)
        return project_along_axis(v, self.projection_dir)

    def add_child(self, child, pos, mirrored=np.array([False, False])):
        if len(pos) == 3 and self.projection_dir is not None:
            pos = self.to_local_coords(pos)
        self.target.add_child(child, self.position + pos, self.mirror_children ^ mirrored)

    def get_reference(self, pos=np.array([0,0]), size=None, mirror_children=np.array([False, False]), projection_dir=None):
        if size is not None:
            assert( (pos + size <= self.size).all() )
        return WallReference(self, self.position + pos, size, self.mirror_children ^ mirror_children, projection_dir)

    def dereference(self):
        return self.target.dereference()


class ToplessWall(Wall):
    def _construct_edges(self):
        self.edges = []
        self.edges.append(Edge(self.size[0], DIR.UP[:2],    flat=True))
        self.edges.append(Edge(self.size[0], DIR.DOWN[:2],  EDGE_STYLE.FLAT,    EDGE_STYLE.FLAT))
        self.edges.append(Edge(self.size[1], DIR.LEFT[:2],  EDGE_STYLE.FLAT,    EDGE_STYLE.TOOTHED))
        self.edges.append(Edge(self.size[1], DIR.RIGHT[:2], EDGE_STYLE.TOOTHED, EDGE_STYLE.FLAT))

class ExtendedWall(Wall):
    def _construct_edges(self):
        self.edges = []
        self.edges.append(Edge(self.size[0], DIR.UP[:2],    EDGE_STYLE.EXTENDED, EDGE_STYLE.EXTENDED))
        self.edges.append(Edge(self.size[0], DIR.DOWN[:2],  EDGE_STYLE.EXTENDED, EDGE_STYLE.EXTENDED))
        self.edges.append(Edge(self.size[1], DIR.LEFT[:2],  EDGE_STYLE.EXTENDED, EDGE_STYLE.EXTENDED))
        self.edges.append(Edge(self.size[1], DIR.RIGHT[:2], EDGE_STYLE.EXTENDED, EDGE_STYLE.EXTENDED))

class SideWall(Wall):
    def _construct_edges(self):
        self.edges = []
        self.edges.append(Edge(self.size[0], DIR.UP[:2],    EDGE_STYLE.FLAT,    EDGE_STYLE.FLAT))
        self.edges.append(Edge(self.size[0], DIR.DOWN[:2],  EDGE_STYLE.FLAT,    EDGE_STYLE.FLAT))
        self.edges.append(Edge(self.size[1], DIR.LEFT[:2],  EDGE_STYLE.FLAT,    EDGE_STYLE.TOOTHED))
        self.edges.append(Edge(self.size[1], DIR.RIGHT[:2], EDGE_STYLE.TOOTHED, EDGE_STYLE.FLAT))


class SubWall(Wall):
    def _construct_edges(self):
        self.edges = []
        self.edges.append(Edge(self.size[0], DIR.UP[:2],    EDGE_STYLE.FLAT, EDGE_STYLE.FLAT))
        self.edges.append(Edge(self.size[0], DIR.DOWN[:2],  EDGE_STYLE.FLAT, EDGE_STYLE.FLAT))
        self.edges.append(Edge(self.size[1], DIR.LEFT[:2],  EDGE_STYLE.FLAT, EDGE_STYLE.FLAT))
        self.edges.append(Edge(self.size[1], DIR.RIGHT[:2], EDGE_STYLE.FLAT, EDGE_STYLE.FLAT))
