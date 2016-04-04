import numpy as np
import math

DIR_UP    = np.array([ 0, 1, 0])
DIR_DOWN  = np.array([ 0,-1, 0])
DIR_LEFT  = np.array([-1, 0, 0])
DIR_RIGHT = np.array([ 1, 0, 0])
DIR_FRONT = np.array([ 0, 0, 1])
DIR_BACK  = np.array([ 0, 0,-1])

EDGE_STYLE_TOOTHED, \
EDGE_STYLE_EXTENDED, \
EDGE_STYLE_FLAT, \
EDGE_STYLE_INTERNAL_FLAT = range(4)

def orthon(v):
    return np.array([-v[1], v[0]]) / np.linalg.norm(v)

class Line():
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def __add__(self, b):
        return Line(self.start + b, self.end + b)
    def __sub__(self, b):
        return Line(self.start - b, self.end - b)

class CutoutRect():
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def render(self, config):

        displace = config.cutting_width / 2.

        l = []

        l.append(Line(np.array([displace,              displace]),               np.array([self.width - displace, displace])))
        l.append(Line(np.array([self.width - displace, displace]),               np.array([self.width - displace, self.height - displace])))
        l.append(Line(np.array([self.width - displace, self.height - displace]), np.array([displace,              self.height - displace])))
        l.append(Line(np.array([displace,              self.height - displace]), np.array([displace,              displace])))

        return l

class Edge():
    def __init__(self, length, outward_dir, begin_style=EDGE_STYLE_FLAT, end_style=EDGE_STYLE_FLAT, flat=False):
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
            return [Line(
                start - direction * displace + self.outward_dir * displace,
                start + direction * (self.length + displace) + self.outward_dir * displace
                )]


        if (self.begin_style in [EDGE_STYLE_TOOTHED, EDGE_STYLE_EXTENDED] and self.end_style == EDGE_STYLE_FLAT) or \
            (self.begin_style == EDGE_STYLE_FLAT and self.end_style in [EDGE_STYLE_TOOTHED, EDGE_STYLE_EXTENDED]):

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

        if begin_style in [EDGE_STYLE_EXTENDED, EDGE_STYLE_TOOTHED]:
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

        if begin_style == EDGE_STYLE_EXTENDED:
            lines.append(Line(
                start + direction * (start_pos - wall_thickness - displace) + outward_dir * (wall_thickness + displace),
                start + direction * (end_pos + displace) + outward_dir * (wall_thickness + displace)
                ))
            lines.append(Line(
                start + direction * (end_pos + displace) + outward_dir * (wall_thickness + displace),
                start + direction * (end_pos + displace) + outward_dir * displace
                ))

        elif begin_style == EDGE_STYLE_TOOTHED:
            middle_teeth = tooth_data[0:-1]

        elif begin_style == EDGE_STYLE_FLAT:
            lines.append(Line(
                start + direction * (start_pos - displace) + outward_dir * displace,
                start + direction * (end_pos - displace) + outward_dir * displace
                ))

        elif begin_style == EDGE_STYLE_INTERNAL_FLAT:
            middle_teeth = tooth_data[0:-1]


        # render last tooth
        start_pos, end_pos, extended = tooth_data[-1]
        last_lines = []

        if end_style == EDGE_STYLE_FLAT:
            last_lines.append(Line(
                start + direction * (start_pos + displace) + outward_dir * displace,
                start + direction * (end_pos + displace) + outward_dir * displace,
                ))

        elif end_style == EDGE_STYLE_EXTENDED:
            last_lines.append(Line(
                start + direction * (start_pos - displace) + outward_dir * displace,
                start + direction * (start_pos - displace) + outward_dir * (wall_thickness + displace),
                ))
            last_lines.append(Line(
                start + direction * (start_pos - displace) + outward_dir * (wall_thickness + displace),
                start + direction * (end_pos + wall_thickness + displace) + outward_dir * (wall_thickness + displace),
                ))

        elif end_style == EDGE_STYLE_TOOTHED:
            middle_teeth.append(tooth_data[-1])

        elif end_style == EDGE_STYLE_INTERNAL_FLAT:
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

        return lines + last_lines


    @staticmethod
    def _check_tooth_count(begin_style, end_style, tooth_count):
        if tooth_count % 2 == 0:
            return  (begin_style in [EDGE_STYLE_EXTENDED, EDGE_STYLE_TOOTHED] and end_style in [EDGE_STYLE_FLAT, EDGE_STYLE_INTERNAL_FLAT]) or \
                    (end_style in [EDGE_STYLE_EXTENDED, EDGE_STYLE_TOOTHED] and begin_style in [EDGE_STYLE_FLAT, EDGE_STYLE_INTERNAL_FLAT])
        else:
            return  (begin_style in [EDGE_STYLE_EXTENDED, EDGE_STYLE_TOOTHED] and end_style in [EDGE_STYLE_EXTENDED, EDGE_STYLE_TOOTHED]) or \
                    (begin_style in [EDGE_STYLE_FLAT, EDGE_STYLE_INTERNAL_FLAT] and end_style in [EDGE_STYLE_FLAT, EDGE_STYLE_INTERNAL_FLAT])

    @staticmethod
    def _get_tooth_count(config, length, odd_tooth_count):
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

        return lines


    @staticmethod
    def _render_toothed_line(start, begin_style, end_style, tooth_positions, direction, outward_dir, wall_thickness, displace=0):
        """
        tooth_positions: list of starting points of tooths, including full edge length
                         i.e. [0, first_tooth_width, first_tooth_width + second_tooth_width, ..., full_edge_length]
        """

        if begin_style in [EDGE_STYLE_EXTENDED, EDGE_STYLE_TOOTHED]:
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

        if begin_style == EDGE_STYLE_EXTENDED:
            lines.extend(self._render_rectangle(start, start_pos - wall_thickness, end_pos, direction, outward_dir, wall_thickness, displace))

        elif begin_style == EDGE_STYLE_TOOTHED:
            middle_teeth = tooth_data[0:-1]


        # render last tooth
        start_pos, end_pos, extended = tooth_data[-1]
        last_lines = []

        if end_style == EDGE_STYLE_EXTENDED:
            lines.extend(self._render_rectangle(start, start_pos, end_pos + wall_thickness, direction, outward_dir, wall_thickness, displace))

        elif end_style == EDGE_STYLE_TOOTHED:
            middle_teeth.append(tooth_data[-1])


        # render middle teeth
        for start_pos, end_pos, extended in middle_teeth:
            if extended:
                lines.extend(self._render_rectangle(start, start_pos, end_pos, direction, outward_dir, wall_thickness, displace))

        return lines + last_lines


class Wall():
    #width = None
    #height = None
    #children = None
    #edges = None

    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.children = []

        self._construct_edges()

    def _construct_edges(self):
        raise Exception("Abstract method")

    def get_edge_by_direction(self, v):
        if (v[0:2] == DIR_UP).all():    return self.edges[0]
        if (v[0:2] == DIR_DOWN).all():  return self.edges[1]
        if (v[0:2] == DIR_LEFT).all():  return self.edges[2]
        if (v[0:2] == DIR_RIGHT).all(): return self.edges[3]

    def render(self, config):
        l = []

        l.extend(i + np.array([0, self.height]) for i in self.edges[0].render(config))
        l.extend(i + np.array([0, 0])           for i in self.edges[1].render(config))
        l.extend(i + np.array([0, 0])           for i in self.edges[2].render(config))
        l.extend(i + np.array([self.width, 0])  for i in self.edges[3].render(config))

        for child, pos in self.children:
            l.extend(i + pos for i in child.render(config))

        return l

class ToplessWall(Wall):
    def _construct_edges(self):
        self.edges = []
        self.edges.append(Edge(self.width,  np.array([ 0, 1]), flat=True))
        self.edges.append(Edge(self.width,  np.array([ 0,-1]), EDGE_STYLE_FLAT, EDGE_STYLE_FLAT))
        self.edges.append(Edge(self.height, np.array([-1, 0]), EDGE_STYLE_FLAT, EDGE_STYLE_TOOTHED))
        self.edges.append(Edge(self.height, np.array([ 1, 0]), EDGE_STYLE_TOOTHED, EDGE_STYLE_FLAT))

class ExtendedWall(Wall):
    def _construct_edges(self):
        self.edges = []
        self.edges.append(Edge(self.width,  np.array([ 0,-1]), EDGE_STYLE_EXTENDED, EDGE_STYLE_EXTENDED))
        self.edges.append(Edge(self.width,  np.array([ 0, 1]), EDGE_STYLE_EXTENDED, EDGE_STYLE_EXTENDED))
        self.edges.append(Edge(self.height, np.array([-1, 0]), EDGE_STYLE_EXTENDED, EDGE_STYLE_EXTENDED))
        self.edges.append(Edge(self.height, np.array([ 1, 0]), EDGE_STYLE_EXTENDED, EDGE_STYLE_EXTENDED))
