import numpy as np
import os

from layer import Layer
from primitive import Line, Circle, ArcPath, Text
from util import DIR, min_vec, max_vec, almost_equal, update_file

def place_2d_objects(objects, config):
    """
    A simple default placement.

    Automatically place the given Object2Ds, stacking them on the Y-axis.
    """

    bounding_boxes = [o.bounding_box() for o in objects]
    heights = [bb[1][1] - bb[0][1] + config.object_distance for bb in bounding_boxes]
    y_positions = [0] + list(np.cumsum(heights))
    return [o - bb[0] + np.array([0,y]) for o, bb, y in zip(objects, bounding_boxes, y_positions)]

def export_svg(objects, config):
    """
    Export given objects to SVG.

    Returns the resulting SVG file as string.
    """

    if not objects:
        raise ValueError('No objects provided for export.')

    vmin, vmax = objects[0].bounding_box()
    for o in objects:
        bb = o.bounding_box()
        vmin = min_vec(vmin, bb[0])
        vmax = max_vec(vmax, bb[1])

    s = """<?xml version="1.0" encoding="UTF-8"?>
        <svg xmlns="http://www.w3.org/2000/svg"
                version="1.1" baseProfile="full"
                viewBox="{} {} {} {}">
        """.format(vmin[0]-5, -vmax[1]-5, (vmax[0]-vmin[0]) + 10, (vmax[1]-vmin[1]) + 10)

    for o in objects:
        for p in o.primitives:

            color = config.get_color_from_layer(p.layer)

            if isinstance(p, Line):
                s += '<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="1px"/>\n'.format(
                        x1    = p.start[0],
                        y1    = -p.start[1],
                        x2    = p.end[0],
                        y2    = -p.end[1],
                        color = color,
                    )
            elif isinstance(p, Circle):
                s += '<circle cx="{cx}" cy="{cy}" r="{r}" stroke="{color}" stroke-width="1px" fill="none"/>\n'.format(
                        cx    = p.center[0],
                        cy    = -p.center[1],
                        r     = p.radius,
                        color = color,
                    )
            elif isinstance(p, ArcPath):
                s += '<path d="M {start_x} {start_y} A {radius_x} {radius_y} {angle_x} {large_arc} {sweep} {to_x} {to_y}" stroke="{color}" stroke-width="1px" fill="none"/>\n'.format(
                        start_x   = p.start[0],
                        start_y   = -p.start[1],
                        radius_x  = p.radius,
                        radius_y  = p.radius,
                        angle_x   = 0,
                        large_arc = 1 if p.large_arc else 0,
                        sweep     = 1 if p.sweep else 0,
                        to_x      = p.end[0],
                        to_y      = -p.end[1],
                        color     = color,
                    )
            elif isinstance(p, Text):
                s += '<text x="{x}" y="{y}" style="font-size:{fontsize}px" fill="{color}">{text}</text>\n'.format(
                        x        = p.position[0],
                        y        = -p.position[1],
                        fontsize = p.fontsize,
                        text     = p.text,
                        color    = color,
                    )

            else:
                raise ValueError('Unknown primitive')

    s += '</svg>'

    return s


class PathAccumulator():
    """
    Accumulates primitives, joining them into SVG paths, if appropriate.
    """

    def __init__(self, first_object, config, strict_layer_matching=True):

        self.objects = []
        self.finalized = False

        self.config = config
        self.strict_layer_matching = strict_layer_matching

        self.output = None
        self.start_point = None
        self.current_point = None
        self.layer = first_object.layer

        if isinstance(first_object, Circle):
            self.finalized = True
            self.objects.append(first_object)
            self.output = '<circle cx="{cx}" cy="{cy}" r="{r}" stroke="{color}" stroke-width="1px" fill="none"/>\n'.format(
                    cx    = first_object.center[0],
                    cy    = -first_object.center[1],
                    r     = first_object.radius,
                    color = config.get_color_from_layer(self.layer)
                )

        elif isinstance(first_object, Text):
            self.finalized = True
            self.objects.append(first_object)
            self.output = '<text x="{x}" y="{y}" style="font-size:{fontsize}px" fill="{color}">{text}</text>\n'.format(
                    x        = first_object.position[0],
                    y        = -first_object.position[1],
                    fontsize = first_object.fontsize,
                    text     = first_object.text,
                    color = config.get_color_from_layer(self.layer)
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
            raise ValueError('Unknown primitive')

    @staticmethod
    def from_list(objects, config, strict_layer_matching=True):
        """
        Create a PathAccumulator objects directly from a list of primitives.

        Raises an exception if the list is empty or any object could not be
        added.
        """

        assert(len(objects) > 0)

        acc = PathAccumulator(objects[0], config, strict_layer_matching)
        acc.add_object_list(objects[1:])

        return acc

    def add_object_list(self, lst):
        """
        Add several objects to the accumulator.

        Raises an exception if any object could not be added.
        """

        for o in lst:

            if not self.add_object(o):
                raise Exception('Could not add complete list to PathAccumulator.')

    def add_object(self, obj):
        """
        Add an object to the accumulator.

        Returns False if the object could not be added due to different layers,
        endpoints or inherent object incompatability.
        """

        if self.finalized:
            return False

        if isinstance(obj, Circle) or isinstance(obj, Text):
            return False

        if not (isinstance(obj, Line) or isinstance(obj, ArcPath)):
            raise ValueError('Unknown primitive')

        if not self.layer_compatible(obj.layer):
            return False

        if not almost_equal(obj.start, self.current_point):
            return False


        self.objects.append(obj)
        self.layer = self.layer.combine(obj.layer)

        if isinstance(obj, Line):

            if almost_equal(obj.end, self.start_point):
                # close the path
                self.output += 'Z" stroke="{color}" stroke-width="1px" fill="none"/>\n'.format(
                        color = self.config.get_color_from_layer(self.layer)
                    )
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
        """
        Close the accumulator and return the generated SVG path code.
        """

        if not self.finalized:

            if self.config.warn_for_unclosed_paths:
                m = 'WARNING: Unclosed path, rendering into warn layer.'
                self.layer = self.layer.combine(Layer.warn(m))
                print(m)

            self.output += '" stroke="{color}" stroke-width="1px" fill="none"/>\n'.format(
                    color = self.config.get_color_from_layer(self.layer)
                )
            self.finalized = True

        return self.output

    def layer_compatible(self, other_layer):
        """
        Check whether own layer is compatible with the given one, according to
        configured `strict_layer_matching` setting.
        """

        if self.strict_layer_matching:
            return self.layer == other_layer

        else:
            return self.layer.compatible(other_layer)


def accumulate_paths(obj, config, strict_layer_matching=True, join_nonconsecutive_paths=True):
    """
    Accumulate an Object2D's primitives into PathAccumulator objects.
    """


    def join_into_list(acc, lst):

        if acc.finalized or not join_nonconsecutive_paths:
            lst.append(acc)
            return

        start_matching = []
        end_matching = []

        for index, elem in enumerate(lst):

            if not elem.finalized and elem.layer_compatible(acc.layer):

                if almost_equal(acc.start_point, elem.current_point):
                    start_matching.append( (index, elem, True) )

                elif almost_equal(acc.start_point, elem.start_point):
                    start_matching.append( (index, elem, False) )

                if almost_equal(acc.current_point, elem.start_point):
                    end_matching.append( (index, elem, True) )

                elif almost_equal(acc.current_point, elem.current_point):
                    end_matching.append( (index, elem, False) )

        assert(len(start_matching) in [0, 1])
        assert(len(end_matching) in [0, 1])

        if start_matching and end_matching:

            s_index, s_elem, s_dir_matching = start_matching[0]
            e_index, e_elem, e_dir_matching = end_matching[0]

            if s_index == e_index:
                assert(s_dir_matching == e_dir_matching)
                if s_dir_matching:
                    s_elem.add_object_list(acc.objects)
                else:
                    s_elem.add_object_list([o.reverse() for o in reversed(acc.objects)])

            elif s_dir_matching and e_dir_matching:
                s_elem.add_object_list(acc.objects + e_elem.objects)
                lst.pop(e_index)
            elif s_dir_matching:
                s_elem.add_object_list(
                        acc.objects + [o.reverse() for o in reversed(e_elem.objects)]
                    )
                lst.pop(e_index)
            elif e_dir_matching:
                lst[s_index] = PathAccumulator.from_list(
                        [o.reverse() for o in reversed(s_elem.objects)] + acc.objects + e_elem.objects,
                        config,
                        strict_layer_matching
                    )
                lst.pop(e_index)
            else:
                e_elem.add_object_list(
                        [o.reverse() for o in reversed(acc.objects)] + s_elem.objects
                    )
                lst.pop(s_index)

        elif start_matching:
            index, elem, dir_matching = start_matching[0]

            if dir_matching:
                elem.add_object_list(acc.objects)
            else:
                lst[index] = PathAccumulator.from_list(
                        [o.reverse() for o in reversed(acc.objects)] + elem.objects,
                        config,
                        strict_layer_matching
                    )

        elif end_matching:
            index, elem, dir_matching = end_matching[0]

            if dir_matching:
                acc.add_object_list(elem.objects)
                lst[index] = acc
            else:
                elem.add_object_list(
                        [o.reverse() for o in reversed(acc.objects)]
                    )

        else:
            lst.append(acc)


    acc_list = []
    acc = None

    for p in obj.primitives:

        if acc is None:
            acc = PathAccumulator(p, config, strict_layer_matching)

        else:
            r = acc.add_object(p)

            if not r:
                join_into_list(acc, acc_list)

                acc = PathAccumulator(p, config, strict_layer_matching)

    join_into_list(acc, acc_list)

    return acc_list


def export_svg_with_paths(objects, config, join_nonconsecutive_paths=True):
    """
    Export given objects to SVG, converting contained Line objects to SVG paths
    and joining adjacent primitive pairs.

    Returns the resulting SVG file as string.
    """

    if not objects:
        raise ValueError('No objects provided for export.')

    vmin, vmax = objects[0].bounding_box()
    for o in objects:
        bb = o.bounding_box()
        vmin = min_vec(vmin, bb[0])
        vmax = max_vec(vmax, bb[1])

    s = """<?xml version="1.0" encoding="UTF-8"?>
        <svg xmlns="http://www.w3.org/2000/svg"
                version="1.1" baseProfile="full"
                viewBox="{} {} {} {}">
        """.format(vmin[0]-5, -vmax[1]-5, (vmax[0]-vmin[0]) + 10, (vmax[1]-vmin[1]) + 10)

    for o in objects:

        acc_list = accumulate_paths(o, config, True, join_nonconsecutive_paths)

        s += ''.join(acc.finalize() for acc in acc_list)

    s += '</svg>'

    return s


_MAKE_SOURCE = """
all: all-dxf

%.dxf: %.ps
	pstoedit -dt -f dxf:-polyaslines\ -mm $< $@

%.ps: %.svg
	inkscape -C -P $@ $<

%.stl: %.scad
	openscad -o $@ $<

export.stl: {dxffiles}


.PHONY: all view

view: {dxffiles}
	openscad export.scad &
"""


def _export_paths_to_openscad(paths, viewbox, filename, directory, translate, color, config, thickness_factor=1):
    """
    Convert paths to SVG file, write to file, return openscad source code.
    """

    svg = """<?xml version="1.0" encoding="UTF-8"?>
        <svg xmlns="http://www.w3.org/2000/svg"
                version="1.1" baseProfile="full"
                viewBox="{}">
        """.format(viewbox)
    svg += ''.join(p.finalize() for p in paths)
    svg += '</svg>'

    openscad_source = """
        translate([{tx}, {ty}, 0])
        color("{color}")
        linear_extrude(height = {thickness} * {thickness_factor}, center = true, convexity = 10)
        import (file = "{filename}", scale = 2.54/0.96 * 10/7);
        """.format(
                tx = translate[0],
                ty = translate[1],
                color = color,
                thickness = config.wall_thickness,
                filename = filename + '.dxf',
                thickness_factor = thickness_factor,
            )

    update_file(os.path.join(directory, filename + '.svg'), svg)

    return openscad_source


def export_openscad(box, config, directory, join_all_svg=True):
    """
    Export given box to OpenSCAD for previewing.

    Writes a number of files in the given directory. You can then run `make
    view` in this directory to open an OpenSCAD window or `make export.stl` to
    export it to an STL file.

    This feature needs `inkscape`, `pstoedit`, `openscad` and `make` to be
    configured and in your path.

    If `join_all_svg` is `True` the export uses less SVG files which decreases
    export time but may also decrease quality.
    """

    walls = box._gather_walls(config)

    # uniquify wall references, keep order for deterministic output
    seen = set()
    walls = [(w,p,d) for w,p,d in box._gather_walls(config) if not (w in seen or seen.add(w))]

    openscad_source = ''
    svg_filenames = []

    for wall_index, (wall, pos, direction) in enumerate(walls):

        # export single wall

        rendered = wall.render(config)

        vmin, vmax = rendered.bounding_box()
        viewbox = '{} {} {} {}'.format(
                0,
                0,
                (vmax[0]-vmin[0]),
                (vmax[1]-vmin[1]),
            )

        # get completely positive svg coordinates
        rendered -= vmin
        rendered -= np.array([0, vmax[1]-vmin[1]])

        paths = accumulate_paths(rendered, config, False)

        if join_all_svg:
            difference_paths = []
            union_paths = []
        else:
            difference_paths = [p for p in paths if p.layer.name == 'cut']
            union_paths = [p for p in paths if p.layer.name == 'info']

        # overall openscad commands

        if (abs(direction) == DIR.RIGHT).all():
            rotate = 'rotate([90,0,90])'
        elif (abs(direction) == DIR.UP).all():
            rotate = 'rotate([90,0,0])'
        elif (abs(direction) == DIR.FRONT).all():
            rotate = 'rotate([0,0,0])'

        openscad_source += """
            translate([{apx},{apy},  {apz}])
            {rotate} {{
            """.format(
                    apx = pos[0],
                    apy = pos[1],
                    apz = pos[2],
                    rotate = rotate,
                )

        if difference_paths:
            openscad_source += """
                difference() {
                """

        if union_paths:
            openscad_source += """
                    union() {
                """

        # export outline

        l = [p for p in paths if p.layer.name == 'edge']
        assert(len(l) > 0)
        outline = l[0]

        outline_file_name = 'w{}-outline'.format(wall_index)
        svg_filenames.append(outline_file_name)

        openscad_source += _export_paths_to_openscad(
                [outline] if not join_all_svg else paths,
                viewbox,
                outline_file_name,
                directory,
                vmin,
                config.get_color_from_layer(outline.layer),
                config,
            )


        # export info objects (union with outline)

        for obj_index, obj in enumerate(union_paths):
            if obj.layer.name == 'info':

                obj_file_name = 'w{}-u{}'.format(wall_index, obj_index)
                svg_filenames.append(obj_file_name)

                openscad_source += _export_paths_to_openscad(
                        [obj],
                        viewbox,
                        obj_file_name,
                        directory,
                        vmin,
                        config.get_color_from_layer(obj.layer),
                        config,
                        1.1,
                    )

        if union_paths:
            openscad_source += """
                    } // end union
                """


        # export cutout objects

        for obj_index, obj in enumerate(difference_paths):
            if obj.layer.name == 'cut':

                obj_file_name = 'w{}-d{}'.format(wall_index, obj_index)
                svg_filenames.append(obj_file_name)

                openscad_source += _export_paths_to_openscad(
                        [obj],
                        viewbox,
                        obj_file_name,
                        directory,
                        vmin,
                        config.get_color_from_layer(obj.layer),
                        config,
                        1.1,
                    )

        if difference_paths:
            openscad_source += """
                } // end difference
                """

        openscad_source += """
            } // end rotate
            """

    make_source = _MAKE_SOURCE.format(dxffiles=' '.join(s+'.dxf' for s in svg_filenames))

    update_file(os.path.join(directory, 'Makefile'), make_source)
    update_file(os.path.join(directory, 'export.scad'), openscad_source)
