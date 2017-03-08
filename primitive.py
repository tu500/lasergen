import numpy as np
import math

from layer import Layer
from util import DIR2, min_vec, max_vec, mirror_array_bool_to_factor
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

    def update_layer(self, layer):
        """
        Update all children's layers with the given value.
        """

        for p in self.primitives:
            p.layer = p.update_layer(layer)

    def bounding_box(self):
        """
        Calculate an axis aligned bounding box containing all primitives.

        Return value is `(min_corner, max_corner)`.
        """

        if not self.primitives:
            raise ValueError('Cannot calculate bounding box for empty collection.')

        bounding_boxes = [p.bounding_box() for p in self.primitives]

        vmin = min_vec(*(pmin for pmin, pmax in bounding_boxes))
        vmax = max_vec(*(pmax for pmin, pmax in bounding_boxes))

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

    def rotate(self, deg):
        """
        Return a new Object2D created by rotating all primitives in the
        'global' (meaning local to this Object2D, not its primitives) reference
        system counterclockwise.

        The rotation amount is given in degrees. Only multiples of 90 degrees
        are supported.
        """
        return Object2D([p.rotate(deg) for p in self.primitives])

    def mirror(self, mirror_axes):
        """
        Return a new Object2D created by mirroring all primitives in the
        'global' (meaning local to this Object2D, not its primitives) reference
        system along the specified axes.

        The axes are specified by a boolean array `mirror_axes` indicating
        which axes should be inverted.
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

    _data_to_local_coords = None
    parent = None

    def __init__(self, layer=Layer('cut')):
        self.layer = layer

    def update_layer(self, layer):
        """
        Update layer data with the given value.
        """

        self.layer = self.layer.combine(layer)

    def render(self, config):
        """Render into an Object2D."""
        raise NotImplementedError('Abstract method')

    def set_parent(self, parent, own_position):
        """
        Save a reference to this object's parent, ie. the WallReference it was
        added to. Automatically convert all parameters given by
        `_data_to_local_coords` to local coordinates according to the parent.

        Automatically called by WallReference.add_child.
        """

        if self.parent is not None:
            return

        self.parent = parent
        self.position = own_position #TODO i don't like this design

        if self._data_to_local_coords:
            for e in self._data_to_local_coords:
                if hasattr(self, e):
                    v = getattr(self, e)
                    if v is not None:
                        if len(v) == 3:
                            v = parent.to_local_coords(v)
                        v = Frac.array_total_length(v, parent.size)
                        setattr(self, e, v)

        self.init_parent()

    def init_parent(self):
        """
        Callback for initializing the object if access to the parent is needed.
        """
        pass

    @staticmethod
    def _calc_center_dir(v):
        """
        Helper function allowing boolean values for center parameters.
        """

        if isinstance(v, np.ndarray):
            return v
        if v == True:
            return np.array([1,1])
        elif v == False:
            return np.array([0,0])
        else:
            return np.array(v)


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
    def rotate(self, deg):
        """
        Rotate the primitive counterclockwise.

        The rotation amount is given in degrees. Only multiples of 90 degrees
        are supported.
        """
        return Object2D([p.rotate(deg) for p in self.primitives])

    def mirror(self, mirror_axes):
        """
        Mirror the primitive along the specified axes.

        The axes are specified by a boolean array `mirror_axes` indicating
        which axes should be inverted.
        """
        raise NotImplementedError('Abstract method')
    def reverse(self):
        """
        Reverse the direction of the primitive, if applicable.

        This is mainly used for exporting to continuous SVG path elements.
        """
        raise NotImplementedError('Abstract method')

    def bounding_box(self):
        """
        Calculate an axis aligned bounding box.

        Return value is `(min_corner, max_corner)`.
        """
        raise NotImplementedError('Abstract method')

    def render(self, config):
        """Render into an Object2D."""
        return Object2D([self])


class Line(Primitive2D):
    """
    A simple line primitive.
    """

    def __init__(self, start, end, layer=Layer('cut')):
        super(Line, self).__init__(layer)

        self.start = start
        self.end = end

    def __add__(self, b):
        return Line(self.start + b, self.end + b, layer=self.layer)
    def __sub__(self, b):
        return Line(self.start - b, self.end - b, layer=self.layer)
    def rotate(self, deg):
        return Line(DIR2.rotate(self.start, deg), DIR2.rotate(self.end, deg), layer=self.layer)
    def mirror(self, mirror_axes):
        fac = mirror_array_bool_to_factor(mirror_axes)
        return Line(self.start * fac, self.end * fac, layer=self.layer)
    def reverse(self):
        return Line(self.end, self.start, layer=self.layer)
    def bounding_box(self):
        vmin = min_vec(self.start, self.end)
        vmax = max_vec(self.start, self.end)
        return (vmin, vmax)

class Circle(Primitive2D):
    """
    A simple circle primitive.
    """

    def __init__(self, center, radius, layer=Layer('cut')):
        super(Circle, self).__init__(layer)

        self.center = center
        self.radius = radius

    def __add__(self, b):
        return Circle(self.center + b, self.radius, layer=self.layer)
    def __sub__(self, b):
        return Circle(self.center - b, self.radius, layer=self.layer)
    def rotate(self, deg):
        return Circle(DIR2.rotate(self.center, deg), self.radius, layer=self.layer)
    def mirror(self, mirror_axes):
        fac = mirror_array_bool_to_factor(mirror_axes)
        return Circle(self.center * fac, self.radius, layer=self.layer)
    def reverse(self):
        # not applicable
        return self

    def bounding_box(self):
        vmin = min_vec(self.center - np.array([self.radius, self.radius]))
        vmax = max_vec(self.center + np.array([self.radius, self.radius]))
        return (vmin, vmax)

class ArcPath(Primitive2D):
    """
    A primitive inspired by the SVG path arc command.

    Rendered one-to-one into the corresponding SVG element. Mainly used for
    drawing circle segments.
    """

    def __init__(self, start, end, radius, large_arc=True, sweep=True, layer=Layer('cut')):
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
    def rotate(self, deg):
        return ArcPath(DIR2.rotate(self.start, deg), DIR2.rotate(self.end, deg), self.radius, self.large_arc, self.sweep, layer=self.layer)
    def mirror(self, mirror_axes):
        parity = (sum(1 for v in mirror_axes if v) % 2) == 1
        fac = mirror_array_bool_to_factor(mirror_axes)
        return ArcPath(self.start * fac, self.end * fac, self.radius, self.large_arc, (not self.sweep) if parity else self.sweep, layer=self.layer)
    def reverse(self):
        return ArcPath(self.end, self.start, self.radius, self.large_arc, not self.sweep)

    def bounding_box(self):
        # TODO: this is only a heuristic

        if self.large_arc:
            t = 2*np.array([self.radius, self.radius])
        else:
            t = np.array([self.radius, self.radius])

        center = (self.start + self.end) / 2
        vmin = center - t
        vmax = center + t
        return (vmin, vmax)

    @staticmethod
    def from_center_angle(center, angle_start, angle_end, radius, layer=Layer('cut')):
        """
        Construct an ArcPath object from a given center, radius and angle interval.

        The angles are given in degrees, measuring counterclockwise. Angle 0 is
        pointing right, in the direction of the X axis.
        """

        start = center + radius * np.array([math.cos(angle_start / 180 * math.pi), math.sin(angle_start / 180 * math.pi)])
        end = center + radius * np.array([math.cos(angle_end / 180 * math.pi), math.sin(angle_end / 180 * math.pi)])
        large_arc = angle_end - angle_start >= 180
        return ArcPath(start, end, radius, large_arc=large_arc, layer=layer)

class Text(Primitive2D):
    """
    A text primitive.
    """

    def __init__(self, position, text, fontsize=5, layer=Layer('info')):
        super(Text, self).__init__(layer)

        self.position = position
        self.text = text
        self.fontsize = fontsize

    def __add__(self, b):
        return Text(self.position + b, self.text, self.fontsize, layer=self.layer)
    def __sub__(self, b):
        return Text(self.position - b, self.text, self.fontsize, layer=self.layer)
    def rotate(self, deg):
        # TODO
        return Text(DIR2.rotate(self.position, deg), self.text, self.fontsize, layer=self.layer)
    def mirror(self, mirror_axes):
        # TODO
        fac = mirror_array_bool_to_factor(mirror_axes)
        return Text(self.position * fac, self.text, self.fontsize, layer=self.layer)
    def reverse(self):
        # not applicable
        return self

    def bounding_box(self):
        # TODO
        vmin = self.position
        vmax = self.position
        return (vmin, vmax)
