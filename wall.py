import numpy as np
import math

from util import DIR, DIR2, orthon, min_vec, max_vec, project_along_axis, mirror_array_bool_to_factor
from units import Frac


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

class EDGE_ELEMENT_STYLE():
    REMOVE, \
    FLAT, \
    FLAT_EXTENDED = range(3)


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

# walls

class Edge(PlanarObject):
    def __init__(self, length, outward_dir, begin_style=EDGE_STYLE.FLAT, end_style=EDGE_STYLE.FLAT, flat=False):
        self.length = length
        self.outward_dir = outward_dir / np.linalg.norm(outward_dir)
        self.begin_style = begin_style
        self.end_style = end_style
        self.flat = flat

        self.counterpart = None

        self.sub_elements = []

    def render(self, config):

        start = np.array([0,0])

        # perpendicular to outward direction
        # abs works because this should be a unit vector or its negative
        direction = abs(orthon(self.outward_dir))

        displace = config.cutting_width / 2.
        wall_thickness = config.wall_thickness

        # check sub_elements list
        sub_elements = sorted(self.sub_elements, key=lambda x: x[0])

        # TODO cleanup this code

        part_positions = []
        for pos,length,_ in sub_elements:
            part_positions.append(pos)
            part_positions.append(pos+length)
        part_positions = [0] + part_positions + [self.length]
        # part_positions should be sorted
        assert( all(part_positions[i] <= part_positions[i+1] for i in range(len(part_positions)-1)) )

        # prepare part list
        if self.flat:
            if self.sub_elements:
                raise Exception("Not implemented")

            parts = [(0, self.length, 'flat')]

        else:
            parts = []
            parts.append( [0, None, self.begin_style] )
            for pos,length,style in sub_elements:
                if style == EDGE_ELEMENT_STYLE.REMOVE:
                    ps = EDGE_STYLE.INTERNAL_FLAT
                    ns = EDGE_STYLE.INTERNAL_FLAT
                elif style == EDGE_ELEMENT_STYLE.FLAT:
                    ps = EDGE_STYLE.TOOTHED
                    ns = EDGE_STYLE.TOOTHED
                elif style == EDGE_ELEMENT_STYLE.FLAT_EXTENDED:
                    ps = EDGE_STYLE.INTERNAL_FLAT
                    ns = EDGE_STYLE.INTERNAL_FLAT
                parts[-1][1] = pos - parts[-1][0]
                parts[-1][2] = (parts[-1][2], ps)
                parts.append( [pos, length, style] )
                parts.append( [pos + length, None, ns] )
            parts[-1][1] = self.length - parts[-1][0]
            parts[-1][2] = (parts[-1][2], self.end_style)

        # remove empty parts
        parts = [p for p in parts if p[1] != 0]

        return sum(
                (self._render_part(start, direction, self.outward_dir, displace, wall_thickness, config, *p) for p in parts),
                Object2D()
            )


    def _render_part(self, start, direction, outward_dir, displace, wall_thickness, config, pos, length, style):

        start = start + pos * direction

        if style == 'flat':
            return Object2D([Line(
                start - direction * displace + outward_dir * displace,
                start + direction * (length + displace) + outward_dir * displace
                )])

        elif style == EDGE_ELEMENT_STYLE.FLAT:
            return Object2D([Line(
                start + direction * displace + outward_dir * displace,
                start + direction * (length - displace) + outward_dir * displace
                )])

        elif style == EDGE_ELEMENT_STYLE.FLAT_EXTENDED:
            return Object2D([
                    Line(
                            start - direction * displace + outward_dir * displace,
                            start - direction * displace + outward_dir * (wall_thickness + displace)
                        ),
                    Line(
                            start - direction * displace + outward_dir * (wall_thickness + displace),
                            start + direction * (length + displace) + outward_dir * (wall_thickness + displace)
                        ),
                    Line(
                            start + direction * (length + displace) + outward_dir * (wall_thickness + displace),
                            start + direction * (length + displace) + outward_dir * displace
                        ),
                ])

        elif style == EDGE_ELEMENT_STYLE.REMOVE:
            return Object2D()

        else:

            begin_style, end_style = style

            if (begin_style in [EDGE_STYLE.TOOTHED, EDGE_STYLE.EXTENDED] and end_style in [EDGE_STYLE.FLAT, EDGE_STYLE.INTERNAL_FLAT]) or \
                (begin_style in [EDGE_STYLE.FLAT, EDGE_STYLE.INTERNAL_FLAT] and end_style in [EDGE_STYLE.TOOTHED, EDGE_STYLE.EXTENDED]):

                odd_tooth_count = False

            else:
                odd_tooth_count = True

            tooth_count = self._get_tooth_count(config, length, odd_tooth_count)
            tooth_length = length / tooth_count

            tooth_positions = [0] + list(np.cumsum([tooth_length for i in range(tooth_count)]))

            return self._render_toothed_line(
                    start,
                    begin_style,
                    end_style,
                    tooth_positions,
                    direction,
                    self.outward_dir,
                    wall_thickness,
                    displace
                )

    def add_element(self, pos, length, style, auto_add_counterpart=True):
        self.sub_elements.append((pos, length, style))

        if auto_add_counterpart and self.counterpart is not None:
            if style == EDGE_ELEMENT_STYLE.FLAT:
                self.counterpart.add_element(pos, length, EDGE_ELEMENT_STYLE.FLAT_EXTENDED, False)
            elif style == EDGE_ELEMENT_STYLE.FLAT_EXTENDED:
                self.counterpart.add_element(pos, length, EDGE_ELEMENT_STYLE.FLAT, False)



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

    def get_reference(self, pos=0, length=None, projection_dir=None):
        if length is not None:
            assert(pos + length <= self.length)
        return EdgeReference(self, pos, length, projection_dir)

    def dereference(self):
        return self


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


        lines = Object2D()

        # render first tooth
        start_pos, end_pos, extended = tooth_data[0]

        if begin_style == EDGE_STYLE.EXTENDED:
            lines.extend(CutoutEdge._render_rectangle(start, start_pos - wall_thickness, end_pos, direction, outward_dir, wall_thickness, displace))

        elif begin_style == EDGE_STYLE.TOOTHED:
            middle_teeth = tooth_data[0:-1]


        # render last tooth
        start_pos, end_pos, extended = tooth_data[-1]

        if end_style == EDGE_STYLE.EXTENDED:
            lines.extend(CutoutEdge._render_rectangle(start, start_pos, end_pos + wall_thickness, direction, outward_dir, wall_thickness, displace))

        elif end_style == EDGE_STYLE.TOOTHED:
            middle_teeth.append(tooth_data[-1])


        # render middle teeth
        for start_pos, end_pos, extended in middle_teeth:
            if extended:
                lines.extend(CutoutEdge._render_rectangle(start, start_pos, end_pos, direction, outward_dir, wall_thickness, displace))

        return lines

class EdgeReference():

    def __init__(self, target, pos=0, length=None, projection_dir=None):
        assert(pos >= 0)

        if length is None:
            length = target.length - pos
            assert(length >= 0)

        self.target = target
        self.position = pos
        self.length = length
        self.projection_dir = projection_dir

        # not sure if this is needed in an EdgeReference
        if target.counterpart is not None:
            # not sure about projection_dir
            self.counterpart = target.counterpart.get_reference(pos, length, projection_dir)
        else:
            self.counterpart = None

    def add_element(self, pos, length, style, auto_add_counterpart=True):
        self.target.add_element(self.position + pos, length, style, auto_add_counterpart)

    def to_local_coords(self, v):
        assert(self.projection_dir is not None)
        return project_along_axis(v, self.projection_dir)

    def get_reference(self, pos=0, length=None, projection_dir=None):
        if length is not None:
            assert(pos + length <= self.length)
        return EdgeReference(self, self.position + pos, length, projection_dir)

    def dereference(self):
        return self.target.dereference()


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
        return self.edges[self._get_edge_index_by_direction(v)]

    @staticmethod
    def _get_edge_index_by_direction(v):
        if (v == DIR2.UP).all():    return 0
        if (v == DIR2.DOWN).all():  return 1
        if (v == DIR2.LEFT).all():  return 2
        if (v == DIR2.RIGHT).all(): return 3

    def render(self, config):
        l = Object2D()

        # TODO implement render for edge references?
        l.extend(self.edges[0].dereference().render(config) + np.array([0, self.size[1]]))
        l.extend(self.edges[1].dereference().render(config) + np.array([0, 0]))
        l.extend(self.edges[2].dereference().render(config) + np.array([0, 0]))
        l.extend(self.edges[3].dereference().render(config) + np.array([self.size[0], 0]))

        for child, pos, mirror_axes in self.children:
            l.extend(child.render(config).mirror(mirror_axes) + pos)

        return l

    def add_child(self, child, pos, mirrored=np.array([False, False])):
        pos = Frac.array_total_length(pos, self.size)
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

        self._init_edges_from_target()

    def _init_edges_from_target(self):
        self.edges = [None] * 4

        if self.position[0] == 0:
            if self.target.get_edge_by_direction(DIR2.LEFT) is not None:
                self.edges[Wall._get_edge_index_by_direction(DIR2.LEFT)]  = self.target.get_edge_by_direction(DIR2.LEFT ).get_reference(self.position[1], self.size[1], projection_dir=DIR2.LEFT)
        if self.position[0] + self.size[0] == self.target.size[0]:
            if self.target.get_edge_by_direction(DIR2.RIGHT) is not None:
                self.edges[Wall._get_edge_index_by_direction(DIR2.RIGHT)] = self.target.get_edge_by_direction(DIR2.RIGHT).get_reference(self.position[1], self.size[1], projection_dir=DIR2.RIGHT)
        if self.position[1] == 0:
            if self.target.get_edge_by_direction(DIR2.DOWN) is not None:
                self.edges[Wall._get_edge_index_by_direction(DIR2.DOWN)]  = self.target.get_edge_by_direction(DIR2.DOWN ).get_reference(self.position[0], self.size[0], projection_dir=DIR2.DOWN)
        if self.position[1] + self.size[1] == self.target.size[1]:
            if self.target.get_edge_by_direction(DIR2.UP) is not None:
                self.edges[Wall._get_edge_index_by_direction(DIR2.UP)]    = self.target.get_edge_by_direction(DIR2.UP   ).get_reference(self.position[0], self.size[0], projection_dir=DIR2.UP)

    def get_edge_by_direction(self, v):
        if len(v) == 3 and self.projection_dir is not None:
            v = self.to_local_coords(v)
        return self.edges[Wall._get_edge_index_by_direction(v)]

    def to_local_coords(self, v):
        assert(self.projection_dir is not None)
        return project_along_axis(v, self.projection_dir)

    def add_child(self, child, pos, mirrored=np.array([False, False])):
        if len(pos) == 3 and self.projection_dir is not None:
            pos = self.to_local_coords(pos)
        pos = Frac.array_total_length(pos, self.size)
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
        self.edges.append(Edge(self.size[0], DIR.UP[:2],    flat=True).get_reference(projection_dir=DIR2.UP))
        self.edges.append(Edge(self.size[0], DIR.DOWN[:2],  EDGE_STYLE.FLAT,    EDGE_STYLE.FLAT).get_reference(projection_dir=DIR2.DOWN))
        self.edges.append(Edge(self.size[1], DIR.LEFT[:2],  EDGE_STYLE.FLAT,    EDGE_STYLE.TOOTHED).get_reference(projection_dir=DIR2.LEFT))
        self.edges.append(Edge(self.size[1], DIR.RIGHT[:2], EDGE_STYLE.TOOTHED, EDGE_STYLE.FLAT).get_reference(projection_dir=DIR2.RIGHT))

class ExtendedWall(Wall):
    def _construct_edges(self):
        self.edges = []
        self.edges.append(Edge(self.size[0], DIR.UP[:2],    EDGE_STYLE.EXTENDED, EDGE_STYLE.EXTENDED).get_reference(projection_dir=DIR2.UP))
        self.edges.append(Edge(self.size[0], DIR.DOWN[:2],  EDGE_STYLE.EXTENDED, EDGE_STYLE.EXTENDED).get_reference(projection_dir=DIR2.DOWN))
        self.edges.append(Edge(self.size[1], DIR.LEFT[:2],  EDGE_STYLE.EXTENDED, EDGE_STYLE.EXTENDED).get_reference(projection_dir=DIR2.LEFT))
        self.edges.append(Edge(self.size[1], DIR.RIGHT[:2], EDGE_STYLE.EXTENDED, EDGE_STYLE.EXTENDED).get_reference(projection_dir=DIR2.RIGHT))

class SideWall(Wall):
    def _construct_edges(self):
        self.edges = []
        self.edges.append(Edge(self.size[0], DIR.UP[:2],    EDGE_STYLE.FLAT,    EDGE_STYLE.FLAT).get_reference(projection_dir=DIR2.UP))
        self.edges.append(Edge(self.size[0], DIR.DOWN[:2],  EDGE_STYLE.FLAT,    EDGE_STYLE.FLAT).get_reference(projection_dir=DIR2.DOWN))
        self.edges.append(Edge(self.size[1], DIR.LEFT[:2],  EDGE_STYLE.FLAT,    EDGE_STYLE.TOOTHED).get_reference(projection_dir=DIR2.LEFT))
        self.edges.append(Edge(self.size[1], DIR.RIGHT[:2], EDGE_STYLE.TOOTHED, EDGE_STYLE.FLAT).get_reference(projection_dir=DIR2.RIGHT))


class SubWall(Wall):
    def _construct_edges(self):
        self.edges = []
        self.edges.append(Edge(self.size[0], DIR.UP[:2],    EDGE_STYLE.FLAT, EDGE_STYLE.FLAT).get_reference(projection_dir=DIR2.UP))
        self.edges.append(Edge(self.size[0], DIR.DOWN[:2],  EDGE_STYLE.FLAT, EDGE_STYLE.FLAT).get_reference(projection_dir=DIR2.DOWN))
        self.edges.append(Edge(self.size[1], DIR.LEFT[:2],  EDGE_STYLE.FLAT, EDGE_STYLE.FLAT).get_reference(projection_dir=DIR2.LEFT))
        self.edges.append(Edge(self.size[1], DIR.RIGHT[:2], EDGE_STYLE.FLAT, EDGE_STYLE.FLAT).get_reference(projection_dir=DIR2.RIGHT))
