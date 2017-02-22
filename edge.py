import numpy as np
import math

from util import DIR2, almost_equal
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

    default_end_styles = {
            EDGE_ELEMENT_STYLE.FLAT          : EDGE_STYLE.INTERNAL_FLAT,
            EDGE_ELEMENT_STYLE.FLAT_EXTENDED : EDGE_STYLE.TOOTHED,
            EDGE_ELEMENT_STYLE.REMOVE        : EDGE_STYLE.INTERNAL_FLAT,
            EDGE_ELEMENT_STYLE.TOOTHED       : EDGE_STYLE.TOOTHED,
        }

    allowed_neighbour_styles = {
            EDGE_STYLE.TOOTHED          : set([EDGE_STYLE.INTERNAL_FLAT]),
            EDGE_STYLE.EXTENDED         : set(),
            EDGE_STYLE.FLAT             : set([EDGE_STYLE.INTERNAL_FLAT]),
            EDGE_STYLE.INTERNAL_FLAT    : set([EDGE_STYLE.FLAT, EDGE_STYLE.TOOTHED]),
            EDGE_STYLE.OUTWARD          : set([EDGE_STYLE.INTERNAL_OUTWARD]),
            EDGE_STYLE.INTERNAL_OUTWARD : set([EDGE_STYLE.OUTWARD]),
        }

    allowed_neighbour_corner_styles = {
            EDGE_STYLE.TOOTHED          : set([EDGE_STYLE.FLAT, EDGE_STYLE.TOOTHED]),
            EDGE_STYLE.EXTENDED         : set([EDGE_STYLE.EXTENDED]),
            EDGE_STYLE.FLAT             : set([EDGE_STYLE.FLAT, EDGE_STYLE.TOOTHED]),
            EDGE_STYLE.INTERNAL_FLAT    : set(),
            EDGE_STYLE.OUTWARD          : set(),
            EDGE_STYLE.INTERNAL_OUTWARD : set(),
        }

    def __init__(self, pos, length, style, begin_style, end_style, prev_style=None, next_style=None, layer=None):

        self.pos = pos
        self.length = length
        self.style = style
        self.begin_style = begin_style
        self.end_style = end_style
        self.prev_style = prev_style
        self.next_style = next_style
        self.layer = layer

    def get_counterpart_element(self):
        """
        Get an edge element representing a matching counterpart for this
        element.
        """

        if self.style == EDGE_ELEMENT_STYLE.FLAT:
            d = {
                    EDGE_STYLE.FLAT          : EDGE_STYLE.INTERNAL_OUTWARD,
                    EDGE_STYLE.INTERNAL_FLAT : EDGE_STYLE.OUTWARD,
                    EDGE_STYLE.TOOTHED       : EDGE_STYLE.INTERNAL_FLAT,
                    None                     : None,
                }
            return _EdgeElement(self.pos, self.length, EDGE_ELEMENT_STYLE.FLAT_EXTENDED, None, None, d[self.prev_style], d[self.next_style])

        elif self.style == EDGE_ELEMENT_STYLE.FLAT_EXTENDED:
            d = {
                    EDGE_STYLE.INTERNAL_FLAT    : EDGE_STYLE.TOOTHED,
                    EDGE_STYLE.INTERNAL_OUTWARD : EDGE_STYLE.FLAT,
                    EDGE_STYLE.OUTWARD          : EDGE_STYLE.INTERNAL_FLAT,
                    None                        : None,
                }
            return _EdgeElement(self.pos, self.length, EDGE_ELEMENT_STYLE.FLAT, None, None, d[self.prev_style], d[self.next_style])

        elif self.style == EDGE_ELEMENT_STYLE.REMOVE:
            d = {
                    EDGE_STYLE.FLAT             : EDGE_STYLE.INTERNAL_OUTWARD,
                    EDGE_STYLE.INTERNAL_FLAT    : EDGE_STYLE.OUTWARD,
                    EDGE_STYLE.TOOTHED          : EDGE_STYLE.INTERNAL_FLAT,
                    EDGE_STYLE.INTERNAL_OUTWARD : EDGE_STYLE.FLAT,
                    EDGE_STYLE.OUTWARD          : EDGE_STYLE.INTERNAL_FLAT,
                    None                        : None,
                }
            return _EdgeElement(self.pos, self.length, EDGE_ELEMENT_STYLE.FLAT_EXTENDED, None, None, d[self.prev_style], d[self.next_style])

    def copy(self):
        return _EdgeElement(self.pos, self.length, self.style, self.begin_style, self.end_style, self.prev_style, self.next_style, self.layer)

    def __str__(self):
        return '[EE {style} {pos},{len} {fs} {ss}]'.format(
                style = self.style,
                pos = self.pos,
                len = self.length,
                fs = self.begin_style,
                ss = self.end_style,
            )

    def __repr__(self):

        opt = ''

        if self.prev_style is not None:
            opt += ', prev_style={}'.format(self.prev_style)
        if self.next_style is not None:
            opt += ', next_style={}'.format(self.next_style)
        if self.layer is not None:
            opt += ', layer={}'.format(self.layer)

        return '_EdgeElement({}, {}, {}, {}, {}{})'.format(
                self.pos,
                self.length,
                self.style,
                self.begin_style,
                self.end_style,
                opt,
            )


class Edge(PlanarObject):
    """
    A 2D object representing a wall's edge.

    Renders a toothed line according to configured values.

    Always renders into positive X or Y direction. The direction in which
    extending teeth are rendered is controlled by the outward_dir parameter.
    This one also controls the general rendering direction of the edge.
    """

    def __init__(self, length, outward_dir, begin_style=EDGE_STYLE.FLAT, end_style=EDGE_STYLE.FLAT, style=EDGE_ELEMENT_STYLE.TOOTHED, layer='cut'):
        super(Edge, self).__init__(layer)

        self.length = length
        self.outward_dir = outward_dir / np.linalg.norm(outward_dir)
        self.begin_style = begin_style
        self.end_style = end_style
        self.style = style

        self.counterpart = None

        self.sub_elements = []


    def add_element(self, pos, length, style, begin_style=None, end_style=None, prev_style=None, next_style=None, auto_add_counterpart=True):
        """
        Add a new edge element subelement to this edge. If auto_add_counterpart
        is True a corresponding edge element is also added to this edge's
        counterpart. In this case an exception is raised, if no counterpart is
        configured.
        """

        assert(begin_style is None or begin_style in _EdgeElement.allowed_end_styles[style])
        assert(end_style   is None or end_style   in _EdgeElement.allowed_end_styles[style])

        new_element = _EdgeElement(pos, length, style, begin_style, end_style, prev_style, next_style)
        self.sub_elements.append(new_element)

        # add counterpart with matching styles
        if auto_add_counterpart:
            assert(self.counterpart is not None)

            cp = new_element.get_counterpart_element()
            self.counterpart.add_element(cp.pos, cp.length, cp.style, cp.begin_style, cp.end_style, cp.prev_style, cp.next_style, False)

    def set_style(self, style, set_counterpart=True):
        """
        Set the edge's main style. If set_counterpart is True the counterpart's
        style will be changed accordingly, too. In this case an exception is
        raised, if no counterpart is configured.
        """

        self.style = style

        if set_counterpart:
            assert(self.counterpart is not None)

            if style in [EDGE_ELEMENT_STYLE.FLAT, EDGE_ELEMENT_STYLE.REMOVE]:
                self.counterpart.set_style(EDGE_ELEMENT_STYLE.FLAT_EXTENDED, set_counterpart=False)
            elif style == EDGE_ELEMENT_STYLE.FLAT_EXTENDED:
                self.counterpart.set_style(EDGE_ELEMENT_STYLE.FLAT, set_counterpart=False)
            elif style == EDGE_ELEMENT_STYLE.TOOTHED:
                self.counterpart.set_style(EDGE_ELEMENT_STYLE.TOOTHED, set_counterpart=False)

    def set_counterpart(self, counterpart, backreference=True):
        """
        Set the edge's counterpart. If backreference is True the a reference to
        this edge is added to the new counterpart, too.
        """

        assert(self.counterpart is None)
        assert(self.length == counterpart.length)

        self.counterpart = counterpart.get_reference()

        if backreference:
            counterpart.set_counterpart(self, False)


    def render(self, config):

        start = np.array([0,0])

        # perpendicular to outward direction
        # abs works because this should be a unit vector or its negative
        direction = abs(DIR2.orthon(self.outward_dir))

        displace = config.cutting_width / 2.
        wall_thickness = config.wall_thickness

        elements = self._prepare_element_list(config)

        self._check_counterpart_elements_matching(elements, config)

        return sum(
                (self._render_element(start, direction, self.outward_dir, displace, wall_thickness, config, p) for p in elements),
                Object2D()
            )


    def _prepare_element_list(self, config):
        """
        Prepare an element list for rendering. Interleave configured sub
        elements with toothed segments, check begin/end styles, remove empty
        intermediate elements.
        """

        sub_elements = sorted(self.sub_elements, key=lambda x: x.pos)
        self._check_sub_element_list_non_overlapping(sub_elements)


        elements = [_EdgeElement(0, None, self.style, self.begin_style, None, None, None)]

        for elem in sub_elements:
            prev_elem = elements[-1]

            # the previous element is a generated intermediate element with some unset values
            prev_elem.length = elem.pos - prev_elem.pos
            prev_elem.end_style = elem.prev_style

            elements.append(elem.copy())
            elements.append(_EdgeElement(elem.pos + elem.length, None, self.style, elem.next_style, None, None, None) )

        last_elem = elements[-1]
        last_elem.length = self.length - last_elem.pos
        last_elem.end_style = self.end_style


        elements = self._remove_empty_elements(elements)
        elements = self._calculate_element_edge_styles(elements)
        elements = self._convert_toothed_elements(elements, config)

        return elements

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


    @staticmethod
    def _remove_empty_elements(elements):
        """
        Remove zero-length elements from the prepared element list. Check if
        removed elements' edge styles match with their neighbour elements,
        transfer if needed.
        """

        t = [None] + elements + [None]

        for prev_elem, cur_elem, next_elem in zip(t, t[1:], t[2:]):
            if cur_elem.length == 0:

                if prev_elem is not None:

                    if prev_elem.length == 0:
                        raise Exception('Neighbouring zero-length edge elements.')

                    if cur_elem.end_style is not None:

                        if not (prev_elem.end_style == cur_elem.end_style or prev_elem.end_style is None):
                            raise Exception('Zero-length edge element with non-matching previous end_style.')

                        prev_elem.end_style = cur_elem.end_style

                if next_elem is not None:

                    if next_elem.length == 0:
                        raise Exception('Neighbouring zero-length edge elements.')

                    if cur_elem.begin_style is not None:

                        if not (next_elem.begin_style == cur_elem.begin_style or next_elem.begin_style is None):
                            raise Exception('Zero-length edge element with non-matching next begin_style.')
                        next_elem.begin_style = cur_elem.begin_style

        return [e for e in elements if e.length != 0]


    @staticmethod
    def _calculate_element_edge_styles(elements):
        """
        Set neighbouring edge elements' edge styles to default values, if still
        unspecified.
        """

        for first_elem, second_elem in zip(elements, elements[1:]):

            if first_elem.end_style is None and second_elem.begin_style is None:

                default_first  = _EdgeElement.default_end_styles[first_elem.style]
                default_second = _EdgeElement.default_end_styles[second_elem.style]

                allowed_first  = _EdgeElement.allowed_end_styles[first_elem.style]
                allowed_second = _EdgeElement.allowed_end_styles[second_elem.style]

                allowed_from_neigh_first  = set.union(*(_EdgeElement.allowed_neighbour_styles[s] for s in allowed_second))
                allowed_from_neigh_second = set.union(*(_EdgeElement.allowed_neighbour_styles[s] for s in allowed_first))

                allowed_first  = set.intersection(allowed_first,  allowed_from_neigh_first)
                allowed_second = set.intersection(allowed_second, allowed_from_neigh_second)

                assert(len(allowed_first)  >= 1)
                assert(len(allowed_second) >= 1)

                if default_first in allowed_first:
                    first_elem.end_style = default_first

                elif default_second in allowed_second:
                    second_elem.begin_style = default_second

                else:
                    first_elem.end_style = allowed_first.pop()

                # fallthrough

            if first_elem.end_style is None:

                t = _EdgeElement.allowed_neighbour_styles[second_elem.begin_style]
                t = set.intersection(t, _EdgeElement.allowed_end_styles[first_elem.style])

                assert(len(t) >= 1)

                default = _EdgeElement.default_end_styles[first_elem.style]
                first_elem.end_style = default if default in t else t.pop()

            elif second_elem.begin_style is None:

                t = _EdgeElement.allowed_neighbour_styles[first_elem.end_style]
                t = set.intersection(t, _EdgeElement.allowed_end_styles[second_elem.style])

                assert(len(t) >= 1)

                default = _EdgeElement.default_end_styles[second_elem.style]
                second_elem.begin_style = default if default in t else t.pop()

            assert(first_elem.end_style is not None and second_elem.begin_style is not None)

            # one should be enough, but...
            assert(first_elem.end_style in _EdgeElement.allowed_neighbour_styles[second_elem.begin_style])
            assert(second_elem.begin_style in _EdgeElement.allowed_neighbour_styles[first_elem.end_style])

        return elements


    def _convert_toothed_elements(self, elements, config):
        """
        Convert all toothed edge elements in the list into their corresponding
        list of teeth given by FLAT / FLAT_EXTENDED edge elements.
        """

        l = []

        for e in elements:

            if e.style != EDGE_ELEMENT_STYLE.TOOTHED:
                l.append(e)

            else:
                l.extend(self._prepare_toothed_element(e, config))

        return l

    def _prepare_toothed_element(self, element, config):
        """
        Convert a single toothed edge element into its corresponding list of
        teeth given by FLAT / FLAT_EXTENDED edge elements.

        This is where tooth length calculation is done.
        """

        assert(element.style == EDGE_ELEMENT_STYLE.TOOTHED)

        length = element.length
        begin_style, end_style = element.begin_style, element.end_style

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
        layer = None if tooth_length_satisfied else 'warn'

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
                None,
                None,
                layer,
            ) for pos, style in tooth_data]

        elements[0].begin_style = begin_style
        elements[-1].end_style = end_style

        return elements


    def _check_counterpart_elements_matching(self, elements, config):
        """
        Check whether the calculated elements match the ones of the counterpart
        edge, if it exists.
        """

        if self.counterpart is None:
            return

        cp_elements = self.counterpart.dereference()._prepare_element_list(config)

        if len(elements) != len(cp_elements):
            print('WARNING: Edge counterpart count mismatch, rendering into error layer.')
            for e in elements:
                e.layer = 'error'
            return

        for a, b in zip(elements, cp_elements):

            if not almost_equal(a.pos, b.pos):
                a.layer = 'error'
                print('WARNING: Edge element counterpart position mismatch, rendering into error layer.')
                continue
            if not almost_equal(a.length, b.length):
                a.layer = 'error'
                print('WARNING: Edge element counterpart length mismatch, rendering into error layer.')
                continue

            if a.style == EDGE_ELEMENT_STYLE.FLAT:
                if not b.style in [EDGE_ELEMENT_STYLE.FLAT_EXTENDED, EDGE_ELEMENT_STYLE.REMOVE]:
                    a.layer = 'error'
                    print('WARNING: Edge element counterpart style mismatch, rendering into error layer.')
            elif a.style == EDGE_ELEMENT_STYLE.FLAT_EXTENDED:
                if not b.style in [EDGE_ELEMENT_STYLE.FLAT, EDGE_ELEMENT_STYLE.REMOVE]:
                    a.layer = 'error'
                    print('WARNING: Edge element counterpart style mismatch, rendering into error layer.')
            elif a.style == EDGE_ELEMENT_STYLE.REMOVE:
                if not b.style in [EDGE_ELEMENT_STYLE.FLAT, EDGE_ELEMENT_STYLE.FLAT_EXTENDED, EDGE_ELEMENT_STYLE.REMOVE]:
                    a.layer = 'error'
                    print('WARNING: Edge element counterpart style mismatch, rendering into error layer.')
            else:
                assert(False)


    def _render_element(self, start, direction, outward_dir, displace, wall_thickness, config, element):
        """
        Render a single edge element into an Object2D.
        """

        start = start + element.pos * direction
        length = element.length
        style = element.style
        begin_style, end_style = element.begin_style, element.end_style
        layer = element.layer or self.layer

        assert(begin_style in _EdgeElement.allowed_end_styles[style])
        assert(end_style   in _EdgeElement.allowed_end_styles[style])

        if style == EDGE_ELEMENT_STYLE.FLAT:

            s = -displace         if begin_style == EDGE_STYLE.FLAT else displace
            t = length + displace if end_style   == EDGE_STYLE.FLAT else length - displace

            return Object2D([Line(
                start + direction * s + outward_dir * displace,
                start + direction * t + outward_dir * displace,
                )], layer)

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
                        start + direction * s + outward_dir * (wall_thickness + displace),
                    ))

            l.append(Line(
                        start + direction * s + outward_dir * (wall_thickness + displace),
                        start + direction * t + outward_dir * (wall_thickness + displace),
                ))

            if end_style == EDGE_STYLE.TOOTHED:
                l.append(Line(
                        start + direction * t + outward_dir * (wall_thickness + displace),
                        start + direction * t + outward_dir * displace,
                    ))

            return Object2D(l, layer)

        elif style == EDGE_ELEMENT_STYLE.REMOVE:
            return Object2D()

        else:
            raise Exception("Invalid _EdgeElement for rendering.")


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
    """
    A specialized edge rendering flat teeth as rectangular cutouts.

    Used to place a wall into the middle of another wall.
    """

    def _render_element(self, start, direction, outward_dir, displace, wall_thickness, config, element):

        start = start + element.pos * direction
        length = element.length
        style = element.style
        begin_style, end_style = element.begin_style, element.end_style
        layer = element.layer or self.layer

        if style in [EDGE_ELEMENT_STYLE.FLAT, EDGE_ELEMENT_STYLE.REMOVE]:

            assert(begin_style in _EdgeElement.allowed_end_styles[EDGE_ELEMENT_STYLE.FLAT])
            assert(end_style   in _EdgeElement.allowed_end_styles[EDGE_ELEMENT_STYLE.FLAT])

            start_pos = 0
            end_pos = length

            lines = []

            lines.append(Line(
                        start + direction * (start_pos + displace) + outward_dir * displace,
                        start + direction * (end_pos - displace) + outward_dir * displace
                ))

            if end_style == EDGE_STYLE.INTERNAL_FLAT:
                lines.append(Line(
                        start + direction * (end_pos - displace) + outward_dir * displace,
                        start + direction * (end_pos - displace) + outward_dir * (wall_thickness - displace)
                    ))

            lines.append(Line(
                        start + direction * (end_pos - displace) + outward_dir * (wall_thickness - displace),
                        start + direction * (start_pos + displace) + outward_dir * (wall_thickness - displace)
                ))

            if begin_style == EDGE_STYLE.INTERNAL_FLAT:
                lines.append(Line(
                        start + direction * (start_pos + displace) + outward_dir * (wall_thickness - displace),
                        start + direction * (start_pos + displace) + outward_dir * displace
                    ))

            return Object2D(lines, layer)

        elif style == EDGE_ELEMENT_STYLE.FLAT_EXTENDED:
            return Object2D()

        else:
            raise Exception("Invalid _EdgeElement for rendering.")

class EdgeReference():
    """
    A reference object for edges.

    Contains logic to do coordinate transformations to automatically project
    coordinates to 1D and translate children's positions when adding them to
    the target edge.

    This allows to reference a subpart of an edge and use it as if it were a
    complete edge.
    """

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

    def add_element(self, pos, length, style, begin_style=None, end_style=None, prev_style=None, next_style=None, auto_add_counterpart=True):
        self.target.add_element(self.position + pos, length, style, begin_style, end_style, prev_style, next_style, auto_add_counterpart)

    def set_style(self, style, set_counterpart=True):
        if self.position != 0 and self.length != target.length:
            raise Exception('Setting main edge style not supported for partial edge references.')

        self.target.set_style(style, set_counterpart)

    def set_counterpart(self, counterpart, backreference=True):
        if self.position != 0 and self.length != target.length:
            raise Exception('Setting counterpart not supported for partial edge references.')

        self.target.set_counterpart(counterpart, backreference)

    def to_local_coords(self, v):
        assert(self.projection_dir is not None)
        return DIR2.project_along_axis(v, self.projection_dir)

    def get_reference(self, pos=0, length=None, projection_dir=None):
        if length is not None:
            assert(pos + length <= self.length)
        return EdgeReference(self, pos, length, projection_dir)

    def dereference(self):
        return self.target.dereference()
