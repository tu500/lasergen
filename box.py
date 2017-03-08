import numpy as np

from util import DIR, DIR2
from units import Rel
from edge import CutoutEdge, EDGE_STYLE
from wall import Wall, ToplessWall, InvToplessWall, ExtendedWall, SideWall, InvSideWall, SubWall

class Box():
    """
    Object representing a box.

    References its walls and possibly subboxes.
    """

    def __init__(self, width, height, depth, name=None):
        self.size = [width, height, depth]
        self.abs_size = np.array([None, None, None])

        self.subboxes = []
        self.position = np.array([0,0,0])

        if name is None:
            self.name = type(self).__name__
        else:
            self.name = name

    def subdivide(self, direction, sizes, names=None):
        """
        Subdivide this box along given direction.

        Sizes can be specified as non-absolute values, automatically summing up
        and calculating relative sizes. This process is inspired by CSS-like
        star notation.

        Given values may be absolute values, relative values (`Rel` objects) or
        `None` (meaning sum of its children).

        Absolute values will be calculated by calling `.configure`. Make sure
        to call this after setting up all subboxes and before using any walls.

        The subboxes' names will be assigned from the given list of names.
        Alternatively, names may be specified in the `sizes` parameter as a
        tuple of `(size, name)` for each subbox.

        A name of `None` will be replaced with a default name. Also default
        names will be generated if no names are provided.

        Returns a list of the newly added subboxes.
        """

        assert self.subboxes == []

        def normalize_size_entry(index, entry):

            default_name = '{}.DIR{}{}'.format(
                    self.name,
                    DIR.dir_to_axis_name(direction),
                    index
                )

            if isinstance(entry, tuple):
                if entry[1] is not None:
                    return entry
                else:
                    return (entry, default_name)
            else:
                return (entry, default_name)

        if names is not None:
            sizes_and_names = (normalize_size_entry(*t) for t in enumerate(zip(sizes, names)))
        else:
            sizes_and_names = (normalize_size_entry(*t) for t in enumerate(sizes))

        if (direction == DIR.RIGHT).all():
            self.subboxes = [SubBox(size, 'ref', 'ref', name=name) for size, name in sizes_and_names]
        elif (direction == DIR.UP).all():
            self.subboxes = [SubBox('ref', size, 'ref', name=name) for size, name in sizes_and_names]
        elif (direction == DIR.FRONT).all():
            self.subboxes = [SubBox('ref', 'ref', size, name=name) for size, name in sizes_and_names]

        return self.subboxes


    def get_wall_by_direction(self, v):
        """
        Get the wall lying in the specified direction.

        Returns a wall reference that automatically converts box coordinates to
        the local wall coordinates.
        """

        return self.walls[self._get_wall_index_by_direction(v)]

    @staticmethod
    def _get_wall_index_by_direction(v):
        if (v == DIR.UP).all():    return 0
        if (v == DIR.DOWN).all():  return 1
        if (v == DIR.LEFT).all():  return 2
        if (v == DIR.RIGHT).all(): return 3
        if (v == DIR.FRONT).all(): return 4
        if (v == DIR.BACK).all():  return 5


    def render(self, config):
        """
        Render this box's and all its subboxes' walls into a list of `Object2D`s.
        """

        # uniquify wall references, keep order for deterministic output
        seen = set()
        walls = [x for x,_,_ in self._gather_walls(config) if not (x in seen or seen.add(x))]
        return [w.render(config) for w in walls]

    def _gather_walls(self, config):
        """
        Get a list of this box and its subboxes' walls, their positions and
        directions.
        """

        s = []

        for d in DIR.DIRS:

            wall = self.get_wall_by_direction(d)

            if not wall:
                continue

            position = self.position + d * config.wall_thickness/2

            if DIR.is_axis(d):
                position = position + d * self.abs_size

            j, k = DIR.perpendicular_axes(d)
            to = wall.get_total_offset()
            position -= j * DIR2.project_along_axis(to, wall.to_local_coords(k))
            position -= k * DIR2.project_along_axis(to, wall.to_local_coords(j))

            s.append((wall.dereference(), position, d))


        for c in self.subboxes:
            s.extend(c._gather_walls(config))

        return s


    def configure(self, config):
        """
        Calculate absolute sizes for this box and its subboxes.

        Make sure to call this after setting up all subboxes and before using
        any walls.
        """

        self._configure_rec(config)
        self._construct_rec(config)

    def _configure_rec(self, config):
        """
        Recursive implementation of configure.

        Follows a bottom-up approach.
        """

        self.abs_size = np.array([None, None, None])

        for c in self.subboxes:
            c._configure_rec(config)


        # dimensions
        for i in range(3):

            sum_abs_size, sum_rel_size, unit_length, ref_size = self._get_sum(config)

            # fixed absolute size configured?
            if self._has_absolute_width_configured(i):
                self.abs_size[i] = self.size[i]

            # take absolute size from bound children
            if ref_size[i] is not None:
                assert self.abs_size[i] is None or ref_size[i] == self.abs_size[i]
                self.abs_size[i] = ref_size[i]

            # calculate unit_length from own size
            if self.abs_size[i] is not None and sum_rel_size[i] != Rel(0):
                assert self.abs_size[i] >= sum_abs_size[i]
                new_ul = sum_rel_size[i].unit_length_from_total(self.size[i] - sum_abs_size[i])

                if unit_length[i] is not None:
                    assert new_ul == unit_length[i]

                unit_length[i] = new_ul


            # if unit_length is available update unknown subbox sizes
            if unit_length[i] is not None:

                for c in self.subboxes:
                    if isinstance(c.size[i], Rel) and c.abs_size[i] is None:
                        c._set_absolute_size(c.size[i].total_length_from_unit(unit_length[i]), i, config)
                        #sum_size[i] += t


            sum_size, unknown_children_count = self._get_final_sum(config)


            if self.size[i] is None:
                # all children's sizes must be known
                assert unknown_children_count[i] == 0

                # own size must be known somehow
                assert sum_size[i] is not None or ref_size[i] is not None

                if sum_size[i] is None:
                    self.abs_size[i] = ref_size[i] # should be a NOP
                elif ref_size[i] is None:
                    self.abs_size[i] = sum_size[i]
                else:
                    assert ref_size[i] == sum_size[i]
                    self.abs_size[i] = sum_size[i]

            elif self.size[i] == 'ref':
                if unknown_children_count[i] == 0 and sum_size[i] is not None:
                    self.abs_size[i] = sum_size[i]
                else:
                    # there are relative sized subboxes, but the unit length is unknown
                    # or there aren't any children
                    pass

            elif isinstance(self.size[i], Rel):
                if unknown_children_count[i] == 0 and sum_size[i] is not None:
                    self.abs_size[i] = sum_size[i]
                else:
                    # there are relative sized subboxes, but the unit length is unknown
                    # or there aren't any children
                    pass

            elif self._has_absolute_width_configured(i):
                # all children's sizes must be known, this is known implicitly
                assert unknown_children_count[i] == 0

                if self.abs_size[i] is not None:
                    assert self.abs_size[i] == self.size[i]
                if sum_size[i] is not None:
                    assert sum_size[i] == self.size[i]
                self.abs_size[i] = self.size[i]


            # update bound subbox sizes
            if self.abs_size[i] is not None:

                for c in self.subboxes:
                    if c.size[i] == 'ref' and c.abs_size[i] is None:
                        c._set_absolute_size(self.abs_size[i], i, config)

    def _get_sum(self, config):
        """
        Internal, for configure step.

        Sum up the children's configured and already calculated sizes and
        assert some restrictions.
        """

        # sum of all absolute configured children (size is int, float or None) plus subwalls
        sum_abs_size = [0, 0, 0]
        # (relative) sum of all relative configured children
        sum_rel_size = [Rel(0), Rel(0), Rel(0)]
        # unit length taken from relative configured children, all must match, None if unknown
        unit_length = [None, None, None]
        # absolute size taken from reference configured children, all must match, None if unknown
        ref_size = [None, None, None]

        for i in range(3):
            non_ref_children_count = sum(1 for c in self.subboxes if c.size[i] != 'ref')
            if non_ref_children_count > 1:
                sum_abs_size[i] += (non_ref_children_count - 1) * config.subwall_thickness

        for c in self.subboxes:

            for i in range(3):

                assert not (c.size[i] is None and c.abs_size[i] is None)

                if c.size[i] is None:
                    assert c.abs_size[i] is not None
                    #sum_size[i] += c.abs_size[i]
                    sum_abs_size[i] += c.abs_size[i]

                elif c.size[i] == 'ref':
                    if c.abs_size[i] is not None:
                        assert ref_size[i] is None or ref_size[i] == c.abs_size[i]
                        ref_size[i] = c.abs_size[i]

                elif isinstance(c.size[i], Rel):
                    if c.abs_size[i] is None:
                        sum_rel_size[i] += c.size[i]
                    else:
                        #sum_size[i] += c.abs_size[i]

                        sum_rel_size[i] += c.size[i]
                        new_ul = c.size[i].unit_length_from_total(c.abs_size[i])
                        assert unit_length[i] is None or new_ul == unit_length[i]
                        unit_length[i] = new_ul

                elif c._has_absolute_width_configured(i):
                    assert c.abs_size[i] is not None
                    #sum_size[i] += c.abs_size[i]
                    sum_abs_size[i] += c.abs_size[i]

        return sum_abs_size, sum_rel_size, unit_length, ref_size

    def _set_absolute_size(self, value, i, config):
        """
        Internal, for configure step.

        Top-down approach for setting now known sizes for subboxes.
        """

        assert isinstance(self.size[i], Rel) or self.size[i] == 'ref'
        assert self.abs_size[i] is None

        self.abs_size[i] = value


        # update subboxes

        if not self.subboxes:
            return

        sum_abs_size, sum_rel_size, unit_length, ref_size = self._get_sum(config)

        assert unit_length[i] is None
        assert ref_size[i] is None

        if sum_rel_size[i] != Rel(0):
            assert self.abs_size[i] >= sum_abs_size[i]
            unit_length[i] = sum_rel_size[i].unit_length_from_total(self.abs_size[i] - sum_abs_size[i])

        for c in self.subboxes:
            if c.abs_size[i] is None:
                if isinstance(c.size[i], Rel):
                    c._set_absolute_size(c.size[i].total_length_from_unit(unit_length[i]), i, config)
                elif c.size[i] == 'ref':
                    c._set_absolute_size(value, i, config)
                else:
                    assert False

    def _has_absolute_width_configured(self, i):
        """
        Internal, for configure step.
        """

        return isinstance(self.size[i], int) or isinstance(self.size[i], float)

    def _get_final_sum(self, config):
        """
        Internal, for configure step.

        Sum up the total sum all children, also considering subwall thicknesses.
        """

        # sum of final size of all non-ref children plus subwalls, None if there are none (with known size)
        sum_size = [None, None, None]
        # number of still unknown children
        unknown_children_count = [0, 0, 0]

        for i in range(3):

            unknown_children_count[i] = sum(1 for c in self.subboxes
                    if c.abs_size[i] is None
                    and c.size[i] != 'ref'
                )

            non_ref_children_count = sum(1 for c in self.subboxes if c.size[i] != 'ref')
            if non_ref_children_count > 1:
                subwall_sum = (non_ref_children_count - 1) * config.subwall_thickness
            else:
                subwall_sum = 0

            l = [c.abs_size[i] for c in self.subboxes
                    if c.abs_size[i] is not None
                    and c.size[i] != 'ref'
                ]

            if l:
                sum_size[i] = sum(l) + subwall_sum

        return sum_size, unknown_children_count


    def _construct_rec(self, config):
        """
        Recursive implementation of construct.

        Construct the boxes' walls and subwalls.
        """

        self._construct_walls()
        self._set_subbox_positions(config)
        self._construct_subwalls(config)

        for c in self.subboxes:
            c._construct_rec(config)

    def _construct_walls(self):
        """
        Defined for box templates. Use to automatically construct walls for
        root boxes.
        """

        raise NotImplementedError('Abstract method')

    def _set_subbox_positions(self, config):
        """
        Set absolute 3D space coordinates of this subbox's origin.
        """

        cur_pos = self.position.copy()

        for c in self.subboxes:

            c.position = cur_pos

            for i, d in enumerate(DIR.AXES):

                if c.size[i] != 'ref':
                    cur_pos = cur_pos + d * (c.abs_size[i] + config.wall_thickness)

    def _construct_subwalls(self, config):
        """
        Construct subwalls and add to own subboxes.

        Setup subbox wall references, add cutout edges to own walls.
        """

        # TODO use subbox positions to simplify this code

        if not self.subboxes:
            return

        cur_pos = np.array([0.,0.,0.])
        cur_wall_refs = [self.get_wall_by_direction(-d) for d in DIR.AXES]

        # assert subdivision only along one axis
        non_ref_indices = [i for i,s in enumerate(self.subboxes[0].size) if s != 'ref']
        assert len(non_ref_indices) == 1
        working_axis_index = non_ref_indices[0]
        working_axis= DIR.AXES[working_axis_index]

        for box_index, c in enumerate(self.subboxes):

            c.walls = [None] * 6

            n_pos = cur_pos.copy()
            n_walls = cur_wall_refs.copy()

            # sorting ensures other wallrefs are set before constructing a new
            # subwall, thus being able to set the wallrefs' edge references to
            # the new CutoutEdges
            for i, d in sorted(enumerate(DIR.AXES), key=lambda x: c.size[x[0]] != 'ref'):

                # assert subdivision only along one axis
                if i == working_axis_index:
                    assert c.size[i] != 'ref'
                else:
                    assert c.size[i] == 'ref'

                pos_index = self._get_wall_index_by_direction(d)
                neg_index = self._get_wall_index_by_direction(-d)

                # needed because some of the surrounding walls may not be references / have projection_dirs
                to_local_coords = lambda v: DIR.project_along_axis(v, d)

                # set negative wall
                r = cur_wall_refs[i]
                if r is not None:
                    c.walls[neg_index] = r.get_reference(to_local_coords(cur_pos), to_local_coords(c.abs_size), projection_dir=-d)
                else:
                    c.walls[neg_index] = None

                # set positive wall, reference parent's wall for subbox with 'ref' size or the last subbox
                if c.size[i] == 'ref' or box_index == len(self.subboxes) - 1:

                    r = self.get_wall_by_direction(d)
                    if r is not None:
                        c.walls[pos_index] = r.get_reference(to_local_coords(cur_pos), to_local_coords(c.abs_size), projection_dir=d)
                    else:
                        c.walls[pos_index] = None

                else:

                    # need to create a new subwall

                    ref_wall = self.get_wall_by_direction(-d)
                    name = '{}.SUB{}{}'.format(self.name, DIR.dir_to_axis_name(d), box_index)
                    r = SubWall(ref_wall.size, name=name)

                    # add cutout edges
                    j, k = [DIR.AXES[a] for a in range(3) if a != i]

                    for target_dir, other_dir in [(j,k), (-j,k), (k,j), (-k,j)]:

                        target_wall = self.get_wall_by_direction(target_dir)
                        if target_wall is not None:

                            # create CutoutEdge object
                            l = ref_wall.to_local_coords(other_dir).dot(ref_wall.size) # size of reference wall in direction other_dir
                            e = CutoutEdge(l, target_wall.to_local_coords(d), EDGE_STYLE.TOOTHED, EDGE_STYLE.TOOTHED)
                            target_wall.add_child(e, cur_pos + c.abs_size[i] * d)

                            # set counterpart between new CutoutEdge and corresponding edge of new SubWall
                            e.set_counterpart(r.get_edge_by_direction(to_local_coords(target_dir)).dereference())

                            # add edge reference in working direction to the wall reference perpendicular to working direction
                            child_target_wall_ref = c.get_wall_by_direction(target_dir)
                            child_target_wall_ref.edges[Wall._get_edge_index_by_direction(child_target_wall_ref.to_local_coords(d))] = e.get_reference()

                    # add wall reference in working direction to current sobbox
                    c.walls[pos_index] = r.get_reference(to_local_coords(cur_pos), to_local_coords(c.abs_size), projection_dir=d)

                    cur_pos[i] += c.abs_size[i] + config.subwall_thickness
                    cur_wall_refs[i] = r

            # add edge reference in negative working direction to the wall references perpendicular to working direction
            if box_index > 0:

                for target_dir in DIR.perpendicular_dirs(working_axis):

                    local_target_dir = DIR.project_along_axis(target_dir, working_axis)
                    cutout_edge = cur_wall_refs[working_axis_index].get_edge_by_direction(local_target_dir).dereference()

                    child_target_wall_ref = c.get_wall_by_direction(target_dir)
                    edge_index = Wall._get_edge_index_by_direction(child_target_wall_ref.to_local_coords(-working_axis))
                    child_target_wall_ref.edges[edge_index] = cutout_edge.get_reference()

            c._set_wallref_names()


    def _set_wallref_default_data(self):
        """
        Set default data of walls, common to all box templates.
        """

        self._set_wallref_projection_dirs()
        self._set_wall_names()
        self._set_wallref_names()
        self._set_egde_counterparts()

    def _set_wallref_projection_dirs(self):
        """
        Set all wall refs' projection dirs.
        """

        for d in DIR.DIRS:
            wref = self.get_wall_by_direction(d)

            if wref is not None:
                wref.projection_dir = d

    def _set_wall_names(self):
        """
        Set all walls' names to default values.
        """

        for d in DIR.DIRS:
            wref = self.get_wall_by_direction(d)

            if wref is not None:
                w = wref.dereference()
                w.name = self.name + '.' + DIR.dir_to_name(d)

    def _set_wallref_names(self):
        """
        Set all wall ref's names to default values.

        Separate from `_set_wall_names` because this is used for subboxes too.
        """

        for d in DIR.DIRS:
            wref = self.get_wall_by_direction(d)

            if wref is not None:
                wref.name = self.name + '.' + DIR.dir_to_name(d)

    def _set_egde_counterparts(self):
        """
        Set all walls' edges' counterparts.

        Needs setup projection dirs.
        """

        for wall_dir in DIR.DIRS:

            for edge_dir in DIR.perpendicular_dirs(wall_dir):
                if self.get_wall_by_direction(wall_dir) is not None and self.get_wall_by_direction(edge_dir) is not None:
                    self.get_wall_by_direction(wall_dir).get_edge_by_direction(edge_dir).set_counterpart(
                            self.get_wall_by_direction(edge_dir).get_edge_by_direction(wall_dir).dereference(),
                            False
                        )


    def __str__(self):
        return '[Box "{name}" ({sx}, {sy}, {sz}) / ({asx}, {asy}, {asz})]'.format(
                name = self.name,
                sx = self.size[0],
                sy = self.size[1],
                sz = self.size[2],
                asx = self.abs_size[0],
                asy = self.abs_size[1],
                asz = self.abs_size[2],
            )


class ClosedBox(Box):
    """
    A box template for a completely closed box.
    """

    def _construct_walls(self):
        self.walls = []
        self.walls.append(InvSideWall(  DIR.project_along_axis(self.abs_size, DIR.UP)    ).get_reference())
        self.walls.append(SideWall(     DIR.project_along_axis(self.abs_size, DIR.DOWN)  ).get_reference())
        self.walls.append(InvSideWall(  DIR.project_along_axis(self.abs_size, DIR.LEFT)  ).get_reference())
        self.walls.append(SideWall(     DIR.project_along_axis(self.abs_size, DIR.RIGHT) ).get_reference())
        self.walls.append(ExtendedWall( DIR.project_along_axis(self.abs_size, DIR.FRONT) ).get_reference())
        self.walls.append(ExtendedWall( DIR.project_along_axis(self.abs_size, DIR.BACK)  ).get_reference())
        self._set_wallref_default_data()


class ToplessBox(Box):
    """
    A box template for a box with one open side.
    """

    def _construct_walls(self):
        self.walls = []
        self.walls.append(InvToplessWall( DIR.project_along_axis(self.abs_size, DIR.UP)    ).get_reference())
        self.walls.append(ToplessWall(    DIR.project_along_axis(self.abs_size, DIR.DOWN)  ).get_reference())
        self.walls.append(InvToplessWall( DIR.project_along_axis(self.abs_size, DIR.LEFT)  ).get_reference())
        self.walls.append(ToplessWall(    DIR.project_along_axis(self.abs_size, DIR.RIGHT) ).get_reference())
        self.walls.append(None)
        self.walls.append(ExtendedWall(   DIR.project_along_axis(self.abs_size, DIR.BACK)  ).get_reference())
        self._set_wallref_default_data()


class SubBox(Box):
    """
    A box object leaving out some root box logic.
    """

    def __init__(self, width, height, depth, name=None):
        self.size = [width, height, depth]
        self.abs_size = np.array([None, None, None])

        self.subboxes = []

        if name is None:
            self.name = type(self).__name__
        else:
            self.name = name

    def _construct_rec(self, config):
        # subboxes don't have a `_construct_walls` method
        self._set_subbox_positions(config)
        self._construct_subwalls(config)

        for c in self.subboxes:
            c._construct_rec(config)
