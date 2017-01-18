from wall import ToplessWall, ExtendedWall, SideWall
from util import DIR
from units import Rel

DIRECTION_X = 0
DIRECTION_Y = 1
DIRECTION_Z = 2

class Box():
    def __init__(self, width, height, depth):
        self.size = [width, height, depth]
        self.abs_size = [None, None, None]

        self._construct_walls()
        self.subboxes = []

    def subdivide(self, direction, *sizes):
        assert(self.subboxes == [])

        if direction == 0:
            self.subboxes = [SubBox(size, 'ref', 'ref') for size in sizes]
        elif direction == 1:
            self.subboxes = [SubBox('ref', size, 'ref') for size in sizes]
        elif direction == 2:
            self.subboxes = [SubBox('ref', 'ref', size) for size in sizes]

    def render(self, config):
        return [w.render(config) for w in self.walls if w is not None]

    def configure(self, config):

        self.abs_size = [None, None, None]

        for c in self.subboxes:
            c.configure(config)

        # dimensions
        for i in range(3):

            sum_abs_size, sum_rel_size, unit_length, ref_size = self._get_sum()

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
                        c._set_absolute_size(c.size[i].total_length_from_unit(unit_length[i]), i)
                        #sum_size[i] += t

            l = [c.abs_size[i] for c in self.subboxes
                    if c.abs_size[i] is not None
                    and c.size[i] != 'ref'
                ]
            sum_size = sum(l) if l else None


            if self.size[i] is None:
                # all children's sizes must be known
                unknown_children = sum(1 for c in self.subboxes
                        if c.abs_size[i] is None
                        and c.size[i] != 'ref'
                    )
                assert(unknown_children == 0)

                # own size must be known somehow
                assert(sum_size is not None or ref_size[i] is not None)

                if sum_size is None:
                    self.abs_size[i] = sum_size
                elif ref_size[i] is None:
                    self.abs_size[i] = ref_size[i] # should be a NOP
                else:
                    assert(ref_size[i] == sum_size)
                    self.abs_size[i] = sum_size

            elif self.size[i] == 'ref':
                unknown_children = sum(1 for c in self.subboxes
                        if c.abs_size[i] is None
                        and c.size[i] != 'ref'
                    )
                if unknown_children == 0 and sum_size is not None:
                    self.abs_size[i] = sum_size
                else:
                    # there are relative sized subboxes, but the unit length is unknown
                    # or there aren't any children
                    pass

            elif isinstance(self.size[i], Rel):
                unknown_children = sum(1 for c in self.subboxes
                        if c.abs_size[i] is None
                        and c.size[i] != 'ref'
                    )
                if unknown_children == 0 and sum_size is not None:
                    self.abs_size[i] = sum_size
                else:
                    # there are relative sized subboxes, but the unit length is unknown
                    # or there aren't any children
                    pass

            elif self._has_absolute_width_configured(i):
                if self.abs_size[i] is not None:
                    assert(self.abs_size[i] == self.size[i])
                if sum_size is not None:
                    assert(sum_size == self.size[i])
                self.abs_size[i] = self.size[i]


            # update bound subbox sizes
            if self.abs_size[i] is not None:

                for c in self.subboxes:
                    if c.size[i] == 'ref' and c.abs_size[i] is None:
                        c._set_absolute_size(self.abs_size[i], i)

    def _get_sum(self):

        #sum_width = 0
        sum_abs_size = [0, 0, 0]
        sum_rel_size = [Rel(0), Rel(0), Rel(0)]
        unit_length = [None, None, None]
        ref_size = [None, None, None]

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

    def _set_absolute_size(self, value, i):

        assert(isinstance(self.size[i], Rel) or self.size[i] == 'ref')
        assert(self.abs_size[i] is None)

        self.abs_size[i] = value


        # update subboxes

        if not self.subboxes:
            return

        sum_abs_size, sum_rel_size, unit_length, ref_size = self._get_sum()

        assert(unit_length[i] is None)
        assert(ref_size[i] is None)

        if sum_rel_size[i] != Rel(0):
            assert(self.abs_size[i] >= sum_abs_size[i])
            unit_length[i] = sum_rel_size[i].unit_length_from_total(self.abs_size[i] - sum_abs_size[i])

        for c in self.subboxes:
            if c.abs_size[i] is None:
                if isinstance(c.size[i], Rel):
                    c._set_absolute_size(c.size[i].total_length_from_unit(unit_length[i]), i)
                elif c.size[i] == 'ref':
                    c._set_absolute_size(value, i)
                else:
                    assert(False)

    def _has_absolute_width_configured(self, i):
        return isinstance(self.size[i], int) or isinstance(self.size[i], float)


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
        self.walls.append(SideWall(self.size[0], self.size[2]))
        self.walls.append(SideWall(self.size[1], self.size[2]))
        self.walls.append(SideWall(self.size[0], self.size[2]))
        self.walls.append(SideWall(self.size[1], self.size[2]))
        self.walls.append(ExtendedWall(self.size[0], self.size[1]))
        self.walls.append(ExtendedWall(self.size[0], self.size[1]))

class ClosedBox(Box):
    def _construct_walls(self):
        self.walls = []
        self.walls.append(ToplessWall(self.size[0], self.size[2]))
        self.walls.append(ToplessWall(self.size[1], self.size[2]))
        self.walls.append(ToplessWall(self.size[0], self.size[2]))
        self.walls.append(ToplessWall(self.size[1], self.size[2]))
        self.walls.append(None)
        self.walls.append(ExtendedWall(self.size[0], self.size[1]))


class SubBox(Box):
    def __init__(self, width, height, depth):
        self.size = [width, height, depth]
        self.abs_size = [None, None, None]

        self.subboxes = []

    def render(self, config):
        # TODO uniquify wall references
        pass

    def get_wall_by_direction(self, v):
        if (v == DIR.UP).all():    return self.walls[0]
        if (v == DIR.DOWN).all():  return self.walls[1]
        if (v == DIR.LEFT).all():  return self.walls[2]
        if (v == DIR.RIGHT).all(): return self.walls[3]
        if (v == DIR.FRONT).all(): return self.walls[4]
        if (v == DIR.BACK).all():  return self.walls[5]
