import numpy as np
import math

from util import DIR, DIR2
from units import Frac
from primitive import Object2D, PlanarObject, Text
from edge import EDGE_STYLE, EDGE_ELEMENT_STYLE, _EdgeElement, Edge


class Wall(PlanarObject):
    """
    Object representing a wall.

    Walls contain edges and other 2D children.
    """

    #size = None
    #children = None
    #edges = None

    def __init__(self, size, name=None):
        self.size = np.array(size)

        self.children = []

        self._construct_edges()

        if name is None:
            self.name = type(self).__name__
        else:
            self.name = name

    def get_edge_by_direction(self, v):
        return self.edges[self._get_edge_index_by_direction(v)]

    @staticmethod
    def _get_edge_index_by_direction(v):
        if (v == DIR2.UP).all():    return 0
        if (v == DIR2.DOWN).all():  return 1
        if (v == DIR2.LEFT).all():  return 2
        if (v == DIR2.RIGHT).all(): return 3

    def render(self, config):
        self._check_corner_edge_styles_matching()

        l = Object2D()

        # TODO implement render for edge references?
        l.extend(self.edges[0].dereference().render(config)           + np.array([0, self.size[1]]))
        l.extend(self.edges[3].dereference().render(config).reverse() + np.array([self.size[0], 0]))
        l.extend(self.edges[1].dereference().render(config).reverse() + np.array([0, 0]))
        l.extend(self.edges[2].dereference().render(config)           + np.array([0, 0]))

        for child, pos, mirror_axes in self.children:
            l.extend(child.render(config).mirror(mirror_axes) + pos)

        if config.print_wall_names:
            l.append(Text(np.array([5,5]), self.name))

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

    def _check_corner_edge_styles_matching(self):
        l = [
                (DIR2.LEFT,  'begin_style', DIR2.DOWN, 'begin_style'),
                (DIR2.LEFT,  'end_style',   DIR2.UP,   'begin_style'),
                (DIR2.RIGHT, 'begin_style', DIR2.DOWN, 'end_style'),
                (DIR2.RIGHT, 'end_style',   DIR2.UP,   'end_style'),
            ]

        for d1, t1, d2, t2 in l:
            e1 = self.get_edge_by_direction(d1).dereference()
            e2 = self.get_edge_by_direction(d2).dereference()

            s1 = getattr(e1, t1)
            s2 = getattr(e2, t2)

            if not s1 in _EdgeElement.allowed_neighbour_corner_styles[s2]:
                print('ERROR: Corner edge style mismatch, rendering into error layer.')
                e1.layer = 'error'
                e2.layer = 'error'

    def _construct_edges(self):
        raise NotImplementedError('Abstract method')

    def __str__(self):
        return '[Wall "{name}" ({sizex}, {sizey})]'.format(
                name  = self.name,
                sizex = self.size[0],
                sizey = self.size[1]
            )

class WallReference():
    """
    A reference object for walls.

    Contains logic to do coordinate transformations to automatically project
    coordinates to 2D and translate children's positions when adding them to
    the target wall.

    Also stores local edge references.

    This allows to reference a subpart of a wall and use it as if it were a
    complete wall.
    """

    def __init__(self, target, pos=np.array([0,0]), size=None, mirror_children=np.array([False, False]), projection_dir=None, name=None):
        assert( (pos >= np.array([0,0])).all() )

        if size is None:
            size = target.size - pos
            assert( (size >= np.array([0,0])).all() )

        self.target = target
        self.position = pos
        self.size = size
        self.mirror_children = mirror_children
        self.projection_dir = projection_dir
        self.name = name

        self._init_edges_from_target()

    def _init_edges_from_target(self):
        self.edges = [None] * 4

        if self.position[0] == 0:
            self.edges[Wall._get_edge_index_by_direction(DIR2.LEFT)]  = self.target.get_edge_by_direction(DIR2.LEFT ).get_reference(self.position[1], self.size[1], projection_dir=DIR2.LEFT)
        if self.position[0] + self.size[0] == self.target.size[0]:
            self.edges[Wall._get_edge_index_by_direction(DIR2.RIGHT)] = self.target.get_edge_by_direction(DIR2.RIGHT).get_reference(self.position[1], self.size[1], projection_dir=DIR2.RIGHT)
        if self.position[1] == 0:
            self.edges[Wall._get_edge_index_by_direction(DIR2.DOWN)]  = self.target.get_edge_by_direction(DIR2.DOWN ).get_reference(self.position[0], self.size[0], projection_dir=DIR2.DOWN)
        if self.position[1] + self.size[1] == self.target.size[1]:
            self.edges[Wall._get_edge_index_by_direction(DIR2.UP)]    = self.target.get_edge_by_direction(DIR2.UP   ).get_reference(self.position[0], self.size[0], projection_dir=DIR2.UP)

    def get_edge_by_direction(self, v):
        if len(v) == 3 and self.projection_dir is not None:
            v = self.to_local_coords(v)
        return self.edges[Wall._get_edge_index_by_direction(v)]

    def to_local_coords(self, v):
        assert(self.projection_dir is not None)
        return DIR.project_along_axis(v, self.projection_dir)

    def add_child(self, child, pos, mirrored=np.array([False, False])):
        if len(pos) == 3 and self.projection_dir is not None:
            pos = self.to_local_coords(pos)
        pos = Frac.array_total_length(pos, self.size)
        child.set_parent(self)
        self.target.add_child(child, self.position + pos, self.mirror_children ^ mirrored)

    def get_reference(self, pos=np.array([0,0]), size=None, mirror_children=np.array([False, False]), projection_dir=None):
        if size is not None:
            assert( (pos + size <= self.size).all() )
        return WallReference(self, pos, size, self.mirror_children ^ mirror_children, projection_dir)

    def dereference(self):
        return self.target.dereference()

    def __str__(self):
        return '[WallRef "{name}" {dir}({posx}, {posy}) / ({sizex}, {sizey})] -> {target}'.format(
                posx   = self.position[0],
                posy   = self.position[1],
                sizex  = self.size[0],
                sizey  = self.size[1],
                dir    = DIR.dir_to_name(self.projection_dir) + ' ' if self.projection_dir is not None else '',
                name   = self.name,
                target = self.target
            )


class ToplessWall(Wall):
    """
    A wall template defining a side wall with one flat edge.
    """

    def _construct_edges(self):
        self.edges = []
        self.edges.append(Edge(self.size[0], DIR2.UP,    style=EDGE_ELEMENT_STYLE.FLAT).get_reference(projection_dir=DIR2.UP))
        self.edges.append(Edge(self.size[0], DIR2.DOWN,  EDGE_STYLE.FLAT,    EDGE_STYLE.FLAT).get_reference(projection_dir=DIR2.DOWN))
        self.edges.append(Edge(self.size[1], DIR2.LEFT,  EDGE_STYLE.FLAT,    EDGE_STYLE.TOOTHED).get_reference(projection_dir=DIR2.LEFT))
        self.edges.append(Edge(self.size[1], DIR2.RIGHT, EDGE_STYLE.TOOTHED, EDGE_STYLE.FLAT).get_reference(projection_dir=DIR2.RIGHT))

class ExtendedWall(Wall):
    """
    A wall template defining a cover wall with extended corners.
    """

    def _construct_edges(self):
        self.edges = []
        self.edges.append(Edge(self.size[0], DIR2.UP,    EDGE_STYLE.EXTENDED, EDGE_STYLE.EXTENDED).get_reference(projection_dir=DIR2.UP))
        self.edges.append(Edge(self.size[0], DIR2.DOWN,  EDGE_STYLE.EXTENDED, EDGE_STYLE.EXTENDED).get_reference(projection_dir=DIR2.DOWN))
        self.edges.append(Edge(self.size[1], DIR2.LEFT,  EDGE_STYLE.EXTENDED, EDGE_STYLE.EXTENDED).get_reference(projection_dir=DIR2.LEFT))
        self.edges.append(Edge(self.size[1], DIR2.RIGHT, EDGE_STYLE.EXTENDED, EDGE_STYLE.EXTENDED).get_reference(projection_dir=DIR2.RIGHT))

class SideWall(Wall):
    """
    A wall template defining a side wall.
    """

    def _construct_edges(self):
        self.edges = []
        self.edges.append(Edge(self.size[0], DIR2.UP,    EDGE_STYLE.FLAT,    EDGE_STYLE.FLAT).get_reference(projection_dir=DIR2.UP))
        self.edges.append(Edge(self.size[0], DIR2.DOWN,  EDGE_STYLE.FLAT,    EDGE_STYLE.FLAT).get_reference(projection_dir=DIR2.DOWN))
        self.edges.append(Edge(self.size[1], DIR2.LEFT,  EDGE_STYLE.FLAT,    EDGE_STYLE.TOOTHED).get_reference(projection_dir=DIR2.LEFT))
        self.edges.append(Edge(self.size[1], DIR2.RIGHT, EDGE_STYLE.TOOTHED, EDGE_STYLE.FLAT).get_reference(projection_dir=DIR2.RIGHT))

class InvSideWall(Wall):
    """
    A wall template defining a side wall with inverted toothing.
    """

    def _construct_edges(self):
        self.edges = []
        self.edges.append(Edge(self.size[0], DIR2.UP,    EDGE_STYLE.FLAT,    EDGE_STYLE.FLAT).get_reference(projection_dir=DIR2.UP))
        self.edges.append(Edge(self.size[0], DIR2.DOWN,  EDGE_STYLE.FLAT,    EDGE_STYLE.FLAT).get_reference(projection_dir=DIR2.DOWN))
        self.edges.append(Edge(self.size[1], DIR2.LEFT,  EDGE_STYLE.TOOTHED, EDGE_STYLE.FLAT).get_reference(projection_dir=DIR2.LEFT))
        self.edges.append(Edge(self.size[1], DIR2.RIGHT, EDGE_STYLE.FLAT,    EDGE_STYLE.TOOTHED).get_reference(projection_dir=DIR2.RIGHT))


class SubWall(Wall):
    """
    A wall template defining a wall used as subbox divider.
    """

    def _construct_edges(self):
        self.edges = []
        self.edges.append(Edge(self.size[0], DIR2.UP,    EDGE_STYLE.FLAT, EDGE_STYLE.FLAT).get_reference(projection_dir=DIR2.UP))
        self.edges.append(Edge(self.size[0], DIR2.DOWN,  EDGE_STYLE.FLAT, EDGE_STYLE.FLAT).get_reference(projection_dir=DIR2.DOWN))
        self.edges.append(Edge(self.size[1], DIR2.LEFT,  EDGE_STYLE.FLAT, EDGE_STYLE.FLAT).get_reference(projection_dir=DIR2.LEFT))
        self.edges.append(Edge(self.size[1], DIR2.RIGHT, EDGE_STYLE.FLAT, EDGE_STYLE.FLAT).get_reference(projection_dir=DIR2.RIGHT))
