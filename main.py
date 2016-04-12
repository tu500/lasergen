import codecs
import numpy as np

from wall import HexBoltCutout, CircleCutout, Wall, ToplessWall, ExtendedWall
from config import Config
from export import place_2d_objects, export_svg

def main():
    c = Config(8., 12., 4., 3., 2.)
    w = ToplessWall(100., 200.)

    w.add_child(HexBoltCutout(6), np.array([20,20]))
    w.add_child(CircleCutout(6), np.array([40,20]))

    e = ExtendedWall(100., 120.)

    objects = place_2d_objects([w.render(c), e.render(c)], c)

    with codecs.open('foo.svg', 'wb', 'utf-8') as f:
        f.write(export_svg(objects))

if __name__ == "__main__":
    main()
