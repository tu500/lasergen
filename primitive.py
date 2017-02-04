import numpy as np
import math

from util import min_vec, max_vec, mirror_array_bool_to_factor
from units import Frac


class Object2D():
    """
    Helper class to group several 2D primitives toghether into a 2D object.
    """

    def __init__(self, primitives=None):
        if primitives is None:
            self.primitives = []
        else:
            self.primitives = primitives

    def bounding_box(self):
        """
        Calculate an axis aligned bounding box containing all primitives.
        Return value is (min_corner, max_corner).
        """

        if not self.primitives:
            raise Exception("PANIC!!!!")

        p = self.primitives[0]
        if isinstance(p, Line):
            vmin = p.start
            vmax = p.start
        elif isinstance(p, Circle):
            vmin = p.center
            vmax = p.center

        for p in self.primitives:
            if isinstance(p, Line):
                vmin = min_vec(vmin, p.start, p.end)
                vmax = max_vec(vmax, p.start, p.end)
            elif isinstance(p, Circle):
                vmin = min_vec(vmin, p.center - np.array([p.radius, p.radius]))
                vmax = max_vec(vmax, p.center + np.array([p.radius, p.radius]))
            elif isinstance(p, ArcPath):
                # TODO: this is only a (bad) heuristic
                vmin = min_vec(vmin, p.start - 2*np.array([p.radius, p.radius]), p.end - 2*np.array([p.radius, p.radius]))
                vmax = max_vec(vmax, p.start + 2*np.array([p.radius, p.radius]), p.end + 2*np.array([p.radius, p.radius]))
            else:
                raise Exception("PANIC")

        return (vmin, vmax)

    def __add__(self, b):
        """
        If argument is an Object2D, create a new Object2D concatenating both's
        primitive list. Else perform element wise additionn.
        """
        if isinstance(b, Object2D):
            return Object2D(self.primitives + b.primitives)
        return Object2D([i + b for i in self.primitives])

    def __sub__(self, b):
        """
        Perform elementwise subtraction.
        """
        return Object2D([i - b for i in self.primitives])

    def extend(self, b):
        """
        Extend own primitive list with another Object2D's one.
        """
        self.primitives.extend(b.primitives)

    def mirror(self, mirror_axes):
        """
        Return a new Object2D created by mirroring all primitives in the
        'global' (meaning local to this Object2D, not its primitives) reference
        system along the specified axes.
        """
        return Object2D([p.mirror(mirror_axes) for p in self.primitives])


class Primitive2D():
    """
    Abstract base class for 2D primitives.
    """
    def __add__(self, b):
        """Translation."""
        raise NotImplementedError('Abstract method')
    def __sub__(self, b):
        """Translation."""
        raise NotImplementedError('Abstract method')
    def mirror(self, mirror_axes):
        raise NotImplementedError('Abstract method')


class Line(Primitive2D):
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def __add__(self, b):
        return Line(self.start + b, self.end + b)
    def __sub__(self, b):
        return Line(self.start - b, self.end - b)
    def mirror(self, mirror_axes):
        fac = mirror_array_bool_to_factor(mirror_axes)
        return Line(self.start * fac, self.end * fac)

class Circle(Primitive2D):
    def __init__(self, center, radius):
        self.center = center
        self.radius = radius

    def __add__(self, b):
        return Circle(self.center + b, self.radius)
    def __sub__(self, b):
        return Circle(self.center - b, self.radius)
    def mirror(self, mirror_axes):
        fac = mirror_array_bool_to_factor(mirror_axes)
        return Circle(self.center * fac, self.radius)

class ArcPath(Primitive2D):
    def __init__(self, start, end, radius, large_arc=True, sweep=True):
        self.start = start
        self.end = end
        self.radius = radius
        self.large_arc = large_arc
        self.sweep = sweep

    def __add__(self, b):
        return ArcPath(self.start + b, self.end + b, self.radius, self.large_arc, self.sweep)
    def __sub__(self, b):
        return ArcPath(self.start - b, self.end - b, self.radius, self.large_arc, self.sweep)
    def mirror(self, mirror_axes):
        # TODO
        return self

    @staticmethod
    def from_center_angle(center, angle_start, angle_end, radius):
        start = center + radius * np.array([math.cos(angle_start / 180 * math.pi), math.sin(angle_start / 180 * math.pi)])
        end = center + radius * np.array([math.cos(angle_end / 180 * math.pi), math.sin(angle_end / 180 * math.pi)])
        large_arc = angle_end - angle_start >= 180
        return ArcPath(start, end, radius, large_arc=large_arc)

class Text(Primitive2D):
    def __init__(self, positionn, text, fontsize=5):
        self.position = position
        self.text = text
        self.fontsize = fontsize

    def __add__(self, b):
        return Text(self.position + b, self.text, self.fontsize)
    def __sub__(self, b):
        return Text(self.position - b, self.text, self.fontsize)
    def mirror(self, mirror_axes):
        # TODO
        return self
