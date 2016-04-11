from wall import Line, Circle

def export_svg(objects):

    s = """<?xml version="1.0" encoding="UTF-8"?>
        <svg xmlns="http://www.w3.org/2000/svg"
                version="1.1" baseProfile="full"
                viewBox="-50 -250 300 300">
        """

    for o in objects:

        if isinstance(o, Line):
            s += '<line x1="{}" y1="{}" x2="{}" y2="{}" stroke="black" stroke-width="1px"/>\n'.format(
                    o.start[0],
                    -o.start[1],
                    o.end[0],
                    -o.end[1]
                )
        elif isinstance(o, Circle):
            s += '<circle cx="{}" cy="{}" r="{}" stroke="black" stroke-width="1px" fill="none"/>\n'.format(
                    o.center[0],
                    -o.center[1],
                    o.radius
                )
        else:
            raise Exception("PANIC")

    s += '</svg>'

    return s
