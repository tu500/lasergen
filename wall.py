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
        """
        Get the edge lying in the specified direction.

        Returns an edge reference that automatically converts wall coordinates
        to the local edge coordinates.
        """

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
        """
        Add a PlanarObject as new child to this wall.

        If any position coordinates are given as `Frac` values they will be
        interpreted relative to this wall's size.
        """

        pos = Frac.array_total_length(pos, self.size)
        self.children.append((child, pos, mirrored))

    def get_reference(self, pos=np.array([0,0]), size=None, mirror_children=np.array([False, False]), projection_dir=None):
        """
        Construct a new reference given its offset and size relative to this
        wall.
        """

        if size is not None:
            assert( (pos + size <= self.size).all() )
        return WallReference(self, pos, size, mirror_children, projection_dir)

    def dereference(self):
        """
        Used for transparently dereferecing WallReferences. Returns self.
        """
        return self

    def _set_edgeref_default_data(self):
        """
        Set default data of edge references.
        """

        # first set projection dirs
        for d in DIR2.DIRS:
            self.get_edge_by_direction(d).projection_dir = d

        # then add counterpart references
        for d, neg_pd, pos_pd in [
                (DIR2.UP, DIR2.LEFT, DIR2.RIGHT),
                (DIR2.DOWN, DIR2.LEFT, DIR2.RIGHT),
                (DIR2.RIGHT, DIR2.DOWN, DIR2.UP),
                (DIR2.LEFT, DIR2.DOWN, DIR2.UP),
            ]:

            e = self.get_edge_by_direction(d)
            e.set_corner_counterpart(self.get_edge_by_direction(neg_pd), -1, False)
            e.set_corner_counterpart(self.get_edge_by_direction(pos_pd), 1, False)

    def _construct_edges(self):
        """
        Abstract method implemented by subclasses defining wall templates to
        construct their edges accordingly.
        """
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
        """
        Automatically add local edge references referencing the target's edges
        if the specified region extends to the respective target's edge.
        """

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
        """
        Get the edge lying in the specified direction.

        Returns an edge reference that automatically converts wall coordinates
        to the local edge coordinates.

        Note that the edges returned are specific to this wall reference and
        may differ from those of the target, as this reference may specifiy a
        subregion of the target wall.
        """

        if len(v) == 3 and self.projection_dir is not None:
            v = self.to_local_coords(v)
        return self.edges[Wall._get_edge_index_by_direction(v)]

    def to_local_coords(self, v):
        """
        Convert external 3D coordinates to local 2D wall coordinates according
        to the configured projection dir.

        An error is raised if no projection dir is configured.
        """

        assert(self.projection_dir is not None)
        return DIR.project_along_axis(v, self.projection_dir)

    def add_child(self, child, pos, mirrored=np.array([False, False])):
        """
        Add a PlanarObject as new child to the target wall.

        The given position is relative to this wall reference's coordinate
        system and will be automatically converted to the one of the target
        wall. This also applies to coordinate values specified as `Frac`
        values.

        If possible and applicable the child's parameters will be converted,
        too.
        """

        if len(pos) == 3 and self.projection_dir is not None:
            pos = self.to_local_coords(pos)
        pos = Frac.array_total_length(pos, self.size)
        child.set_parent(self, pos)
        self.target.add_child(child, self.position + pos, self.mirror_children ^ mirrored)

    def get_reference(self, pos=np.array([0,0]), size=None, mirror_children=np.array([False, False]), projection_dir=None):
        """
        Construct a new reference given its offset and size relative to this
        wall reference.
        """

        if size is not None:
            assert( (pos + size <= self.size).all() )
        return WallReference(self, pos, size, self.mirror_children ^ mirror_children, projection_dir)

    def dereference(self):
        """
        Returns the eventual wall object this reference points to.
        """
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
        self.edges.append(Edge(self.size[0], DIR2.UP,    style=EDGE_ELEMENT_STYLE.FLAT).get_reference())
        self.edges.append(Edge(self.size[0], DIR2.DOWN,  EDGE_STYLE.FLAT,    EDGE_STYLE.FLAT).get_reference())
        self.edges.append(Edge(self.size[1], DIR2.LEFT,  EDGE_STYLE.FLAT,    EDGE_STYLE.TOOTHED).get_reference())
        self.edges.append(Edge(self.size[1], DIR2.RIGHT, EDGE_STYLE.TOOTHED, EDGE_STYLE.FLAT).get_reference())
        self._set_edgeref_default_data()

class InvToplessWall(Wall):
    """
    A wall template defining a side wall with one flat edge.
    """

    def _construct_edges(self):
        self.edges = []
        self.edges.append(Edge(self.size[0], DIR2.UP,    style=EDGE_ELEMENT_STYLE.FLAT).get_reference())
        self.edges.append(Edge(self.size[0], DIR2.DOWN,  EDGE_STYLE.FLAT,    EDGE_STYLE.FLAT).get_reference())
        self.edges.append(Edge(self.size[1], DIR2.LEFT,  EDGE_STYLE.TOOTHED, EDGE_STYLE.FLAT).get_reference())
        self.edges.append(Edge(self.size[1], DIR2.RIGHT, EDGE_STYLE.FLAT,    EDGE_STYLE.TOOTHED).get_reference())
        self._set_edgeref_default_data()

class ExtendedWall(Wall):
    """
    A wall template defining a cover wall with extended corners.
    """

    def _construct_edges(self):
        self.edges = []
        self.edges.append(Edge(self.size[0], DIR2.UP,    EDGE_STYLE.EXTENDED, EDGE_STYLE.EXTENDED).get_reference())
        self.edges.append(Edge(self.size[0], DIR2.DOWN,  EDGE_STYLE.EXTENDED, EDGE_STYLE.EXTENDED).get_reference())
        self.edges.append(Edge(self.size[1], DIR2.LEFT,  EDGE_STYLE.EXTENDED, EDGE_STYLE.EXTENDED).get_reference())
        self.edges.append(Edge(self.size[1], DIR2.RIGHT, EDGE_STYLE.EXTENDED, EDGE_STYLE.EXTENDED).get_reference())
        self._set_edgeref_default_data()

class SideWall(Wall):
    """
    A wall template defining a side wall.
    """

    def _construct_edges(self):
        self.edges = []
        self.edges.append(Edge(self.size[0], DIR2.UP,    EDGE_STYLE.FLAT,    EDGE_STYLE.FLAT).get_reference())
        self.edges.append(Edge(self.size[0], DIR2.DOWN,  EDGE_STYLE.FLAT,    EDGE_STYLE.FLAT).get_reference())
        self.edges.append(Edge(self.size[1], DIR2.LEFT,  EDGE_STYLE.FLAT,    EDGE_STYLE.TOOTHED).get_reference())
        self.edges.append(Edge(self.size[1], DIR2.RIGHT, EDGE_STYLE.TOOTHED, EDGE_STYLE.FLAT).get_reference())
        self._set_edgeref_default_data()

class InvSideWall(Wall):
    """
    A wall template defining a side wall with inverted toothing.
    """

    def _construct_edges(self):
        self.edges = []
        self.edges.append(Edge(self.size[0], DIR2.UP,    EDGE_STYLE.FLAT,    EDGE_STYLE.FLAT).get_reference())
        self.edges.append(Edge(self.size[0], DIR2.DOWN,  EDGE_STYLE.FLAT,    EDGE_STYLE.FLAT).get_reference())
        self.edges.append(Edge(self.size[1], DIR2.LEFT,  EDGE_STYLE.TOOTHED, EDGE_STYLE.FLAT).get_reference())
        self.edges.append(Edge(self.size[1], DIR2.RIGHT, EDGE_STYLE.FLAT,    EDGE_STYLE.TOOTHED).get_reference())
        self._set_edgeref_default_data()


class SubWall(Wall):
    """
    A wall template defining a wall used as subbox divider.
    """

    def _construct_edges(self):
        self.edges = []
        self.edges.append(Edge(self.size[0], DIR2.UP,    EDGE_STYLE.FLAT, EDGE_STYLE.FLAT).get_reference())
        self.edges.append(Edge(self.size[0], DIR2.DOWN,  EDGE_STYLE.FLAT, EDGE_STYLE.FLAT).get_reference())
        self.edges.append(Edge(self.size[1], DIR2.LEFT,  EDGE_STYLE.FLAT, EDGE_STYLE.FLAT).get_reference())
        self.edges.append(Edge(self.size[1], DIR2.RIGHT, EDGE_STYLE.FLAT, EDGE_STYLE.FLAT).get_reference())
        self._set_edgeref_default_data()
