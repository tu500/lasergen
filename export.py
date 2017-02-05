import numpy as np

from primitive import Line, Circle, ArcPath, Text
from util import min_vec, max_vec, almost_equal

def place_2d_objects(objects, config):
    bounding_boxes = [o.bounding_box() for o in objects]
    heights = [bb[1][1] - bb[0][1] + config.object_distance for bb in bounding_boxes]
    y_positions = [0] + list(np.cumsum(heights))
    return [o - bb[0] + np.array([0,y]) for o, bb, y in zip(objects, bounding_boxes, y_positions)]

def export_svg(objects):

    if not objects:
        raise Exception("PANIC!!!!!")

    vmin, vmax = objects[0].bounding_box()
    for o in objects:
        bb = o.bounding_box()
        vmin = min_vec(vmin, bb[0])
        vmax = max_vec(vmax, bb[1])

    s = """<?xml version="1.0" encoding="UTF-8"?>
        <svg xmlns="http://www.w3.org/2000/svg"
                version="1.1" baseProfile="full"
                viewBox="{} {} {} {}">
        """.format(vmin[0]-5, -(vmax[1]-vmin[1]) - 5, (vmax[0]-vmin[0]) + 10, (vmax[1]-vmin[1]) + 10)

    for o in objects:
        for p in o.primitives:

            if isinstance(p, Line):
                s += '<line x1="{}" y1="{}" x2="{}" y2="{}" stroke="black" stroke-width="1px"/>\n'.format(
                        p.start[0],
                        -p.start[1],
                        p.end[0],
                        -p.end[1]
                    )
            elif isinstance(p, Circle):
                s += '<circle cx="{}" cy="{}" r="{}" stroke="black" stroke-width="1px" fill="none"/>\n'.format(
                        p.center[0],
                        -p.center[1],
                        p.radius
                    )
            elif isinstance(p, ArcPath):
                s += '<path d="M {start_x} {start_y} A {radius_x} {radius_y} {angle_x} {large_arc} {sweep} {to_x} {to_y}" stroke="black" stroke-width="1px" fill="none"/>\n'.format(
                        start_x   = p.start[0],
                        start_y   = -p.start[1],
                        radius_x  = p.radius,
                        radius_y  = p.radius,
                        angle_x   = 0,
                        large_arc = 1 if p.large_arc else 0,
                        sweep     = 1 if p.sweep else 0,
                        to_x      = p.end[0],
                        to_y      = -p.end[1]
                    )
            elif isinstance(p, Text):
                s += '<text x="{}" y="{}" style="font-size:{}px" fill="red">{}</text>\n'.format(
                        p.position[0],
                        -p.position[1],
                        p.fontsize,
                        p.text
                    )

            else:
                raise Exception("PANIC")

    s += '</svg>'

    return s


class PathAccumulator():
    def __init__(self, first_object):

        self.objects = []
        self.finalized = False

        self.output = None
        self.start_point = None
        self.current_point = None

        if isinstance(first_object, Circle):
            self.finalized = True
            self.objects.append(first_object)
            self.output = '<circle cx="{}" cy="{}" r="{}" stroke="black" stroke-width="1px" fill="none"/>\n'.format(
                    first_object.center[0],
                    -first_object.center[1],
                    first_object.radius
                )

        elif isinstance(first_object, Text):
            self.finalized = True
            self.objects.append(first_object)
            self.output = '<text x="{}" y="{}" style="font-size:{}px" fill="red">{}</text>\n'.format(
                    first_object.position[0],
                    -first_object.position[1],
                    first_object.fontsize,
                    first_object.text
                )

        elif isinstance(first_object, Line) or isinstance(first_object, ArcPath):
            self.start_point = first_object.start
            self.current_point = self.start_point
            self.output = '<path d="M {},{} '.format(
                    self.start_point[0],
                    -self.start_point[1]
                )
            self.add_object(first_object)

        else:
            raise Exception("PANIC")

    def add_object(self, obj):

        if self.finalized:
            return False

        if isinstance(obj, Circle) or isinstance(obj, Text):
            return False

        if not (isinstance(obj, Line) or isinstance(obj, ArcPath)):
            raise Exception("PANIC")

        if not almost_equal(obj.start, self.current_point):
            return False


        self.objects.append(obj)

        if isinstance(obj, Line):

            if almost_equal(obj.end, self.start_point):
                # close the path
                self.output += 'Z" stroke="black" stroke-width="1px" fill="none"/>\n'
                self.finalized = True

            else:
                self.current_point = obj.end
                self.output += 'L {},{} '.format(
                        obj.end[0],
                        -obj.end[1]
                    )

        elif isinstance(obj, ArcPath):
            self.current_point = obj.end
            self.output += 'A {radius_x} {radius_y} {angle_x} {large_arc} {sweep} {to_x},{to_y} '.format(
                    radius_x  = obj.radius,
                    radius_y  = obj.radius,
                    angle_x   = 0,
                    large_arc = 1 if obj.large_arc else 0,
                    sweep     = 1 if obj.sweep else 0,
                    to_x      = obj.end[0],
                    to_y      = -obj.end[1]
                )

        return True

    def finalize(self):

        if not self.finalized:
            self.output += '" stroke="black" stroke-width="1px" fill="none"/>\n'
            self.finalized = True

        return self.output


def export_svg_with_paths(objects):

    if not objects:
        raise Exception("PANIC!!!!!")

    vmin, vmax = objects[0].bounding_box()
    for o in objects:
        bb = o.bounding_box()
        vmin = min_vec(vmin, bb[0])
        vmax = max_vec(vmax, bb[1])

    s = """<?xml version="1.0" encoding="UTF-8"?>
        <svg xmlns="http://www.w3.org/2000/svg"
                version="1.1" baseProfile="full"
                viewBox="{} {} {} {}">
        """.format(vmin[0]-5, -(vmax[1]-vmin[1]) - 5, (vmax[0]-vmin[0]) + 10, (vmax[1]-vmin[1]) + 10)

    for o in objects:

        acc = None

        for p in o.primitives:

            if acc is None:
                acc = PathAccumulator(p)

            else:
                r = acc.add_object(p)

                if not r:
                    s += acc.finalize()
                    acc = PathAccumulator(p)

        s += acc.finalize()

    s += '</svg>'

    return s
