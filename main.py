#!/usr/bin/python3

import codecs
import numpy as np

from wall import HexBoltCutout, CircleCutout, MountingScrewCutout, Wall, ToplessWall, ExtendedWall
from wall import CutoutEdge, EDGE_STYLE
from config import Config
from export import place_2d_objects, export_svg
from util import DIR
from units import Rel
from box import ClosedBox, ToplessBox

def main():
    c = Config(8., 12., 4., 3., 2.)

    cb = ClosedBox(100, 120, 60)
    cb.subdivide(DIR.UP, Rel(3), Rel(1))
    cb.configure(c)
    cb.construct(c)
    cb.get_wall_by_direction(DIR.BACK).add_child(HexBoltCutout(6), np.array([20,20,0]))
    cb.get_wall_by_direction(DIR.BACK).add_child(CircleCutout(6), np.array([40,20,0]))
    cb.get_wall_by_direction(DIR.BACK).add_child(MountingScrewCutout(6.5, 3, 20, cb.get_wall_by_direction(DIR.BACK).to_local_coords(DIR.DOWN)), np.array([60,40,0]))
    tb = ToplessBox(100, 120, 60)
    tb.configure(c)
    tb.construct(c)

    e = ExtendedWall(100., 120.)
    e.add_child(CutoutEdge(120, np.array([1,0]), EDGE_STYLE.FLAT, EDGE_STYLE.FLAT), np.array([40, 0]))

    objects = place_2d_objects(cb.render(c) + tb.render(c) + [e.render(c)], c)

    with codecs.open('foo.svg', 'wb', 'utf-8') as f:
        f.write(export_svg(objects))

if __name__ == "__main__":
    main()
