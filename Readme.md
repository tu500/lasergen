LaserGen
========

LaserGen is an extendable python library / framework for automatically creating
designs to be used with laser cutters to create simple to complex boxed cases.

Features
--------

* Automatic creation of toothed edges for better stability
* Simple adding of predefined cutouts
* Cases with multiple, nested compartments
* SVG export
* OpenSCAD / STL export for 3D preview

Requirements
------------

* `numpy`

To use the OpenSCAD export you will also need:

* `inkscape`
* `pstoedit`
* `openscad`
* `make`

Usage
-----

See `docs/userguide.md` for an overview. Also there are some examples in the
`examples` directory.

Todo / Nice to Have
-------------------

* More configurable warnings
* Support multiple wall thicknesses
* Improved OpenSCAD export
* Automatic object placement
* DSL with editor (read 'vim') support

Feedback
--------

If you like this project and maybe have a nice example design or additional 2D
objects to include here, feel free to drop me an email or open a pull request.
