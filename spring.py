import numpy as np
from enum import Enum

class SpringType(Enum):
    STRUCTURAL = 1
    SHEAR = 2
    BENDING = 3


class Spring:
    def __init__(self, v1, v2, stiffness, damping, spring_type):
        self.v1 = v1
        self.v2 = v2

        self.stiffness = stiffness
        self.damping = damping

        self.type = spring_type

        self.rest_length = np.linalg.norm(
            v2.position - v1.position
        )

    def apply_force(self):
        delta = self.v2.position - self.v1.position

        length = np.linalg.norm(delta)

        if length == 0:
            return

        direction = delta / length

        deformation = length - self.rest_length

        elastic_force = (
            -self.stiffness
            * deformation
            * direction
        )

        self.v1.force += elastic_force
        self.v2.force -= elastic_force