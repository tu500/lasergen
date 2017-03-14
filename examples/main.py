#!/usr/bin/python3

import codecs
import numpy as np

from lasergen.planar import HexBoltCutout, CircleCutout, MountingScrewCutout
from lasergen.wall import ToplessWall, ExtendedWall
from lasergen.edge import CutoutEdge, EDGE_STYLE
from lasergen.config import Config
from lasergen.export import place_2d_objects, export_svg_with_paths
from lasergen.util import DIR
from lasergen.units import Rel
from lasergen.box import ClosedBox, ToplessBox

def main():
    c = Config(8., 12., 4., 3., 2.)

    cb = ClosedBox(100, 120, 60)
    cb.subdivide(DIR.UP, [Rel(3), Rel(1)])
    cb.configure(c)
    cb.get_wall_by_direction(DIR.BACK).add_child(HexBoltCutout(6), [20,20,0])
    cb.get_wall_by_direction(DIR.BACK).add_child(CircleCutout(6), [40,20,0])
    cb.get_wall_by_direction(DIR.BACK).add_child(MountingScrewCutout(6.5, 3, 20, DIR.DOWN), [60,40,0])
    tb = ToplessBox(100, 120, 60)
    tb.configure(c)

    e = ExtendedWall([100., 120.])
    e.add_child(CutoutEdge(120, np.array([1,0]), EDGE_STYLE.INTERNAL_FLAT, EDGE_STYLE.INTERNAL_FLAT), [40, 0])

    objects = place_2d_objects(cb.render(c) + tb.render(c) + [e.render(c)], c)

    with codecs.open('foo.svg', 'wb', 'utf-8') as f:
        f.write(export_svg_with_paths(objects, c))

if __name__ == "__main__":
    main()
