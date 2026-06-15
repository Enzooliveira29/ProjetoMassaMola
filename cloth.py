import numpy as np

from vertex import Vertex
from spring import Spring, SpringType


class Cloth:
    def __init__(self):
        self.vertices = []
        self.springs = []

    def build_grid(self, rows, cols, spacing=1.0):

        for i in range(rows):
            for j in range(cols):

                position = [
                    j * spacing,
                    -i * spacing,
                    0
                ]

                fixed = (i == 0)

                vertex = Vertex(
                    len(self.vertices),
                    position,
                    fixed=fixed
                )

                self.vertices.append(vertex)
    def compute_forces(self):

        gravity = np.array([0, -9.81, 0])

        for vertex in self.vertices:

            vertex.force = np.zeros(3)

            if not vertex.fixed:
                vertex.force += gravity * vertex.mass

        for spring in self.springs:
            spring.apply_force()

    def integrate(self, dt):

        for vertex in self.vertices:

            if vertex.fixed:
                continue

            vertex.acceleration = (
                vertex.force / vertex.mass
            )

            vertex.velocity += (
                vertex.acceleration * dt
            )

            vertex.position += (
                vertex.velocity * dt
            )
            
    def update(self, dt):

        self.compute_forces()

        self.integrate(dt)

