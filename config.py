class Config():

    colors = {
            'cutout'  : 'black',
            'outline' : 'black',
            'error'   : 'red',
            'info'    : 'green',
            'warn'    : 'orange',
        }

    abort_on_tooth_length_error = False
    print_wall_names = True
    warn_for_unclosed_paths = True

    def __init__(self, tooth_min_width, tooth_max_width, wall_thickness, object_distance, cutting_width=0):
        self.tooth_min_width = tooth_min_width
        self.tooth_max_width = tooth_max_width
        self.wall_thickness = wall_thickness
        self.subwall_thickness = wall_thickness # other values aren't supported yet
        self.cutting_width = cutting_width
        self.object_distance = object_distance

    def copy(self):

        n = Config(
                self.tooth_min_width,
                self.tooth_max_width,
                self.wall_thickness,
                self.object_distance,
                self.cutting_width,
            )

        n.subwall_thickness           = self.subwall_thickness
        n.abort_on_tooth_length_error = self.abort_on_tooth_length_error
        n.print_wall_names            = self.print_wall_names
        n.warn_for_unclosed_paths     = self.warn_for_unclosed_paths

        n.colors = self.colors.copy()

        return n

    def get_color_from_layer(self, layer):

        if layer.warn_level is not None:
            return self.colors[layer.warn_level]

        else:
            return self.colors[layer.name]

    def get_displacement_from_layer(self, layer):

        if layer.name == 'outline':
            return self.cutting_width / 2

        elif layer.name == 'cutout':
            return -self.cutting_width / 2

        elif layer.name == 'info':
            return 0
