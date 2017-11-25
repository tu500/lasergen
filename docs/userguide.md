User Guide
==========

Coordinate System
-----------------

LaserGen uses a right handed coordinate system with the following mapping:

* The first axis `X` goes to the right.
* The second axis `Y` goes up.
* The third axis `Z` goes to the front.

Semantic names for the directions are provided by `util.DIR` and `util.DIR2`.

### Specifying coordinates

LaserGen internally uses numpy arrays to store vectors, but most user interface
methods will automatically create these, so values can be specified by any
iterator with the right length.

### Sizes and base points

When specifying the size of an object, specifically for boxes, walls and edges,
this size is usually interpreted as a base size.

For boxes this means that the given size determines the inner dimension of the
box, so excluding the thickness of its walls. Consistently the size of a wall
refers to its inner dimension, excluding its extruding teeth and the length of
an edge does not include possible extruding ends (see `Edge styles`).

Accordingly the origin of an object's coordinate system is taken to be the
corresponding inner corner.


Boxes
-----

A box is usually the starting points for building anything with LaserGen.

Boxes represent rectangular 3D objects, including their walls and, possibly,
subboxes.

The `box` module provides some templates that define certain standard
configurations.

* `ToplessBox`
* `ClosedBox`

These templates especially will define the layout and toothing of its walls.

Note: After creating a box it has to be configured. See below.

### Subdivision

Boxes can be subdivided into subboxes, defining compartments within their
parent boxes. This is done by calling the `subdivide` method on a box.

`subdivide` takes an axis as direction (`DIR.RIGHT`, `DIR.UP`, `DIR.FRONT`) and
a list of sizes as parameters. These sizes don't have to be specified as
absolute values. LaserGen can automatically calculate missing and also relative
values.

To specify that a subbox should take up as much space as its children need,
give a size of `None`. To specify a size relative to its siblings give a
`units.Rel` object as size.

This behaviour is inspired by CSS like star notation. All subboxes having
relative sizes will split up the remaining space that is left when subtracting
their absolute-sized siblings. Also forcing a relative sized subbox to an
absolute size by its own children will propagate this value to its siblings. In
this case the parent box does not need to impose an absolute size.

For example

```python
box.subdivide(DIR.LEFT, [Rel(1), Rel(3), Rel(1)])
```

will subdivide `box` into 3 subboxes along the `X` axis taking up 1/5, 3/5 and
1/5 of the size, repectively and

```python
box.subdivide(DIR.LEFT, [10, Rel(1), 30])
```

will make the middle box take up the remaining space left by its siblings.

Note: The same values can also be supplied to the initial parent box.

See also the documentation of `subdivide` for how to specify subbox names.
These will be used to generate wall names.

### Configure

To actually calculate absolute values of all subboxes you need to call the
`configure` method.

Note: This needs to be called, too, if you don't use any subdivisions.

Note: Since walls need absolute sizes when being initialized, they can only be
constructed after determining absolute sizes of all subboxes. Therefore this
will be done by the `configure` method. As a side effect walls cannot be used
before calling `configure`, so make sure to first setup all subdivisions and
`configure` before using any walls.

Note: `configure` will abort if any sizes mismatch or are under-specified.


Walls
-----

Walls represent the intended main output of LaserGen projects.

### Creating wall objects

In basic usage you shouldn't need to create wall objects yourself. However if
you need to, LaserGen provides some templates that define different edge
styles:

* `ToplessWall`
* `InvToplessWall`
* `ExtendedWall`
* `SideWall`
* `InvSideWall`
* `SubWall`

The ``Inv*`` templates are needed when creating boxes so the edge styles match
up.

Note: When creating walls yourself you might miss out on some convenience
features provided by wall and edge reference meta data. You probably want to
set this data. See the autoc4 example.

### Using walls

The primary things you want to do with walls is adding child objects and
changing their edge data.

To add 2D children to walls first create the child object and then call
`add_child` on the wall, giving its intended position.

When later rendering the wall, all children will be rendered, too, and included
in the result.


Planar objects
--------------

LaserGen provides a library of default objects that can be added to walls.

* `CutoutRect`
* `CutoutRoundedRect`
* `HexBoltCutout`
* `CircleCutout`
* `MountingScrewCutout`
* `FanCutout`
* `AirVentsCutout`

All these will render into a collection of primitives that later can be
exported. If needed those primitives can be added as children themselves.

* `Line`
* `Circle`
* `ArcPath`
* `Text`

### Custom objects

To create custom objects look at the standard objects in the `planar` module.
Keep in mind to render the object at the origin, as positioning is handled by
the parent wall object.


References
----------

When calling `get_wall_by_direction` on a box or `get_edge_by_directoin` on a
wall the result will actually not be the wall/edge object itself, but rather a
reference object.

These references store the direction of the referenced object and may refer to
only a subportion of the original object.

Note: This only applies to LaserGen generated objects. When creating your own
boxes and walls you need to create and save the references yourself to achieve
the same behaviour. This should however be straight-forward when looking at
example code.

### Coordinate conversion

With this information these references will automatically convert given values
to their local coordinate system. This allows you, when adding children to
walls for example, to specify positions in box space without needing to think
about how to convert them yourself.

For example, the following three calls all will have the same effect:

```python
box.get_wall_by_direction(DIR.DOWN).add_child(CircleCutout(1), [23, 42])
box.get_wall_by_direction(DIR.DOWN).add_child(CircleCutout(1), [23, 0, 42])
box.get_wall_by_direction(DIR.DOWN).add_child(CircleCutout(1), [23, 17, 42])
```

You can manually do these conversions by calling the `to_local_coords` method
on a reference.

### Frac Values

When specifying child positions and sizes it is often helpful to specify these
as fractional values, relative to the total size of the parent object. This can
be done by giving values of `units.Frac`.

For example, to add a circle to the center of a wall:

```python
box.get_wall_by_direction(DIR.DOWN).add_child(CircleCutout(1), [Frac(0.5), Frac(0.5)])
```

These also support adding absolute offsets, so, to create a rectangle of four
circles you could do:

```python
box.get_wall_by_direction(DIR.DOWN).add_child(CircleCutout(1), [Frac(0.5) + 10, Frac(0.5) + 10])
box.get_wall_by_direction(DIR.DOWN).add_child(CircleCutout(1), [Frac(0.5) - 10, Frac(0.5) + 10])
box.get_wall_by_direction(DIR.DOWN).add_child(CircleCutout(1), [Frac(0.5) + 10, Frac(0.5) - 10])
box.get_wall_by_direction(DIR.DOWN).add_child(CircleCutout(1), [Frac(0.5) - 10, Frac(0.5) - 10])
```

This works as expected even when adding objects to walls of subboxes that only
refer to subportions of actual walls, meaning fractional values then are
relative to the size of the subbox, not the size of the actual wall.

Furthermore 2D objects save the wall reference they were added to as parent, so
these conversion rules also apply to parameters of 2D objects. The following
example will create a rectangle half the size of its parent wall.

```python
box.get_wall_by_direction(DIR.DOWN).add_child(CutoutRectangle([Frac(0.5), Frac(0.5)]), [10, 10])
```


Edges
-----

Edges are special 2D objects that take care of rendering edges of walls,
supporting different styles.

### Edge Element Styles

Edges can be rendered in different styles.

* `EDGE_ELEMENT_STYLE.FLAT`
* `EDGE_ELEMENT_STYLE.FLAT_EXTENDED`
* `EDGE_ELEMENT_STYLE.TOOTHED`
* `EDGE_ELEMENT_STYLE.REMOVE`

The `FLAT` style renders a completely flat edge that sits exactly at the
dimension of the wall.

The `FLAT_EXTENDED` style renders a flat edge, that is extended outwards by the
configured wall thickness. With a matching `FLAT` counterpart edge this will
allow two walls to be actually joined together.

The `TOOTHED` style will alternate between short lengths of `FLAT` and
`FLAT_EXTENDED`-like parts, creating a toothed edge for improved stability.

The `REMOVE` style will simply not render anything, allowing custom geometry to
be added. This can be used to create edge cutouts and edge extensions. When not
designing custom objects you shouldn't need to use this. It is however
automatically used by the following 2D objects:

* `RectEdgeCutout`
* `RoundedRectEdgeCutout`

An edge's style can be configured with the `set_style` method.

Note that this cannot be called on edge references that refer only to a
subportion of an edge. See next section.

### Edge elements

Apart from having a main style, edges can also be partitioned further into edge
elements that each have their own style. This allows to have, for example, a
flat edge only having a short toothed part or vice versa.

An element can be added with the `add_element` method. This method honors
partial edge references and can be used to set a style for a subportion of an
edge. Note however that, unlike when setting an edge's main style, edge
elements must not overlap, therefore adding another element to the subpart is
then impossible; the appropriate elements must be added manually.

Internally all portions of an edge not belonging to an added element are given
elements of the edge's main style.

### Edge styles

To control the rendering of an edge's end it can be given one of a number of
edge styles.

* `EDGE_STYLE.TOOTHED`
* `EDGE_STYLE.EXTENDED`
* `EDGE_STYLE.FLAT`
* `EDGE_STYLE.INTERNAL_FLAT`
* `EDGE_STYLE.OUTWARD`
* `EDGE_STYLE.INTERNAL_OUTWARD`

Edge styles are local to one edge. The resulting geometry, however, should be
considered together with its neighbour. The result can be best explained by an
image.

```
    ╲                                ╲
     ╲                                ╲
      ╲                                ╲
       ╔════════════╗                   ╲    ╔════════╗
       ║╲           ║                    ╲   ║        ║
       ║ ╲          ║                     ╲  ║        ║
       ║  ╲         ║                      ╲ ║        ║
       ║   ╲        ║                       ╲║        ║
       ║    ╲-------╚═══════════┄┄┄┄┄        ║--------╚═══════════┄┄┄┄┄
       ║    |╲                               ║╲
       ║    | ╲                              ║ ╲
       ║    |  ╲      EXTENDED               ║  ╲      TOOTHED
       ║    |   ╲                            ║   ╲
       ╚════╗    ╲                           ║    ╲
            ║     ╲                          ║     ╲
            ║      ╲                         ║      ╲
            ║       ╲                        ║       ╲
            ║        ╲                       ║        ╲
            ┆         ╲                      ┆         ╲
            ┆                                ┆
            ┆  EXTENDED                      ┆  FLAT
```

The last three edge styles usually are not needed when setting edge styles in
basic usage. But you will probably need them when designing custom edge
objects, especially custom edge cutouts.

The `INTERNAL_*` styles differ from their counterparts by their handling of
displacement.

Edge styles for edges can be set using the `set_corner_style` method for edges.
The `set_begin_style` and `set_end_style` methods are shortcuts to set corner
styles in the respective directions.

Note that corner styles are a property of a complete edge, therefore setting
them from edge references that refer to subparts of an edge is not supported.

### Edge elements' edge styles

In addition to specifying the geometries of corners, edge elements have edge
style properties, too. In this case they control how these elements and/or
their neighbours are rendered.

In particular, a `TOOTHED` element with a `TOOTHED` end style will end with an
extended part whereas one with a flat end style will end with a flat part.

Note: For other elements the `prev_style` and `next_style` parameters can be
used to control the rendering of automatically added filler elements. The
following example will create a flat element that is continued with a flat
portion of its neighbouring toothed elements, contrary to the default which
would add an extended tooth portion.

```python
wall.get_edge_by_direction(DIR2.UP).add_element(
        10, 20,
        EDGE_ELEMENT_STYLE.FLAT,
        prev_style = EDGE_STYLE.FLAT,
        next_style = EDGE_STYLE.FLAT,
    )
```

### Counterparts

In order for produced parts to be compatible their respective styles must
match, ie. where one edge has an extended element its counterpart must have a
flat one.

Also, local to a single wall, neighbouring edge elements' end styles also have
to begin/end at the same location.

This means that these styles have special requirements and may be set
incompatible. LaserGen helps here by keeping track of edges' counterparts and
changing their settings, too. The appropriate methods have a parameter to turn
this off, for better manual control. This parameter is usually called
`set_counterpart`.

Even when setting these properties by hand, LaserGen will check all styles for
compatibility, producing a warning if there is a mismatch.

Note: This only works when edge have their counterparts configured, which is
true for all LaserGen generated objects. If you create objects yourself, you
probably want to configure these counterparts yourself to profit from this
error checking.


Config
------

LaserGen uses a config objects to handle several parameters.

The most notable settings needed to do rendering and export are given to the
`Config` constructor and configure tooth lenghts, material thickness and export
spacing.


Displacement
------------

LaserGen is able to take into account the cutting width of production tools and
offset all cuts a corresponding distance outwards. In the code this is called
'displacement'. The value is taken to be half the `cutting_width` given in the
config.

Usually you shouldn't need to worry about this. However, this comes into play
when designing custom objects and doing advanced things with edge styles.


Rendering
---------

Rendering turns a wall object into a collection of primitives which can then be
exported.

Specifically, rendering an object returns an `Object2D` which can, if needed,
be edited further.

Calling `render` on a box object will return a list of `Object2D`s, the render
results of all walls it contains.


Layers
------

LaserGen has a rendering layer system, which allows later exporting only
specific layers. This can for example be used to add objects to the `info`
layer for visual reference.

Additionally an object's layer will influence its displacement parameter while
rendering. For example objects on the `info` layer will, by default, be
rendered without any displacement.


Export
------

The last step usually is exporting the generated objects. LaserGen currently
supports two types of export, an SVG export for laser cutting and OpenSCAD /
STL export for previewing.

### Placement

Before exporting multiple 2D objects they need to be positioned such that don't
overlap. Currently the only non-manual option LaserGen provides for placement
is the `place_2d_objects` function. It will stack all given objects on the Y
axis.

### SVG

For exporting to SVG LaserGen provides two options.

* `export_svg`
* `export_svg_with_paths`

Both functions take a list of `Object2D`s, as for example returned by a box's
`render` method, and return a string that can be written to a file.

The first one map LaserGen's primitives to SVG elements one-to-one.

The second will convert all primitives to SVG paths, concatenating elements
with matching endpoints, by default. Additionally this will produce a warning
if there are non-closed paths. This is probably a design error.

### OpenScad

For visual 3D reference LaserGen allows exporting objects via OpenSCAD.

The `export_box_openscad` function, given a box object, will write several
files to the given directory, including a makefile. This allows you to run
`make view` to open an OpenSCAD window containing the arranged objects. Though,
for better viewing experience, I recommend calling `make export.stl` to create
an STL file and view it with blender, because it has better transparency
rendering.

If you want to view only a single object you can set the `single_wall_rules`
or, more explicitly, use the `export_object_openscad` function.

Note: The given directory needs to exist.

Note: To actually convert the files you need the following tools:

* `inkscape`
* `pstoedit`
* `openscad`
* `make`
