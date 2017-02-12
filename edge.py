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
    INTERNAL_FLAT, \
    INTERNAL_TOOTHED = range(5)

class EDGE_ELEMENT_STYLE():
    REMOVE, \
    FLAT, \
    FLAT_EXTENDED, \
    TOOTHED = range(4)


class _EdgeElement():
    """
    Internal. Mainly used for data storage.
    """

    allowed_neighbour_styles = {
            EDGE_ELEMENT_STYLE.FLAT          : [EDGE_STYLE.FLAT, EDGE_STYLE.TOOTHED],
            EDGE_ELEMENT_STYLE.FLAT_EXTENDED : [EDGE_STYLE.INTERNAL_FLAT, EDGE_STYLE.INTERNAL_TOOTHED],
            EDGE_ELEMENT_STYLE.REMOVE        : [EDGE_STYLE.FLAT, EDGE_STYLE.TOOTHED, EDGE_STYLE.INTERNAL_FLAT, EDGE_STYLE.INTERNAL_TOOTHED],
        }

    default_neighbour_styles = {
            EDGE_ELEMENT_STYLE.FLAT          : EDGE_STYLE.TOOTHED,
            EDGE_ELEMENT_STYLE.FLAT_EXTENDED : EDGE_STYLE.INTERNAL_FLAT,
            EDGE_ELEMENT_STYLE.REMOVE        : EDGE_STYLE.TOOTHED,
        }

    def __init__(self, pos, length, style, first_style, second_style):
        """
        For style == EDGE_ELEMENT_STYLE.TOOTHED first_style/second_style mean begin_style/end_style,
        for other values they mean previous_style/next_style.
        """

        self.pos = pos
        self.length = length
        self.style = style
        self.first_style = first_style
        self.second_style = second_style

    def get_counterpart_element(self):

        if self.style == EDGE_ELEMENT_STYLE.FLAT:
            d = {
                    EDGE_STYLE.FLAT    : EDGE_STYLE.INTERNAL_TOOTHED,
                    EDGE_STYLE.TOOTHED : EDGE_STYLE.INTERNAL_FLAT,
                }
            return _EdgeElement(self.pos, self.length, EDGE_ELEMENT_STYLE.FLAT_EXTENDED, d[self.first_style], d[self.second_style])

        elif self.style == EDGE_ELEMENT_STYLE.FLAT_EXTENDED:
            d = {
                    EDGE_STYLE.INTERNAL_FLAT    : EDGE_STYLE.TOOTHED,
                    EDGE_STYLE.INTERNAL_TOOTHED : EDGE_STYLE.FLAT,
                }
            return _EdgeElement(self.pos, self.length, EDGE_ELEMENT_STYLE.FLAT, d[self.first_style], d[self.second_style])

        elif self.style == EDGE_ELEMENT_STYLE.REMOVE:
            d = {
                    EDGE_STYLE.FLAT             : EDGE_STYLE.INTERNAL_TOOTHED,
                    EDGE_STYLE.TOOTHED          : EDGE_STYLE.INTERNAL_FLAT,
                    EDGE_STYLE.INTERNAL_FLAT    : EDGE_STYLE.INTERNAL_TOOTHED,
                    EDGE_STYLE.INTERNAL_TOOTHED : EDGE_STYLE.INTERNAL_FLAT,
                }
            return _EdgeElement(self.pos, self.length, EDGE_ELEMENT_STYLE.FLAT_EXTENDED, d[self.first_style], d[self.second_style])


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

        parts = self._prepare_part_list()

        return sum(
                (self._render_part(start, direction, self.outward_dir, displace, wall_thickness, config, p) for p in parts),
                Object2D()
            )

    def _check_sub_element_list_non_overlapping(self, sub_elements):
        """
        Check whether the given sub elements list contains no overlapping
        elements and the elements are contained in self's dimensions. The given
        list must be sorted.
        """

        part_positions = []

        for e in sub_elements:
            part_positions.append(e.pos)
            part_positions.append(e.pos + e.length)

        part_positions = [0] + part_positions + [self.length]

        # the resulting list must be sorted
        assert( all(part_positions[i] <= part_positions[i+1] for i in range(len(part_positions)-1)) )

    def _prepare_part_list(self):
        """
        Prepare a part list for rendering. Interleave configured sub elements
        with toothed segments, check begin/end styles, remove empty
        intermediate elements.
        """

        sub_elements = sorted(self.sub_elements, key=lambda x: x.pos)
        self._check_sub_element_list_non_overlapping(sub_elements)

        if self.flat:

            if self.sub_elements:
                raise Exception("Not implemented")

            parts = [_EdgeElement(0, self.length, 'flat', None, None)]

        else:

            parts = [_EdgeElement(0, None, EDGE_ELEMENT_STYLE.TOOTHED, self.begin_style, None)]

            for elem in sub_elements:
                prev_elem = parts[-1]

                # the previous element is a generated intermediate element with some unset values
                prev_elem.length = elem.pos - prev_elem.pos
                prev_elem.second_style = elem.first_style

                parts.append(elem)
                parts.append(_EdgeElement(elem.pos + elem.length, None, EDGE_ELEMENT_STYLE.TOOTHED, elem.second_style, None) )

            last_elem = parts[-1]
            last_elem.length = self.length - last_elem.pos
            last_elem.second_style = self.end_style

        # remove empty parts
        for p in parts:
            if p.length == 0:

                # only remove intermediate toothed elements
                assert(p.style == EDGE_ELEMENT_STYLE.TOOTHED)

                # check whether the edge styles are compatible
                bs, es = p.first_style, p.second_style
                if not ((bs == EDGE_STYLE.INTERNAL_FLAT and es in [EDGE_STYLE.FLAT, EDGE_STYLE.TOOTHED]) or \
                        (es == EDGE_STYLE.INTERNAL_FLAT and bs in [EDGE_STYLE.FLAT, EDGE_STYLE.TOOTHED])):
                    raise Exception("Zero length toothed edge element with incompatible edge styles.")

        return [p for p in parts if p.length != 0]


    def _render_part(self, start, direction, outward_dir, displace, wall_thickness, config, part):

        start = start + part.pos * direction
        length = part.length
        style = part.style

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
            l = [
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
                ]

            if part.first_style == EDGE_STYLE.INTERNAL_TOOTHED:
                del l[0]
            if part.second_style == EDGE_STYLE.INTERNAL_TOOTHED:
                del l[-1]

            return Object2D(l)

        elif style == EDGE_ELEMENT_STYLE.REMOVE:
            return Object2D()

        elif style == EDGE_ELEMENT_STYLE.TOOTHED:

            begin_style, end_style = part.first_style, part.second_style

            if (begin_style in [EDGE_STYLE.TOOTHED, EDGE_STYLE.EXTENDED, EDGE_STYLE.INTERNAL_TOOTHED] and end_style in [EDGE_STYLE.FLAT, EDGE_STYLE.INTERNAL_FLAT]) or \
                (begin_style in [EDGE_STYLE.FLAT, EDGE_STYLE.INTERNAL_FLAT] and end_style in [EDGE_STYLE.TOOTHED, EDGE_STYLE.EXTENDED, EDGE_STYLE.INTERNAL_TOOTHED]):

                odd_tooth_count = False

            else:
                odd_tooth_count = True

            tooth_count = self._get_tooth_count(config, length, odd_tooth_count)
            tooth_length = length / tooth_count

            tooth_length_satisfied = config.tooth_min_width <= tooth_length <= config.tooth_max_width
            layer = 'cut' if tooth_length_satisfied else 'warn'

            if not tooth_length_satisfied:
                print('WARNING: Tooth length restrictions not satisfied, rendering into warn layer. ({min} <= {len} <= {max})'.format(
                        max = config.tooth_max_width,
                        min = config.tooth_min_width,
                        len = tooth_length,
                    ))

            tooth_positions = [0] + list(np.cumsum([tooth_length for i in range(tooth_count)]))

            return self._render_toothed_line(
                    start,
                    begin_style,
                    end_style,
                    tooth_positions,
                    direction,
                    outward_dir,
                    wall_thickness,
                    displace,
                    layer
                )

    def add_element(self, pos, length, style, prev_style=None, next_style=None, auto_add_counterpart=True):

        if prev_style is None:
            prev_style = _EdgeElement.default_neighbour_styles[style]
        if next_style is None:
            next_style = _EdgeElement.default_neighbour_styles[style]

        assert(prev_style in _EdgeElement.allowed_neighbour_styles[style])
        assert(next_style in _EdgeElement.allowed_neighbour_styles[style])

        new_element = _EdgeElement(pos, length, style, prev_style, next_style)
        self.sub_elements.append(new_element)

        # add counterpart with matching styles
        if auto_add_counterpart and self.counterpart is not None:
            cp = new_element.get_counterpart_element()
            self.counterpart.add_element(cp.pos, cp.length, cp.style, cp.first_style, cp.second_style, False)



    #TODO should this really be a static method?
    @staticmethod
    def _render_toothed_line(start, begin_style, end_style, tooth_positions, direction, outward_dir, wall_thickness, displace=0, layer='cut'):
        """
        tooth_positions: list of starting points of tooths, including full edge length
                         i.e. [0, first_tooth_width, first_tooth_width + second_tooth_width, ..., full_edge_length]
        """

        if begin_style in [EDGE_STYLE.EXTENDED, EDGE_STYLE.TOOTHED, EDGE_STYLE.INTERNAL_TOOTHED]:
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

        elif begin_style == EDGE_STYLE.INTERNAL_TOOTHED:
            lines.append(Line(
                start + direction * (start_pos + displace) + outward_dir * (wall_thickness + displace),
                start + direction * (end_pos + displace) + outward_dir * (wall_thickness + displace)
                ))
            lines.append(Line(
                start + direction * (end_pos + displace) + outward_dir * (wall_thickness + displace),
                start + direction * (end_pos + displace) + outward_dir * displace
                ))


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

        elif end_style == EDGE_STYLE.INTERNAL_TOOTHED:
                lines.append(Line(
                    start + direction * (start_pos - displace) + outward_dir * displace,
                    start + direction * (start_pos - displace) + outward_dir * (wall_thickness + displace)
                    ))
                lines.append(Line(
                    start + direction * (start_pos - displace) + outward_dir * (wall_thickness + displace),
                    start + direction * (end_pos - displace) + outward_dir * (wall_thickness + displace)
                    ))


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

        return Object2D(lines + last_lines, layer)


    @staticmethod
    def _check_tooth_count(begin_style, end_style, tooth_count):
        """
        Check whether a specific tooth count matches given begin and end styles.
        """
        if tooth_count % 2 == 0:
            return  (begin_style in [EDGE_STYLE.EXTENDED, EDGE_STYLE.TOOTHED, EDGE_STYLE.INTERNAL_TOOTHED] and end_style in [EDGE_STYLE.FLAT, EDGE_STYLE.INTERNAL_FLAT]) or \
                    (end_style in [EDGE_STYLE.EXTENDED, EDGE_STYLE.TOOTHED, EDGE_STYLE.INTERNAL_TOOTHED] and begin_style in [EDGE_STYLE.FLAT, EDGE_STYLE.INTERNAL_FLAT])
        else:
            return  (begin_style in [EDGE_STYLE.EXTENDED, EDGE_STYLE.TOOTHED, EDGE_STYLE.INTERNAL_TOOTHED] and end_style in [EDGE_STYLE.EXTENDED, EDGE_STYLE.TOOTHED, EDGE_STYLE.INTERNAL_TOOTHED]) or \
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

        # check for satisfiability of tooth length restrictions

        if min_tooth_count > max_tooth_count:

            if config.abort_on_tooth_length_error:
                raise ValueError('Tooth length out of range.')

            else:
                # use min_tooth_count because max_tooth_count could be zero

                # check if parity is wrong
                if (min_tooth_count % 2 == 0 and odd_tooth_count) or \
                    (min_tooth_count % 2 == 1 and not odd_tooth_count):
                    # add one, because min_tooth_count could be equal to one
                    return min_tooth_count + 1

                else:
                    return min_tooth_count

        if min_tooth_count == max_tooth_count:
            if (min_tooth_count % 2 == 0 and odd_tooth_count) or \
                (min_tooth_count % 2 == 1 and not odd_tooth_count):

                if config.abort_on_tooth_length_error:
                    raise ValueError('Tooth length out of range.')

                else:
                    # add one, because min_tooth_count could be equal to one
                    return min_tooth_count + 1

        # tooth length restrictions are satisfiable, now optimize

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


    def _render_part(self, start, direction, outward_dir, displace, wall_thickness, config, part):

        start = start + part.pos * direction
        length = part.length
        style = part.style

        if style in ['flat', EDGE_ELEMENT_STYLE.FLAT, EDGE_ELEMENT_STYLE.REMOVE]:
            return CutoutEdge._render_rectangle(start, 0, length, direction, outward_dir, wall_thickness, displace)

        elif style == EDGE_ELEMENT_STYLE.FLAT_EXTENDED:
            return Object2D()

        elif style == EDGE_ELEMENT_STYLE.TOOTHED:

            begin_style, end_style = part.first_style, part.second_style

            if (begin_style in [EDGE_STYLE.TOOTHED, EDGE_STYLE.EXTENDED, EDGE_STYLE.INTERNAL_TOOTHED] and end_style in [EDGE_STYLE.FLAT, EDGE_STYLE.INTERNAL_FLAT]) or \
                (begin_style in [EDGE_STYLE.FLAT, EDGE_STYLE.INTERNAL_FLAT] and end_style in [EDGE_STYLE.TOOTHED, EDGE_STYLE.EXTENDED, EDGE_STYLE.INTERNAL_TOOTHED]):

                odd_tooth_count = False

            else:
                odd_tooth_count = True

            tooth_count = self._get_tooth_count(config, length, odd_tooth_count)
            tooth_length = length / tooth_count

            tooth_length_satisfied = config.tooth_min_width <= tooth_length <= config.tooth_max_width
            layer = 'cut' if tooth_length_satisfied else 'warn'

            if not tooth_length_satisfied:
                print('WARNING: Tooth length restrictions not satisfied, rendering into warn layer. ({min} <= {len} <= {max})'.format(
                        max = config.tooth_max_width,
                        min = config.tooth_min_width,
                        len = tooth_length,
                    ))

            tooth_positions = [0] + list(np.cumsum([tooth_length for i in range(tooth_count)]))

            return self._render_toothed_line(
                    start,
                    begin_style,
                    end_style,
                    tooth_positions,
                    direction,
                    outward_dir,
                    wall_thickness,
                    displace,
                    layer
                )


    @staticmethod
    def _render_toothed_line(start, begin_style, end_style, tooth_positions, direction, outward_dir, wall_thickness, displace=0, layer='cut'):
        """
        tooth_positions: list of starting points of tooths, including full edge length
                         i.e. [0, first_tooth_width, first_tooth_width + second_tooth_width, ..., full_edge_length]
        """

        if begin_style in [EDGE_STYLE.EXTENDED, EDGE_STYLE.TOOTHED, EDGE_STYLE.INTERNAL_TOOTHED]:
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


        lines = Object2D()

        # render teeth
        for start_pos, end_pos, extended in tooth_data:
            if not extended:
                lines.extend(CutoutEdge._render_rectangle(start, start_pos, end_pos, direction, outward_dir, wall_thickness, displace))

        lines.set_layer(layer)

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

    def add_element(self, pos, length, style, prev_style=None, next_style=None, auto_add_counterpart=True):
        self.target.add_element(self.position + pos, length, style, prev_style, next_style, auto_add_counterpart)

    def to_local_coords(self, v):
        assert(self.projection_dir is not None)
        return project_along_axis(v, self.projection_dir)

    def get_reference(self, pos=0, length=None, projection_dir=None):
        if length is not None:
            assert(pos + length <= self.length)
        return EdgeReference(self, pos, length, projection_dir)

    def dereference(self):
        return self.target.dereference()
