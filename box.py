from wall import ToplessWall, ExtendedWall, SideWall
from util import DIR
from units import Rel

class Box():
    def __init__(self, width, height, depth):
        self.width = width
        self.height = height
        self.depth = depth

        self.abs_width = None
        self.abs_height = None

        self._construct_walls()
        self.subboxes = []

    def render(self, config):
        return [w.render(config) for w in self.walls if w is not None]

    def configure(self, config):

        if self.abs_width is not None:
            # nothing to do
            return

        for c in self.children:
            c.configure(config)

        sum_abs_width, sum_rel_width, unit_length = self._get_sum()

        if self._has_absolute_width_configured() and sum_rel_width != Rel(0):
            assert(self.width >= sum_abs_width)
            new_ul = sum_rel_width.unit_length_from_total(self.width - sum_abs_width)

            if unit_length is not None:
                assert(new_ul == unit_length)

            unit_length = new_ul

        if unit_length is not None:

            for c in self.children:
                if isinstance(c.width, Rel) and c.abs_width is None:
                    c._set_width_from_unit_length(unit_length)
                    #sum_width += t

        sum_width = sum(c.abs_width for c in children if c.abs_width is not None)

        if self.width is None:
            assert(sum_rel_width == Rel(0) or unit_length is not None)
            self.abs_width = sum_width

        elif isinstance(self.width, Rel):
            if sum_rel_width == Rel(0) or unit_length is not None:
                self.abs_width = sum_width
            else:
                # there are relative sized children, but the unit length is unknown
                return

        elif self._has_absolute_width_configured():
            assert(sum_width == self.width)
            self.abs_width = sum_width

    def _get_sum(self):

        #sum_width = 0
        sum_abs_width = 0
        sum_rel_width = Rel(0)
        unit_length = None

        for c in self.children:

            assert(not (c.width is None and c.abs_width is None))

            if c.width is None:
                assert(c.abs_width is not None)
                #sum_width += c.abs_width
                sum_abs_width += c.abs_width

            elif isinstance(c.width, Rel):
                if c.abs_width is None:
                    sum_rel_width += c.width
                else:
                    #sum_width += c.abs_width

                    sum_rel_width += c.width
                    new_ul = c.width.unit_length_from_total(c.abs_width)
                    assert(unit_length is None or new_ul == unit_length)
                    unit_length = new_ul

            elif self._has_absolute_width_configured():
                assert(c.abs_width is not None)
                #sum_width += c.abs_width
                sum_abs_width += c.abs_width

        return sum_abs_width, sum_rel_width, unit_length

    def _set_width_from_unit_length(self, ul):
        assert(isinstance(self.width, Rel))

        self.abs_width = self.width.total_length_from_unit(ul)


        # update children

        sum_abs_width, sum_rel_width, unit_length = self._get_sum()

        assert(unit_length is None)
        assert(sum_rel_width != Rel(0))

        assert(self.abs_width >= sum_abs_width)
        unit_length = sum_rel_width.unit_length_from_total(self.abs_width - sum_abs_width)

        for c in self.children:
            if isinstance(c.width, Rel) and c.width is None:
                c._set_width_from_unit_length(unit_length)

    def _has_absolute_width_configured(self):
        return isinstance(self.width, int) or isinstance(self.width, float)

    # def configure(self, config):
    #
    #     if self.abs_width is not None and isinstance(self.width, int):
    #         if self.abs_width != self.width:
    #             raise Exception("hard error")
    #     if self.abs_height is not None and isinstance(self.height, int):
    #         if self.abs_height != self.height:
    #             raise Exception("hard error")
    #
    #     if isinstance(self.width, int):
    #         self.abs_width = self.width
    #     if isinstance(self.height, int):
    #         self.abs_height = self.height
    #
    #     # set child sizes, if possible
    #     if self.division_axis == 'x':
    #         if self.abs_height is not None:
    #             for c in self.children:
    #                 c.abs_height = self.abs_height
    #         if self.abs_width is not None:
    #             abs_sum = 0
    #             rel_sum = Rel(0)
    #             for c in self.children:
    #                 if isinstance(c.width, int):
    #                     abs_sum += c.width
    #                 elif isinstance(c.width, Rel):
    #                     rel_sum += c.width
    #                 elif c.width is None:
    #                     c.configure(config)
    #                     if c.abs_width is None:
    #                         raise Exception("hard error")
    #                     abs_sum += c.abs_width
    #             if rel_sum == Rel(0):
    #                 if abs_sum != self.abs_width:
    #                     raise Exception("hard error")
    #             else:
    #                 unit_length = rel_sum.unit_length_from_total(abs_sum)
    #                 for c in self.children:
    #                     if isinstance(c.width, Rel):
    #                         c.abs_width = c.width.total_length_from_unit(unit_length)
    #     elif self.division_axis == 'y':
    #         if self.abs_width is not None:
    #             for c in self.children:
    #                 c.abs_width = self.abs_width
    #         if self.abs_height is not None:
    #             abs_sum = 0
    #             rel_sum = Rel(0)
    #             for c in self.children:
    #                 if isinstance(c.height, int):
    #                     abs_sum += c.height
    #                 elif isinstance(c.height, Rel):
    #                     rel_sum += c.height
    #                 elif c.height is None:
    #                     c.configure(config)
    #                     if c.abs_height is None:
    #                         raise Exception("hard error")
    #                     abs_sum += c.abs_height
    #             if rel_sum == Rel(0):
    #                 if abs_sum != self.abs_height:
    #                     raise Exception("hard error")
    #             else:
    #                 unit_length = rel_sum.unit_length_from_total(abs_sum)
    #                 for c in self.children:
    #                     if isinstance(c.height, Rel):
    #                         c.abs_height = c.height.total_length_from_unit(unit_length)
    #
    #     # call configure for children
    #     for c in self.children:
    #         c.configure(config)
    #
    #     # check if self.size == sum(children.size)
    #     # or set if self hasnt an abs size yet
    #     if self.division_axis == 'x':
    #         if self.abs_height is None:
    #             raise Exception()
    #     elif self.division_axis == 'y':
    #
    #     if self.abs_width is None:
    #         if not isinstance(self.width, Rel):
    #             raise Exception("hard error")
    #         else:
    #             raise Exception("soft error") #?
    #     if self.abs_height is None:
    #         if not isinstance(self.height, Rel):
    #             raise Exception("hard error")
    #         else:
    #             raise Exception("soft error") #?

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
        self.walls.append(SideWall(self.width, self.depth))
        self.walls.append(SideWall(self.height, self.depth))
        self.walls.append(SideWall(self.width, self.depth))
        self.walls.append(SideWall(self.height, self.depth))
        self.walls.append(ExtendedWall(self.width, self.height))
        self.walls.append(ExtendedWall(self.width, self.height))

class ClosedBox(Box):
    def _construct_walls(self):
        self.walls = []
        self.walls.append(ToplessWall(self.width, self.depth))
        self.walls.append(ToplessWall(self.height, self.depth))
        self.walls.append(ToplessWall(self.width, self.depth))
        self.walls.append(ToplessWall(self.height, self.depth))
        self.walls.append(None)
        self.walls.append(ExtendedWall(self.width, self.height))


class SubBox(Box):
    def __init__(self, width, height, depth):
        self.width = width
        self.height = height
        self.depth = depth

        self.abs_width = None
        self.abs_height = None

        self.subboxes = []

    def render(self, config):
        # TODO uniquify wall references

    def get_wall_by_direction(self, v):
        if (v == DIR.UP).all():    return self.walls[0]
        if (v == DIR.DOWN).all():  return self.walls[1]
        if (v == DIR.LEFT).all():  return self.walls[2]
        if (v == DIR.RIGHT).all(): return self.walls[3]
        if (v == DIR.FRONT).all(): return self.walls[4]
        if (v == DIR.BACK).all():  return self.walls[5]
