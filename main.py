#!/usr/bin/python3

import codecs
import numpy as np

from wall import HexBoltCutout, CircleCutout, Wall, ToplessWall, ExtendedWall
from config import Config
from export import place_2d_objects, export_svg
from util import DIR
from box import ClosedBox, ToplessBox

def main():
    c = Config(8., 12., 4., 3., 2.)

    cb = ClosedBox(100, 120, 60)
    cb.configure(c)
    cb.construct()
    cb.get_wall_by_direction(DIR.BACK).add_child(HexBoltCutout(6), np.array([20,20,0]))
    cb.get_wall_by_direction(DIR.BACK).add_child(CircleCutout(6), np.array([40,20,0]))
    tb = ToplessBox(100, 120, 60)
    tb.configure(c)
    tb.construct()

    e = ExtendedWall(100., 120.)

    objects = place_2d_objects(cb.render(c) + tb.render(c), c)

    with codecs.open('foo.svg', 'wb', 'utf-8') as f:
        f.write(export_svg(objects))

if __name__ == "__main__":
    main()
