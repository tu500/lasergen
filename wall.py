import numpy as np
import math

from util import DIR, DIR2, project_along_axis
from units import Frac
from primitive import Object2D, PlanarObject, Text
from edge import EDGE_STYLE, Edge


class Wall(PlanarObject):
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

    def __str__(self):
        return '[Wall "{name}" ({sizex}, {sizey})]'.format(
                name  = self.name,
                sizex = self.size[0],
                sizey = self.size[1]
            )

class WallReference():

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
        return project_along_axis(v, self.projection_dir)

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

class InvSideWall(Wall):
    def _construct_edges(self):
        self.edges = []
        self.edges.append(Edge(self.size[0], DIR.UP[:2],    EDGE_STYLE.FLAT,    EDGE_STYLE.FLAT).get_reference(projection_dir=DIR2.UP))
        self.edges.append(Edge(self.size[0], DIR.DOWN[:2],  EDGE_STYLE.FLAT,    EDGE_STYLE.FLAT).get_reference(projection_dir=DIR2.DOWN))
        self.edges.append(Edge(self.size[1], DIR.LEFT[:2],  EDGE_STYLE.TOOTHED, EDGE_STYLE.FLAT).get_reference(projection_dir=DIR2.LEFT))
        self.edges.append(Edge(self.size[1], DIR.RIGHT[:2], EDGE_STYLE.FLAT,    EDGE_STYLE.TOOTHED).get_reference(projection_dir=DIR2.RIGHT))


class SubWall(Wall):
    def _construct_edges(self):
        self.edges = []
        self.edges.append(Edge(self.size[0], DIR.UP[:2],    EDGE_STYLE.FLAT, EDGE_STYLE.FLAT).get_reference(projection_dir=DIR2.UP))
        self.edges.append(Edge(self.size[0], DIR.DOWN[:2],  EDGE_STYLE.FLAT, EDGE_STYLE.FLAT).get_reference(projection_dir=DIR2.DOWN))
        self.edges.append(Edge(self.size[1], DIR.LEFT[:2],  EDGE_STYLE.FLAT, EDGE_STYLE.FLAT).get_reference(projection_dir=DIR2.LEFT))
        self.edges.append(Edge(self.size[1], DIR.RIGHT[:2], EDGE_STYLE.FLAT, EDGE_STYLE.FLAT).get_reference(projection_dir=DIR2.RIGHT))
