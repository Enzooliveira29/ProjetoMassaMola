import numpy as np

class Vertex:
    def __init__(self, id, position, mass=1.0, fixed=False):
        self.id = id
        self.position = np.array(position, dtype=float)

        self.velocity = np.zeros(3)
        self.acceleration = np.zeros(3)

        self.force = np.zeros(3)

        self.mass = mass
        self.fixed = fixed