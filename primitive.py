import numpy as np
import math

from util import min_vec, max_vec, mirror_array_bool_to_factor
from units import Frac


class Object2D():
    """
    Helper class to group several 2D primitives toghether into a 2D object.
    """

    def __init__(self, primitives=None, layer=None):

        if primitives is None:
            self.primitives = []
        else:
            self.primitives = primitives

        if layer is not None:
            self.set_layer(layer)

    def set_layer(self, layer):
        """
        Overwrite all children's layers to the given value.
        """

        for p in self.primitives:
            p.layer = layer

    def bounding_box(self):
        """
        Calculate an axis aligned bounding box containing all primitives.
        Return value is (min_corner, max_corner).
        """

        if not self.primitives:
            raise ValueError('Cannot calculate bounding box for empty collection.')

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
                # TODO
                pass

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

    def append(self, b):
        """
        Append a primitive to own primitive list.
        """
        self.primitives.append(b)

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

    def reverse(self):
        """
        Return a new Object2D where each primitive has been reversed, i.e. has
        start and end points swapped. This is used for exporting longer svg
        path objects.
        """
        return Object2D([p.reverse() for p in reversed(self.primitives)])


class PlanarObject():
    """
    Abstract base class for objects that render into an Object2D.
    """

    data_to_local_coords = None
    parent = None

    def __init__(self, layer='cut'):
        self.layer = layer

    def render(self, config):
        """Render into an Object2D."""
        raise NotImplementedError('Abstract method')

    def set_parent(self, parent):
        """
        Save a reference to this object's parent, ie. the WallReference it was
        added to. Automatically convert all parameters given by
        `data_to_local_coords` to local coordinates according to the parent.

        Automatically called by WallReference.add_child.
        """

        if self.parent is not None:
            return

        self.parent = parent

        if self.data_to_local_coords:
            for e in self.data_to_local_coords:
                if hasattr(self, e):
                    v = getattr(self, e)
                    if v is not None and len(v) == 3:
                        v = parent.to_local_coords(v)
                        setattr(self, e, v)


class Primitive2D(PlanarObject):
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
    def reverse(self):
        raise NotImplementedError('Abstract method')

    def render(self, config):
        """Render into an Object2D."""
        return Object2D([self])


class Line(Primitive2D):
    def __init__(self, start, end, layer='cut'):
        super(Line, self).__init__(layer)

        self.start = start
        self.end = end

    def __add__(self, b):
        return Line(self.start + b, self.end + b, layer=self.layer)
    def __sub__(self, b):
        return Line(self.start - b, self.end - b, layer=self.layer)
    def mirror(self, mirror_axes):
        fac = mirror_array_bool_to_factor(mirror_axes)
        return Line(self.start * fac, self.end * fac, layer=self.layer)
    def reverse(self):
        return Line(self.end, self.start, layer=self.layer)

class Circle(Primitive2D):
    def __init__(self, center, radius, layer='cut'):
        super(Circle, self).__init__(layer)

        self.center = center
        self.radius = radius

    def __add__(self, b):
        return Circle(self.center + b, self.radius, layer=self.layer)
    def __sub__(self, b):
        return Circle(self.center - b, self.radius, layer=self.layer)
    def mirror(self, mirror_axes):
        fac = mirror_array_bool_to_factor(mirror_axes)
        return Circle(self.center * fac, self.radius, layer=self.layer)
    def reverse(self):
        # not applicable
        return self

class ArcPath(Primitive2D):
    def __init__(self, start, end, radius, large_arc=True, sweep=True, layer='cut'):
        super(ArcPath, self).__init__(layer)

        self.start = start
        self.end = end
        self.radius = radius
        self.large_arc = large_arc
        self.sweep = sweep

    def __add__(self, b):
        return ArcPath(self.start + b, self.end + b, self.radius, self.large_arc, self.sweep, layer=self.layer)
    def __sub__(self, b):
        return ArcPath(self.start - b, self.end - b, self.radius, self.large_arc, self.sweep, layer=self.layer)
    def mirror(self, mirror_axes):
        # TODO this is not trivial
        return self
    def reverse(self):
        # TODO this is not trivial
        return self

    @staticmethod
    def from_center_angle(center, angle_start, angle_end, radius, layer='cut'):
        start = center + radius * np.array([math.cos(angle_start / 180 * math.pi), math.sin(angle_start / 180 * math.pi)])
        end = center + radius * np.array([math.cos(angle_end / 180 * math.pi), math.sin(angle_end / 180 * math.pi)])
        large_arc = angle_end - angle_start >= 180
        return ArcPath(start, end, radius, large_arc=large_arc, layer=layer)

class Text(Primitive2D):
    def __init__(self, position, text, fontsize=5, layer='info'):
        super(Text, self).__init__(layer)

        self.position = position
        self.text = text
        self.fontsize = fontsize

    def __add__(self, b):
        return Text(self.position + b, self.text, self.fontsize, layer=self.layer)
    def __sub__(self, b):
        return Text(self.position - b, self.text, self.fontsize, layer=self.layer)
    def mirror(self, mirror_axes):
        # TODO
        return self
    def reverse(self):
        # not applicable
        return self
