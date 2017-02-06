import numpy as np
import math

from util import orthon, project_along_axis
from primitive import Object2D, PlanarObject, Line


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
        odd amount of teeth.
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
        return EdgeReference(self, pos, length, projection_dir)

    def dereference(self):
        return self.target.dereference()
