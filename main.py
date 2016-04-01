import codecs

from wall import Wall, ToplessWall, ExtendedWall
from config import Config
from export import export_svg

def main():
    c = Config(8., 12., 4., 2.)
    w = ToplessWall(100., 200.)

    result = w.render(c)

    with codecs.open('foo.svg', 'wb', 'utf-8') as f:
        f.write(export_svg(result))

if __name__ == "__main__":
    main()
