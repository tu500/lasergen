import numpy as np

class DIR():
    UP    = np.array([ 0, 1, 0])
    DOWN  = np.array([ 0,-1, 0])
    LEFT  = np.array([-1, 0, 0])
    RIGHT = np.array([ 1, 0, 0])
    FRONT = np.array([ 0, 0, 1])
    BACK  = np.array([ 0, 0,-1])

def orthon(v):
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
