import numpy as np
import math

from util import DIR2, project_along_axis
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
    TOOTHED = 'toothed'
    EXTENDED = 'extended'
    FLAT = 'flat'
    INTERNAL_FLAT = 'internal_flat'
    OUTWARD = 'outward'
    INTERNAL_OUTWARD = 'internal_outward'

class EDGE_ELEMENT_STYLE():
    REMOVE = 'remove'
    FLAT = 'flat'
    FLAT_EXTENDED = 'flat_extended'
    TOOTHED = 'toothed'


class _EdgeElement():
    """
    Internal. Mainly used for data storage.
    """

    allowed_end_styles = {
            EDGE_ELEMENT_STYLE.FLAT          : set([EDGE_STYLE.FLAT, EDGE_STYLE.INTERNAL_FLAT]),
            EDGE_ELEMENT_STYLE.FLAT_EXTENDED : set([EDGE_STYLE.TOOTHED, EDGE_STYLE.EXTENDED, EDGE_STYLE.OUTWARD, EDGE_STYLE.INTERNAL_OUTWARD]),
            EDGE_ELEMENT_STYLE.REMOVE        : set([EDGE_STYLE.FLAT, EDGE_STYLE.INTERNAL_FLAT, EDGE_STYLE.OUTWARD, EDGE_STYLE.INTERNAL_OUTWARD]),
            EDGE_ELEMENT_STYLE.TOOTHED       : set([EDGE_STYLE.FLAT, EDGE_STYLE.TOOTHED, EDGE_STYLE.INTERNAL_FLAT, EDGE_STYLE.OUTWARD, EDGE_STYLE.INTERNAL_OUTWARD, EDGE_STYLE.EXTENDED]),
        }

    allowed_neighbour_styles = {
            EDGE_STYLE.TOOTHED          : set([EDGE_STYLE.INTERNAL_FLAT]),
            EDGE_STYLE.EXTENDED         : set(),
            EDGE_STYLE.FLAT             : set([EDGE_STYLE.INTERNAL_FLAT]),
            EDGE_STYLE.INTERNAL_FLAT    : set([EDGE_STYLE.FLAT, EDGE_STYLE.TOOTHED]),
            EDGE_STYLE.OUTWARD          : set([EDGE_STYLE.INTERNAL_OUTWARD]),
            EDGE_STYLE.INTERNAL_OUTWARD : set([EDGE_STYLE.OUTWARD]),
        }

    allowed_neighbour_element_styles = {
            EDGE_ELEMENT_STYLE.FLAT          : set([EDGE_STYLE.FLAT, EDGE_STYLE.TOOTHED]),
            EDGE_ELEMENT_STYLE.FLAT_EXTENDED : set([EDGE_STYLE.INTERNAL_FLAT, EDGE_STYLE.INTERNAL_OUTWARD]),
            EDGE_ELEMENT_STYLE.REMOVE        : set([EDGE_STYLE.FLAT, EDGE_STYLE.TOOTHED, EDGE_STYLE.INTERNAL_FLAT, EDGE_STYLE.INTERNAL_OUTWARD]),
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
                    EDGE_STYLE.FLAT    : EDGE_STYLE.INTERNAL_OUTWARD,
                    EDGE_STYLE.TOOTHED : EDGE_STYLE.INTERNAL_FLAT,
                }
            return _EdgeElement(self.pos, self.length, EDGE_ELEMENT_STYLE.FLAT_EXTENDED, d[self.first_style], d[self.second_style])

        elif self.style == EDGE_ELEMENT_STYLE.FLAT_EXTENDED:
            d = {
                    EDGE_STYLE.INTERNAL_FLAT    : EDGE_STYLE.TOOTHED,
                    EDGE_STYLE.INTERNAL_OUTWARD : EDGE_STYLE.FLAT,
                }
            return _EdgeElement(self.pos, self.length, EDGE_ELEMENT_STYLE.FLAT, d[self.first_style], d[self.second_style])

        elif self.style == EDGE_ELEMENT_STYLE.REMOVE:
            d = {
                    EDGE_STYLE.FLAT             : EDGE_STYLE.INTERNAL_OUTWARD,
                    EDGE_STYLE.TOOTHED          : EDGE_STYLE.INTERNAL_FLAT,
                    EDGE_STYLE.INTERNAL_FLAT    : EDGE_STYLE.INTERNAL_OUTWARD,
                    EDGE_STYLE.INTERNAL_OUTWARD : EDGE_STYLE.INTERNAL_FLAT,
                }
            return _EdgeElement(self.pos, self.length, EDGE_ELEMENT_STYLE.FLAT_EXTENDED, d[self.first_style], d[self.second_style])

    def get_own_edge_style(self, neighbour_style):
        allowed_styles = self.allowed_neighbour_styles[neighbour_style]
        end_styles = allowed_styles.intersection(self.allowed_end_styles[self.style])
        assert(len(end_styles) == 1)
        return end_styles.pop()

    def copy(self):
        return _EdgeElement(self.pos, self.length, self.style, self.first_style, self.second_style)

    def __str__(self):
        return '[{style} {pos},{len} {fs} {ss}]'.format(
                style = self.style,
                pos = self.pos,
                len = self.length,
                fs = self.first_style,
                ss = self.second_style,
            )


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
        direction = abs(DIR2.orthon(self.outward_dir))

        displace = config.cutting_width / 2.
        wall_thickness = config.wall_thickness

        elements = self._prepare_element_list(config)

        return sum(
                (self._render_element(start, direction, self.outward_dir, displace, wall_thickness, config, p) for p in elements),
                Object2D()
            )

    def _check_sub_element_list_non_overlapping(self, sub_elements):
        """
        Check whether the given sub elements list contains no overlapping
        elements and the elements are contained in self's dimensions. The given
        list must be sorted.
        """

        element_positions = []

        for e in sub_elements:
            element_positions.append(e.pos)
            element_positions.append(e.pos + e.length)

        element_positions = [0] + element_positions + [self.length]

        # the resulting list must be sorted
        assert( all(element_positions[i] <= element_positions[i+1] for i in range(len(element_positions)-1)) )

    def _prepare_element_list(self, config):
        """
        Prepare an element list for rendering. Interleave configured sub
        elements with toothed segments, check begin/end styles, remove empty
        intermediate elements.
        """

        sub_elements = sorted(self.sub_elements, key=lambda x: x.pos)
        self._check_sub_element_list_non_overlapping(sub_elements)

        if self.flat:

            if self.sub_elements:
                raise NotImplementedError('Flat edge with subelements not implemented')

            elements = [_EdgeElement(0, self.length, EDGE_ELEMENT_STYLE.FLAT, EDGE_STYLE.FLAT, EDGE_STYLE.FLAT)]

        else:

            elements = [_EdgeElement(0, None, EDGE_ELEMENT_STYLE.TOOTHED, self.begin_style, None)]

            for elem in sub_elements:
                elem = elem.copy()
                prev_elem = elements[-1]

                # the previous element is a generated intermediate element with some unset values
                prev_elem.length = elem.pos - prev_elem.pos
                prev_elem.second_style = elem.first_style

                elements.append(elem)
                elements.append(_EdgeElement(elem.pos + elem.length, None, EDGE_ELEMENT_STYLE.TOOTHED, elem.second_style, None) )

                elem.first_style = elem.get_own_edge_style(elem.first_style)
                elem.second_style = elem.get_own_edge_style(elem.second_style)

            last_elem = elements[-1]
            last_elem.length = self.length - last_elem.pos
            last_elem.second_style = self.end_style

        elements = self._remove_empty_elements(elements)
        elements = self._convert_toothed_elements(elements, config)

        return elements

    @staticmethod
    def _remove_empty_elements(elements):
        """
        Remove zero-length elements from the prepared element list. Check if
        removed elements have valid edge styles.
        """

        for e in elements:
            if e.length == 0:

                # only remove intermediate toothed elements
                assert(e.style == EDGE_ELEMENT_STYLE.TOOTHED)

                # check whether the edge styles are compatible
                bs, es = e.first_style, e.second_style
                if not ((bs == EDGE_STYLE.INTERNAL_FLAT and es in [EDGE_STYLE.FLAT, EDGE_STYLE.TOOTHED]) or \
                        (es == EDGE_STYLE.INTERNAL_FLAT and bs in [EDGE_STYLE.FLAT, EDGE_STYLE.TOOTHED])):
                    raise ValueError('Zero length toothed edge element with incompatible edge styles.')

        return [e for e in elements if e.length != 0]


    def _render_element(self, start, direction, outward_dir, displace, wall_thickness, config, element):

        start = start + element.pos * direction
        length = element.length
        style = element.style
        begin_style, end_style = element.first_style, element.second_style

        assert(begin_style in _EdgeElement.allowed_end_styles[style])
        assert(end_style   in _EdgeElement.allowed_end_styles[style])

        if style == EDGE_ELEMENT_STYLE.FLAT:

            s = -displace         if begin_style == EDGE_STYLE.FLAT else displace
            t = length + displace if end_style   == EDGE_STYLE.FLAT else length - displace

            return Object2D([Line(
                start + direction * s + outward_dir * displace,
                start + direction * t + outward_dir * displace
                )])

        elif style == EDGE_ELEMENT_STYLE.FLAT_EXTENDED:

            pd = {
                    EDGE_STYLE.TOOTHED          : displace,
                    EDGE_STYLE.EXTENDED         : wall_thickness + displace,
                    EDGE_STYLE.OUTWARD          : displace,
                    EDGE_STYLE.INTERNAL_OUTWARD : -displace,
                }

            s = -pd[begin_style]
            t = length + pd[end_style]

            l = []

            if begin_style == EDGE_STYLE.TOOTHED:
                l.append(Line(
                        start + direction * s + outward_dir * displace,
                        start + direction * s + outward_dir * (wall_thickness + displace)
                    ))

            l.append(Line(
                        start + direction * s + outward_dir * (wall_thickness + displace),
                        start + direction * t + outward_dir * (wall_thickness + displace)
                ))

            if end_style == EDGE_STYLE.TOOTHED:
                l.append(Line(
                        start + direction * t + outward_dir * (wall_thickness + displace),
                        start + direction * t + outward_dir * displace
                    ))

            return Object2D(l)

        elif style == EDGE_ELEMENT_STYLE.REMOVE:
            return Object2D()

        else:
            raise Exception("Invalid _EdgeElement for rendering.")

    def _convert_toothed_elements(self, elements, config):
        l = []

        for e in elements:

            if e.style != EDGE_ELEMENT_STYLE.TOOTHED:
                l.append(e)

            else:
                l.extend(self._prepare_toothed_element(e, config))

        return l

    def _prepare_toothed_element(self, element, config):

        assert(element.style == EDGE_ELEMENT_STYLE.TOOTHED)

        length = element.length
        begin_style, end_style = element.first_style, element.second_style

        assert(begin_style != EDGE_STYLE.OUTWARD)
        assert(end_style != EDGE_STYLE.OUTWARD)

        # calculate parity
        begin_outward = begin_style in [EDGE_STYLE.TOOTHED, EDGE_STYLE.EXTENDED, EDGE_STYLE.INTERNAL_OUTWARD]
        end_outward = end_style in [EDGE_STYLE.TOOTHED, EDGE_STYLE.EXTENDED, EDGE_STYLE.INTERNAL_OUTWARD]

        odd_tooth_count = (begin_outward and end_outward) or (not begin_outward and not end_outward)

        # calculate tooth length
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

        # prepare element data
        tooth_positions = [0] + list(np.cumsum([tooth_length for i in range(tooth_count)]))

        if begin_outward:
            style_list = [EDGE_ELEMENT_STYLE.FLAT_EXTENDED, EDGE_ELEMENT_STYLE.FLAT] * math.ceil(len(tooth_positions)/2)
        else:
            style_list = [EDGE_ELEMENT_STYLE.FLAT, EDGE_ELEMENT_STYLE.FLAT_EXTENDED] * math.ceil(len(tooth_positions)/2)

        tooth_data = zip(tooth_positions[:-1], style_list)

        # construct elements
        elements = [_EdgeElement(
                element.pos + pos,
                tooth_length,
                style,
                EDGE_STYLE.INTERNAL_FLAT if style == EDGE_ELEMENT_STYLE.FLAT else EDGE_STYLE.TOOTHED,
                EDGE_STYLE.INTERNAL_FLAT if style == EDGE_ELEMENT_STYLE.FLAT else EDGE_STYLE.TOOTHED,
            ) for pos, style in tooth_data]

        elements[0].first_style = begin_style
        elements[-1].second_style = end_style

        return elements

    def add_element(self, pos, length, style, prev_style=None, next_style=None, auto_add_counterpart=True):

        if prev_style is None:
            prev_style = _EdgeElement.default_neighbour_styles[style]
        if next_style is None:
            next_style = _EdgeElement.default_neighbour_styles[style]

        assert(prev_style in _EdgeElement.allowed_neighbour_element_styles[style])
        assert(next_style in _EdgeElement.allowed_neighbour_element_styles[style])

        new_element = _EdgeElement(pos, length, style, prev_style, next_style)
        self.sub_elements.append(new_element)

        # add counterpart with matching styles
        if auto_add_counterpart:
            assert(self.counterpart is not None)

            cp = new_element.get_counterpart_element()
            self.counterpart.add_element(cp.pos, cp.length, cp.style, cp.first_style, cp.second_style, False)


    @staticmethod
    def _check_tooth_count(begin_style, end_style, tooth_count):
        """
        Check whether a specific tooth count matches given begin and end styles.
        """
        if tooth_count % 2 == 0:
            return  (begin_style in [EDGE_STYLE.EXTENDED, EDGE_STYLE.TOOTHED, EDGE_STYLE.INTERNAL_OUTWARD] and end_style in [EDGE_STYLE.FLAT, EDGE_STYLE.INTERNAL_FLAT]) or \
                    (end_style in [EDGE_STYLE.EXTENDED, EDGE_STYLE.TOOTHED, EDGE_STYLE.INTERNAL_OUTWARD] and begin_style in [EDGE_STYLE.FLAT, EDGE_STYLE.INTERNAL_FLAT])
        else:
            return  (begin_style in [EDGE_STYLE.EXTENDED, EDGE_STYLE.TOOTHED, EDGE_STYLE.INTERNAL_OUTWARD] and end_style in [EDGE_STYLE.EXTENDED, EDGE_STYLE.TOOTHED, EDGE_STYLE.INTERNAL_OUTWARD]) or \
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


    @staticmethod
    def _remove_empty_elements(elements):

        for e in elements:
            if e.length == 0:

                # only remove intermediate toothed elements
                assert(e.style == EDGE_ELEMENT_STYLE.TOOTHED)

        return [e for e in elements if e.length != 0]

    def _render_element(self, start, direction, outward_dir, displace, wall_thickness, config, element):

        start = start + element.pos * direction
        length = element.length
        style = element.style
        begin_style, end_style = element.first_style, element.second_style

        if style in [EDGE_ELEMENT_STYLE.FLAT, EDGE_ELEMENT_STYLE.REMOVE]:

            assert(begin_style in _EdgeElement.allowed_end_styles[EDGE_ELEMENT_STYLE.FLAT])
            assert(end_style   in _EdgeElement.allowed_end_styles[EDGE_ELEMENT_STYLE.FLAT])

            assert(begin_style == EDGE_STYLE.INTERNAL_FLAT)
            assert(end_style   == EDGE_STYLE.INTERNAL_FLAT)

            return CutoutEdge._render_rectangle(start, 0, length, direction, outward_dir, wall_thickness, displace)

        elif style == EDGE_ELEMENT_STYLE.FLAT_EXTENDED:
            return Object2D()

        else:
            raise Exception("Invalid _EdgeElement for rendering.")

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
