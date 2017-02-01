import numpy as np

class DIR():
    UP    = np.array([ 0, 1, 0])
    DOWN  = np.array([ 0,-1, 0])
    LEFT  = np.array([-1, 0, 0])
    RIGHT = np.array([ 1, 0, 0])
    FRONT = np.array([ 0, 0, 1])
    BACK  = np.array([ 0, 0,-1])

def is_dir(d):
    dirs = {k:v for k,v in DIR.__dict__.items() if not k.startswith('_')}
    for i in dirs.values():
        if (d == i).all():
            return True
    return False

def dir_to_name(d):
    dirs = {k:v for k,v in DIR.__dict__.items() if not k.startswith('_')}
    for k,v in dirs:
        if (v == d).all():
            return k

def project_along_axis(vec, axis):
    assert(is_dir(axis))
    return np.array([v for v,a in zip(vec, axis) if a == 0])

def mirror_array_bool_to_factor(v):
    return np.array([(-1 if b else 1) for b in v])

def orthon(v):
    # rotate by 90 deg CCW
    return np.array([-v[1], v[0]]) / np.linalg.norm(v)

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
