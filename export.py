import numpy as np

from primitive import Line, Circle, ArcPath, Text
from util import min_vec, max_vec

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
