class Config():

    layers = {
            'cut'   : 'black',
            'error' : 'red',
            'info'  : 'green',
            'warn'  : 'orange',
        }

    abort_on_tooth_length_error = False
    print_wall_names = True

    def __init__(self, tooth_min_width, tooth_max_width, wall_thickness, object_distance, cutting_width=0):
        self.tooth_min_width = tooth_min_width
        self.tooth_max_width = tooth_max_width
        self.wall_thickness = wall_thickness
        self.subwall_thickness = wall_thickness # other values aren't supported yet
        self.cutting_width = cutting_width
        self.object_distance = object_distance
