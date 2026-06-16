import numpy as np
from enum import Enum


class SpringType(Enum):
    STRUCTURAL = 1
    SHEAR = 2
    BENDING = 3


# Mapeia cada tipo de mola para a componente de forca correspondente no
# vertice, para que a contribuicao de cada tipo possa ser analisada.
FORCE_BUCKET = {
    SpringType.STRUCTURAL: "estrutural",
    SpringType.SHEAR: "cisalhamento",
    SpringType.BENDING: "flexao",
}


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

        direction = delta / length  # aponta de v1 para v2

        deformation = length - self.rest_length

        # Forca elastica (lei de Hooke): positiva quando esticada, puxando os
        # vertices um na direcao do outro.
        elastic = (self.stiffness * deformation) * direction

        # Amortecimento: opoe-se a velocidade relativa ao longo da mola,
        # reduzindo oscilacoes excessivas.
        relative_velocity = self.v2.velocity - self.v1.velocity
        damping = (self.damping * np.dot(relative_velocity, direction)) * direction

        bucket = FORCE_BUCKET[self.type]

        # v1 e puxado em +direction (para v2); v2 em -direction (para v1).
        self.v1.forces[bucket] += elastic
        self.v2.forces[bucket] -= elastic
        self.v1.forces["amortecimento"] += damping
        self.v2.forces["amortecimento"] -= damping
