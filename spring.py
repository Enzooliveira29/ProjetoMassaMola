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

    # ---- Jacobianas (metodo implicito de Euler / Kang e Cho) --------------
    def jacobians(self):
        """Blocos 3x3 das matrizes Jacobianas desta mola, usados pelo metodo
        implicito de Euler (Kang e Cho, 2004 -- Secao 4.2.2 da dissertacao).

        Sejam a = v1, b = v2 e d = x_a - x_b, com r = ||d||. Retorna:

          J = d f_a / d x_b   (Eq. 4.33/4.34) -- rigidez elastica
            = k * [ I3 - (L/r) * (I3 - d d^T / r^2) ]

          D = d f_a^d / d v_b  (parte de velocidade da Eq. 4.35) -- amortecimento
            = k^d * (d d^T / r^2)

        Por simetria, o bloco diagonal de a (e de b) recebe -J (-D) e o bloco
        cruzado a<->b recebe +J (+D); por isso Cloth monta o sistema a partir
        destes dois blocos. d/dx do amortecimento (termo cruzado da Eq. 4.35)
        e omitido por ser pequeno e potencialmente desestabilizador -- pratica
        padrao em implementacoes do metodo.
        """
        d = self.v1.position - self.v2.position
        r2 = float(np.dot(d, d))
        I3 = np.eye(3)
        if r2 == 0.0:
            return np.zeros((3, 3)), np.zeros((3, 3))

        r = np.sqrt(r2)
        outer = np.outer(d, d) / r2
        J = self.stiffness * (I3 - (self.rest_length / r) * (I3 - outer))
        D = self.damping * outer
        return J, D
