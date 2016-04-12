import numpy as np

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
