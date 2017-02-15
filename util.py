import numpy as np

class DIR():
    UP    = np.array([ 0, 1, 0])
    DOWN  = np.array([ 0,-1, 0])
    LEFT  = np.array([-1, 0, 0])
    RIGHT = np.array([ 1, 0, 0])
    FRONT = np.array([ 0, 0, 1])
    BACK  = np.array([ 0, 0,-1])

    AXES = [RIGHT, UP, FRONT]
    DIRS = [RIGHT, LEFT, UP, DOWN, FRONT, BACK]

    def is_dir(d):
        for i in DIR.DIRS:
            if (d == i).all():
                return True
        return False

    def dir_to_name(d):
        dirs = {k:v for k,v in DIR.__dict__.items() if k in ['UP', 'DOWN', 'LEFT', 'RIGHT', 'FRONT', 'BACK']}
        for k,v in dirs.items():
            if (v == d).all():
                return k

    def dir_to_axis_name(d):
        if not isinstance(d, str):
            d = DIR.dir_to_name(d)
        return {
                'UP'    : 'Y',
                'DOWN'  : 'Y',
                'LEFT'  : 'X',
                'RIGHT' : 'X',
                'FRONT' : 'Z',
                'BACK'  : 'Z',
            }[d]

    def perpendicular_dirs(d):
        assert(DIR.is_dir(d))
        index = None
        for i,a in enumerate(DIR.AXES):
            if (a==abs(d)).all():
                index = i
                break
        assert(index is not None)
        j,k = [DIR.AXES[i] for i in range(3) if i != index]
        return [j,-j,k,-k]

    def perpendicular_axes(d):
        assert(DIR.is_dir(d))
        index = None
        for i,a in enumerate(DIR.AXES):
            if (a==abs(d)).all():
                index = i
                break
        assert(index is not None)
        return [DIR.AXES[i] for i in range(3) if i != index]

class DIR2():
    UP    = np.array([ 0, 1])
    DOWN  = np.array([ 0,-1])
    LEFT  = np.array([-1, 0])
    RIGHT = np.array([ 1, 0])

    def orthon(v):
        # rotate by 90 deg CCW
        return np.array([-v[1], v[0]]) / np.linalg.norm(v)

def project_along_axis(vec, axis):
    assert(DIR.is_dir(axis))
    return np.array([v for v,a in zip(vec, axis) if a == 0])

def mirror_array_bool_to_factor(v):
    return np.array([(-1 if b else 1) for b in v])

def min_vec(*args):
    return np.array([
        min(v[0] for v in args),
        min(v[1] for v in args)
        ])

def max_vec(*args):
    return np.array([
        max(v[0] for v in args),
        max(v[1] for v in args)
        ])

def almost_equal(a, b, epsilon=1E-10):
    return np.linalg.norm(a-b) < epsilon
