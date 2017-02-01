import numpy as np

from wall import ToplessWall, ExtendedWall, SideWall
from util import DIR
from units import Rel

class Box():
    def __init__(self, width, height, depth):
        self.size = [width, height, depth]
        self.abs_size = np.array([None, None, None])

        self.subboxes = []

    def subdivide(self, direction, *sizes):
        assert(self.subboxes == [])

        if (direction == DIR.RIGHT).all():
            self.subboxes = [SubBox(size, 'ref', 'ref') for size in sizes]
        elif (direction == DIR.UP).all():
            self.subboxes = [SubBox('ref', size, 'ref') for size in sizes]
        elif (direction == DIR.FRONT).all():
            self.subboxes = [SubBox('ref', 'ref', size) for size in sizes]

    def render(self, config):
        # uniquify wall references, keep order for deterministic output
        seen = set()
        walls = [x for x in self._gather_walls() if not (x in seen or seen.add(x))]
        return [w.render(config) for w in walls]

    def _gather_walls(self):
        s = [w.dereference() for w in self.walls if w is not None]

        for c in self.subboxes:
            s.extend(c._gather_walls())

        return s

    def construct(self):
        self._construct_walls()

        for c in self.subboxes:
            c.construct()

    def configure(self, config):

        self.abs_size = np.array([None, None, None])

        for c in self.subboxes:
            c.configure(config)

        # dimensions
        for i in range(3):

            sum_abs_size, sum_rel_size, unit_length, ref_size = self._get_sum(config)

            # fixed absolute size configured?
            if self._has_absolute_width_configured(i):
                self.abs_size[i] = self.size[i]

            # take absolute size from bound children
            if ref_size[i] is not None:
                assert(self.abs_size[i] is None or ref_size[i] == self.abs_size[i])
                self.abs_size[i] = ref_size[i]

            # calculate unit_length from own size
            if self.abs_size[i] is not None and sum_rel_size[i] != Rel(0):
                assert(self.abs_size[i] >= sum_abs_size[i])
                new_ul = sum_rel_size[i].unit_length_from_total(self.size[i] - sum_abs_size[i])

                if unit_length[i] is not None:
                    assert(new_ul == unit_length[i])

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
                assert(unknown_children_count[i] == 0)

                # own size must be known somehow
                assert(sum_size[i] is not None or ref_size[i] is not None)

                if sum_size[i] is None:
                    self.abs_size[i] = ref_size[i] # should be a NOP
                elif ref_size[i] is None:
                    self.abs_size[i] = sum_size[i]
                else:
                    assert(ref_size[i] == sum_size[i])
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
                assert(unknown_children_count[i] == 0)

                if self.abs_size[i] is not None:
                    assert(self.abs_size[i] == self.size[i])
                if sum_size[i] is not None:
                    assert(sum_size[i] == self.size[i])
                self.abs_size[i] = self.size[i]


            # update bound subbox sizes
            if self.abs_size[i] is not None:

                for c in self.subboxes:
                    if c.size[i] == 'ref' and c.abs_size[i] is None:
                        c._set_absolute_size(self.abs_size[i], i, config)

    def _get_sum(self, config):

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

                assert(not (c.size[i] is None and c.abs_size[i] is None))

                if c.size[i] is None:
                    assert(c.abs_size[i] is not None)
                    #sum_size[i] += c.abs_size[i]
                    sum_abs_size[i] += c.abs_size[i]

                elif c.size[i] == 'ref':
                    if c.abs_size[i] is not None:
                        assert(ref_size[i] is None or ref_size[i] == c.abs_size[i])
                        ref_size[i] = c.abs_size[i]

                elif isinstance(c.size[i], Rel):
                    if c.abs_size[i] is None:
                        sum_rel_size[i] += c.size[i]
                    else:
                        #sum_size[i] += c.abs_size[i]

                        sum_rel_size[i] += c.size[i]
                        new_ul = c.size[i].unit_length_from_total(c.abs_size[i])
                        assert(unit_length[i] is None or new_ul == unit_length[i])
                        unit_length[i] = new_ul

                elif c._has_absolute_width_configured(i):
                    assert(c.abs_size[i] is not None)
                    #sum_size[i] += c.abs_size[i]
                    sum_abs_size[i] += c.abs_size[i]

        return sum_abs_size, sum_rel_size, unit_length, ref_size

    def _set_absolute_size(self, value, i, config):

        assert(isinstance(self.size[i], Rel) or self.size[i] == 'ref')
        assert(self.abs_size[i] is None)

        self.abs_size[i] = value


        # update subboxes

        if not self.subboxes:
            return

        sum_abs_size, sum_rel_size, unit_length, ref_size = self._get_sum(config)

        assert(unit_length[i] is None)
        assert(ref_size[i] is None)

        if sum_rel_size[i] != Rel(0):
            assert(self.abs_size[i] >= sum_abs_size[i])
            unit_length[i] = sum_rel_size[i].unit_length_from_total(self.abs_size[i] - sum_abs_size[i])

        for c in self.subboxes:
            if c.abs_size[i] is None:
                if isinstance(c.size[i], Rel):
                    c._set_absolute_size(c.size[i].total_length_from_unit(unit_length[i]), i, config)
                elif c.size[i] == 'ref':
                    c._set_absolute_size(value, i, config)
                else:
                    assert(False)

    def _has_absolute_width_configured(self, i):
        return isinstance(self.size[i], int) or isinstance(self.size[i], float)

    def _get_final_sum(self, config):

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


    def get_wall_by_direction(self, v):
        if (v == DIR.UP).all():    return self.walls[0]
        if (v == DIR.DOWN).all():  return self.walls[1]
        if (v == DIR.LEFT).all():  return self.walls[2]
        if (v == DIR.RIGHT).all(): return self.walls[3]
        if (v == DIR.FRONT).all(): return self.walls[4]
        if (v == DIR.BACK).all():  return self.walls[5]

    def _construct_walls(self):
        raise Exception("Abstract method")

class ToplessBox(Box):
    def _construct_walls(self):
        self.walls = []
        self.walls.append(SideWall(self.size[0], self.size[2]).get_reference(projection_dir=DIR.UP))
        self.walls.append(SideWall(self.size[1], self.size[2]).get_reference(projection_dir=DIR.DOWN))
        self.walls.append(SideWall(self.size[0], self.size[2]).get_reference(projection_dir=DIR.LEFT))
        self.walls.append(SideWall(self.size[1], self.size[2]).get_reference(projection_dir=DIR.RIGHT))
        self.walls.append(ExtendedWall(self.size[0], self.size[1]).get_reference(projection_dir=DIR.FRONT))
        self.walls.append(ExtendedWall(self.size[0], self.size[1]).get_reference(projection_dir=DIR.BACK))

class ClosedBox(Box):
    def _construct_walls(self):
        self.walls = []
        self.walls.append(ToplessWall(self.size[0], self.size[2]).get_reference(projection_dir=DIR.UP))
        self.walls.append(ToplessWall(self.size[1], self.size[2]).get_reference(projection_dir=DIR.DOWN))
        self.walls.append(ToplessWall(self.size[0], self.size[2]).get_reference(projection_dir=DIR.LEFT))
        self.walls.append(ToplessWall(self.size[1], self.size[2]).get_reference(projection_dir=DIR.RIGHT))
        self.walls.append(None)
        self.walls.append(ExtendedWall(self.size[0], self.size[1]).get_reference(projection_dir=DIR.BACK))


class SubBox(Box):
    def __init__(self, width, height, depth):
        self.size = [width, height, depth]
        self.abs_size = np.array([None, None, None])

        self.subboxes = []
